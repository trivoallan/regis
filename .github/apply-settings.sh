#!/usr/bin/env bash
# Applique .github/settings.json au dépôt courant. Fichier du socle : identique dans regis, knock et uske.
set -euo pipefail

cfg="$(dirname "$0")/settings.json"

# Vrai si chaque valeur scalaire de $1 se retrouve au même chemin dans $2.
# Les clés en plus dans $2, que l'API ajoute toujours, sont ignorées ; les listes doivent avoir la même longueur.
covers() {
  jq -en --argjson w "$1" --argjson h "$2" \
    '([$w | paths(scalars | true)] | all(. as $p | ($w | getpath($p)) == ($h | getpath($p))))
     and ([$w | paths(type == "array")] | all(. as $p | ($w | getpath($p) | length) == ($h | getpath($p) | length)))' >/dev/null
}

# Les règles forment une liste : on les indexe par type, pour comparer sans dépendre de l'ordre.
# On y ajoute l'ensemble des types de règle (sinon un type en trop passerait inaperçu) et on trie les listes sans ordre.
norm='.rule_types = (.rules | map(.type) | sort)
  | .bypass_actors |= ((. // []) | sort_by([.actor_type, .actor_id]))
  | .rules |= (map(if .type == "required_status_checks" then .parameters.required_status_checks |= sort_by(.context) else . end)
               | map({(.type): (.parameters // true)}) | add)'

# 0 si la ressource existe, 1 si GitHub répond 404, abandon pour toute autre erreur.
exists() {
  local err
  err="$(gh api "$1" 2>&1 >/dev/null)" && return 0
  case "$err" in *"(HTTP 404)"*) return 1 ;; esac
  echo "erreur sur $1 : $err" >&2; exit 1
}

if [ "${1:-}" = --self-test ]; then
  ! covers '{"s":[1]}' '{"s":[1,2]}'                            || { echo "échec : un élément de liste en plus doit être vu"; exit 1; }
  ! covers '{"e":[]}' '{"e":["x"]}'                             || { echo "échec : une liste vide remplie doit être vue"; exit 1; }
  a='{"bypass_actors":[{"actor_id":5,"actor_type":"RepositoryRole"},{"actor_id":1,"actor_type":"Team"}],"rules":[{"type":"deletion"},{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"},{"context":"test"}]}}]}'
  b='{"id":7,"bypass_actors":[{"actor_id":1,"actor_type":"Team"},{"actor_id":5,"actor_type":"RepositoryRole"}],"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"test","integration_id":1},{"context":"lint","integration_id":1}]}},{"type":"deletion"}]}'
  c="$(jq -c '.rules += [{"type":"creation"}]' <<<"$b")"
  covers "$(jq -c "$norm" <<<"$a")" "$(jq -c "$norm" <<<"$b")"  || { echo "échec : l'ordre des règles et des contrôles doit être ignoré"; exit 1; }
  ! covers "$(jq -c "$norm" <<<"$a")" "$(jq -c "$norm" <<<"$c")" || { echo "échec : un type de règle en plus doit être vu"; exit 1; }
  covers '{"a":1}' '{"a":1,"b":2}'                              || { echo "échec : une clé en plus doit être ignorée"; exit 1; }
  ! covers '{"a":1}' '{"a":2}'                                  || { echo "échec : une valeur différente doit être vue"; exit 1; }
  ! covers '{"r":{"deletion":true}}' '{"r":{}}'                 || { echo "échec : une règle absente doit être vue"; exit 1; }
  covers '{"s":[{"c":"lint"}]}' '{"s":[{"c":"lint","i":15368}]}' || { echo "échec : un champ en plus dans une liste doit être ignoré"; exit 1; }
  ! covers '{"a":false}' '{"a":true}'                           || { echo "échec : un false attendu doit être vu"; exit 1; }
  jq -e '.repository and .ruleset.name' "$cfg" >/dev/null       || { echo "échec : settings.json incomplet"; exit 1; }
  echo "self-test ok"
  exit 0
fi

repo="${GITHUB_REPOSITORY:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
changes=0
report() { if [ "$2" = same ]; then echo "= $1"; else echo "~ $1"; changes=$((changes + 1)); fi; }

# 1. Le dépôt : fusion, fonctions, secret scanning, Dependabot security updates.
info="$(gh api "repos/$repo")"
jq -e .security_and_analysis <<<"$info" >/dev/null || { echo "permission Administration manquante : security_and_analysis absent de la réponse" >&2; exit 1; }
want="$(jq -c .repository "$cfg")"
if covers "$want" "$info"; then report repository same
else gh api -X PATCH "repos/$repo" --input - <<<"$want" >/dev/null; report repository changed; fi

# 2. Les topics : l'ordre ne compte pas.
want="$(jq -c '{names: .topics}' "$cfg")"
if [ "$(jq -c '.names | sort' <<<"$want")" = "$(gh api "repos/$repo/topics" --jq '.names | sort')" ]; then report topics same
else gh api -X PUT "repos/$repo/topics" --input - <<<"$want" >/dev/null; report topics changed; fi

# 3. Les alertes Dependabot : GET répond 204 si elles sont activées, 404 sinon.
want="$(jq -r .vulnerability_alerts "$cfg")"
have=false; exists "repos/$repo/vulnerability-alerts" && have=true
if [ "$want" = "$have" ]; then report vulnerability_alerts same
else gh api -X "$([ "$want" = true ] && echo PUT || echo DELETE)" "repos/$repo/vulnerability-alerts" --silent; report vulnerability_alerts changed; fi

# 4. Private Vulnerability Reporting.
want="$(jq -r .private_vulnerability_reporting "$cfg")"
have="$(gh api "repos/$repo/private-vulnerability-reporting" --jq .enabled)"
if [ "$want" = "$have" ]; then report private_vulnerability_reporting same
else gh api -X "$([ "$want" = true ] && echo PUT || echo DELETE)" "repos/$repo/private-vulnerability-reporting" --silent; report private_vulnerability_reporting changed; fi

# 5. CodeQL en default setup. On le règle avant le ruleset, qui l'exige.
want="$(jq -r .code_scanning_default_setup "$cfg")"
if [ "$want" = "$(gh api "repos/$repo/code-scanning/default-setup" --jq .state)" ]; then report code_scanning_default_setup same
else gh api -X PATCH "repos/$repo/code-scanning/default-setup" -f state="$want" --silent; report code_scanning_default_setup changed; fi

# 6. Les rulesets : settings.json en décrit un seul, tous les autres rulesets du dépôt (faits à la main) sont supprimés.
# On crée ou met à jour celui de settings.json D'ABORD : main n'est jamais sans protection.
want="$(jq -c .ruleset "$cfg")"
name="$(jq -r .name <<<"$want")"
list="$(gh api --paginate "repos/$repo/rulesets?includes_parents=false")"
id="$(jq -r --arg n "$name" 'first(.[] | select(.name == $n) | .id) // empty' <<<"$list")"
if [ -n "$id" ] && covers "$(jq -c "$norm" <<<"$want")" "$(gh api "repos/$repo/rulesets/$id" | jq -c "$norm")"; then report ruleset same
elif [ -n "$id" ]; then gh api -X PUT "repos/$repo/rulesets/$id" --input - <<<"$want" >/dev/null; report ruleset changed
else gh api -X POST "repos/$repo/rulesets" --input - <<<"$want" >/dev/null; report ruleset changed; fi
for other in $(jq -r --arg n "$name" '.[] | select(.name != $n) | .id' <<<"$list"); do
  gh api -X DELETE "repos/$repo/rulesets/$other" --silent; report "ruleset $other (hors settings.json)" changed
done

# 7. La protection de branche classique est remplacée par le ruleset : on la retire, une fois le ruleset en place.
if exists "repos/$repo/branches/main/protection"; then
  gh api -X DELETE "repos/$repo/branches/main/protection" --silent; report classic_protection changed
else report classic_protection same; fi

echo "$changes modification(s)"
if [ "$changes" -gt 0 ] && [ "${GITHUB_EVENT_NAME:-}" = schedule ]; then echo "::warning::$changes réglage(s) rétabli(s)"; fi
