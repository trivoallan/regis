---
adr: SDR-0010
slug: forge-and-ci
title: Forge and continuous integration
status: accepted
revision: 2
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
traits:
  forge:
    vendor: github
    gate: bloquante
---

# Forge and continuous integration

> **Qu'est-ce que ce fichier ?** Un ADR — *Architecture Decision Record* — est une décision consignée : son contexte, les options pesées, ce qui a été retenu, et ce que ça coûte. **Tant qu'il porte `status: proposed`, il s'écrit et se corrige librement.**
>
> **La ligne `revision:` de l'en-tête date la question, pas le fichier.** Elle n'avance que si la question posée ici change — jamais pour une reformulation, une coquille ou un lien réparé. Vous ne la remplissez pas : elle arrive avec le fichier, et votre verdict lui reste attaché. Elle existe pour qu'on reconnaisse, plus tard, un verdict rendu contre une question qui a depuis bougé.
>
> **`rejected` est une réponse pleine, pas un abandon.** Quand la question ne se pose pas dans ce dépôt, l'ADR reçoit le verdict `rejected` avec son motif, et le bloc `traits:` disparaît en entier — une clé sans objet ne se laisse pas vide. Le motif dit alors **ce qui en tient lieu**, pour qu'un agent qui le lit sache à quoi s'en tenir. **Un ADR `rejected` sans bloc `traits:` passe la vérification** — c'est mesuré, pas supposé.

## Context and Problem Statement

**Concrètement, ce que statuer change.** Tant que ces clés sont vides, un agent qui ouvre une merge request ne sait pas **où elle part**, ce qui **s'exécute** quand il pousse, ni si une chaîne rouge **empêche** la fusion ou se contente de l'annoncer. Il perd du temps à réparer un rouge qui n'avait aucune conséquence — ou il fusionne un rouge qui en avait une. Une fois ces deux valeurs écrites, il sait.

**La forge n'est pas qu'un hébergeur, et c'est pourquoi les règles de la chaîne vivent ici.** Elle décide le vocabulaire — merge request ou pull request —, l'outil qui exécute la chaîne, la **syntaxe du fichier** qui la décrit, et l'endroit où vivent les protections de branche. Répondre `github` répond déjà à tout cela : c'est pourquoi l'outil ne fait plus l'objet d'une clé.

**Où vivent ces protections, puisque la forge le décide.** Sur GitLab, dans les paramètres du projet, sous les branches protégées. Sur GitHub, dans les *rulesets* du dépôt ou de l'organisation. La différence n'est pas cosmétique : c'est là, et non dans un fichier de votre dépôt, que `forge.gate: bloquante` devient effectif. Une chaîne rouge n'empêche rien tant qu'un contrôle requis ne la nomme pas.

**Ce qui n'est pas ici.** La stratégie de branche et de fusion est dans [`SDR-0009`](SDR-0009-branching.md) — elle ne dépend pas de la forge. Ce qui part en production est dans [`SDR-0011`](SDR-0011-delivery.md).

## Considered Options

* **Une chaîne bloquante** — rien ne fusionne au rouge. Le coût est réel : une chaîne instable bloque des gens qui n'y sont pour rien, et la pression pour la contourner monte.
* **Une chaîne informative** — elle rapporte, la relecture décide. Moins de friction, et aucune garantie : un rouge signalé se néglige.
* **Aucune chaîne** — la relecture est le seul contrôle. Réponse tenable pour un dépôt sans code exécutable.

## Decision Outcome

**La réponse que la méthode propose, et ses motifs.**

| Clé | Valeur proposée | Motif |
| --- | --- | --- |
| `forge.vendor` | `gitlab` | c'est la forge que la méthode a d'abord outillée, et son vocabulaire en vient — elle écrit « merge request » là où GitHub dit « pull request ». **`github` est un choix admis, pas une déviation** — voir juste en dessous |
| `forge.gate` | `bloquante` | un contrôle qui n'empêche rien n'est pas un contrôle, c'est un rapport. Des deux clés, c'est la seule qui soit une vraie décision |

**L'outil de chaîne ne se déclare plus.** Une clé le portait — `gitlab-ci` sur GitLab, `github-actions` sur GitHub —, et elle ne décidait rien : elle se **dérive** de la forge. Une clé qu'un agent peut calculer est une clé qu'on lui fait remplir pour rien.

**Sur `forge.vendor`, la réponse a une forme que les autres ADR hérités n'ont pas.** Ailleurs, la méthode propose une valeur, ou borne le champ sans choisir. Ici elle fait les deux : elle **propose `gitlab` tout en admettant `github` à égalité**, sans justification à fournir. Les deux sont des réponses pleines, et **l'ensemble est fermé à ces deux-là**.

**Une troisième forge — Gitea, Bitbucket, Forgejo — se dit par `rejected`**, et non en écrivant sa valeur ici. Le motif du verdict nomme alors la forge réelle, pour qu'un agent qui le lit sache à quoi s'en tenir. La raison est que le reste de la méthode n'a pas été éprouvé contre elles.

**Ce verdict coûte plus qu'il n'y paraît, et il faut le savoir avant de le prendre.** `rejected` retire le bloc `traits:` **en entier** : vous perdez donc aussi `forge.gate` — ce qu'une chaîne rouge empêche — et, avec lui, **les règles de toute chaîne prescrites plus bas** : le job de déploiement borné à la branche par défaut, les variables protégées et masquées, les images épinglées, l'interdiction de journaliser une valeur de variable, et le refus d'un secret à une contribution non fiable. Aucune ne s'applique plus. Un dépôt sur une troisième forge qui veut les garder les recopie dans son ADR local, avec son motif. C'est le prix d'un ensemble fermé, et il est réel.

**Les règles de toute chaîne qu'un agent écrit pour ce dépôt.** Elles valent quelle que soit l'offre d'hébergement retenue dans [`SDR-0011`](SDR-0011-delivery.md) ; une règle sans objet pour la vôtre, comme une image sous `paas`, se dit sous Consequences. Elles survivent à la coupe.

**Cinq règles du pipeline.**

1. Le job de déploiement ne tourne que sur la branche par défaut. Une branche de fonctionnalité poussée ne déploie rien.
2. Les variables de déploiement sont protégées et masquées.
3. Les images et les `include` sont épinglés de façon immuable, jamais par une branche ni par `latest`. **La forme immuable dépend de la forge**, et c'est le genre de détail qui se paie. Sur GitLab, c'est le digest d'une image, ou un tag que personne ne déplace. Sur GitHub, **le tag d'une action est mutable par construction** : `actions/checkout@v4` est un tag que son auteur avance à chaque version, et l'épingler ne fige rien. La seule forme immuable y est le **SHA de commit** — `actions/checkout@<sha>`. Un tag qui suffirait ailleurs ne suffit pas ici.

   **`actionlint` ne tient pas cette règle, et il vaut mieux le savoir avant de lui faire confiance.** Sur une chaîne propre qui épingle `actions/checkout@v5` — un tag mutable, exactement ce que cette règle refuse —, il rend **zéro signalement et un code de sortie de 0** : mesuré le 2026-09-20, `actionlint` v1.7.12, macOS 15.0 arm64, sur un dépôt jetable. Ses règles portent sur la syntaxe, sur les expressions et sur quelques formes dangereuses nommées — les paragraphes des règles 4 et 5 ci-dessous en montrent deux à l'œuvre —, et l'épinglage d'une action n'en fait pas partie. **`glci lint` non plus, et c'est mesuré de la même façon.** Sur un `.gitlab-ci.yml` dont deux jobs portent des images délibérément mutables — `node:latest` et `alpine:3` —, il rend `CI configuration is valid: 2 jobs, 5 stages` et un code de sortie de 0 : mesuré le 2026-09-20, `glci` v0.8.0, macOS 15.0 arm64, sur un dépôt jetable. Lui non plus ne pose aucune question sur la façon dont une image est épinglée : il valide la forme de la configuration, et son catalogue s'arrête là. Aucun instrument ne tient donc cette règle, ni sur l'une ni sur l'autre forge — et les deux sont mesurées, aucune n'est déduite de l'autre : c'est la relecture qui lit les `uses:` et les `image:`, un par un.

4. **Aucun job n'écrit dans un journal la valeur d'une variable.** La règle vise le fait, pas une liste de commandes : une interdiction qui nommerait `echo`, `env` et `set -x` se contournerait par `printf`, et elle **contredirait la sortie exigée plus bas**, qui impose d'afficher l'URL de staging et le commit — deux variables. Afficher une valeur que la chaîne publie de toute façon n'est pas la fuiter ; écrire un secret dans un journal, si.

   **`actionlint` ne signale pas davantage un job qui journalise un secret.** Mesuré le 2026-09-20, dans les mêmes conditions : un `run:` qui écrit `echo "jeton ${{ secrets.KUBE_TOKEN }}"` ne rend **aucun signalement** ; pas plus que la commande `env` nue, celle qui déverse l'environnement entier ; pas plus qu'un `curl -u admin:motdepasse`, un identifiant écrit en clair dans un script. Ce qu'il attrape est ailleurs, et c'est un endroit du fichier de chaîne, pas du journal : la clé `password:` d'une `credentials:` — celle d'un `container:` comme celle d'un `services:` —, qu'il nomme sous sa règle `credentials`. Un job qui tient cette borne-là peut fuiter par les trois chemins ci-dessus sans que rien ne le dise.

5. **Une contribution non fiable ne reçoit aucun secret**, et un travail qui s'exécute avec les droits du dépôt cible n'exécute pas le code proposé. La règle vise le fait, comme la précédente : les noms d'événements changent d'une forge à l'autre, et d'une version à l'autre. Sur GitHub, c'est `pull_request_target`, qui s'exécute avec les secrets du dépôt cible sur du code venu d'un fork ; sur GitLab, ce sont les pipelines de merge request déclenchés depuis un fork.

   **Ce qui s'arrête est le secret, pas le test.** Une chaîne qui ne demande aucun secret s'exécute normalement sur une contribution de fork, et elle le doit : couper l'intégration continue des contributions extérieures n'est pas appliquer cette règle, c'est fermer la porte que l'ouverture du dépôt vient d'ouvrir.

   **Cette règle n'a été mesurée sur aucun dépôt, à la différence des constats datés de ce fichier.** Elle vaut comme règle de place publique connue, pas comme mesure. Et **aucun instrument ne la tient** — ni ici, ni chez vous : la relecture de la demande de fusion est le seul recours.

   **`actionlint` en signale une manifestation, et la phrase qui précède ne bouge pas pour autant.** Mesuré le 2026-09-20, `actionlint` v1.7.12, macOS 15.0 arm64, sur un dépôt jetable : sur un `run:` qui interpole directement le titre d'une demande de fusion, il rend, code de sortie 1, `"github.event.pull_request.title" is potentially untrusted. avoid using it directly in inline scripts. instead, pass it through an environment variable` — sa règle `expression`, avec la colonne pointée par un caret. C'est l'injection de script par une entrée non fiable : la forme la plus visible de cette règle, et la seule qu'il voie.

   **Il rate le cœur de la règle, et c'est là qu'un vert tromperait.** Mesuré dans les mêmes conditions, il ne dit **rien** de `pull_request_target` lui-même, ni d'un `actions/checkout` qui coche le `head.sha` d'un fork sous cet événement — la forme dangereuse par excellence, celle qui exécute du code proposé avec les secrets du dépôt cible. Un dépôt qui le verrait au vert pourrait en conclure qu'il respecte cette règle ; il n'en saurait rien.

   **Signaler n'est pas tenir**, et la différence est tout ce qui compte ici : vous lancez cet outil à la main, sur votre poste, et il ne refuse aucune fusion. Une règle dont un instrument nomme une manifestation reste une règle sans instrument.

**Les secrets.** L'agent produit la liste des **noms** des variables que la chaîne attend, jamais leurs valeurs. **Le lieu dépend de votre forge.** Sur GitLab, ce sont les variables CI/CD du projet. Sur GitHub, ce sont les secrets du dépôt, ou ceux d'un environnement quand la règle 1 le demande — un environnement protégé étant aussi ce qui borne le déploiement à la branche par défaut. Dans les deux cas, protégées et masquées, et vous les y posez vous-même. **Ceux-là sont les secrets de la forge, et ils n'y arrivent que parce que vous les y posez.** Un exécuteur local, lui, se sert tout seul, et pas au même endroit selon la forge : `act` lit des fichiers de votre dépôt que personne n'y a posés pour lui, tandis que `glci` va chercher **à distance** les variables réelles de votre projet. Deux pièges distincts, qui se neutralisent différemment — plus bas, avec la mise au point locale.

**La mise au point locale.** Elle se joue **avant la poussée**, et c'est tout son intérêt : une chaîne éprouvée en local ne dépense pas une tentative sur la forge pour une erreur de syntaxe, un job manquant ou un script qui ne démarre pas. Elle ne fait l'objet d'aucun trait : l'outil est une propriété du poste, pas du dépôt. Sur GitLab, l'agent installe `glci` en version `v0.8.0`, depuis le projet GitLab `gitlab-org/ci-cd/runner-tools/glci`, sans droits d'administration :

```bash
(
  os=$(uname -s | tr '[:upper:]' '[:lower:]')
  case "$(uname -m)" in
    x86_64|amd64) arch=amd64 ;;
    arm64|aarch64) arch=arm64 ;;
    *) echo "architecture non prise en charge : mise au point locale sautée" >&2; exit 1 ;;
  esac
  case "$os-$arch" in
    darwin-arm64) attendu=73e1a1a1b566059ab11f53aaad46c62260842c2b258839be6256752ee9ab5c75 ;;
    darwin-amd64) attendu=cec302176f31c46bc49c7288f872f48cf7271d6c70df1273901e5403c5b2270d ;;
    linux-arm64)  attendu=fddd8668159e9dbec46145a27c854d15740009373bcba115ba096e881510d88e ;;
    linux-amd64)  attendu=0758d9774ebfe46b5231e77e60b8457346da0ae41e1ffc585e567e4441712ca4 ;;
    *) echo "plateforme non prise en charge : mise au point locale sautée" >&2; exit 1 ;;
  esac
  tmp=$(mktemp)
  curl -fsSL -o "$tmp" \
    "https://gitlab.com/api/v4/projects/gitlab-org%2Fci-cd%2Frunner-tools%2Fglci/packages/generic/glci/v0.8.0/glci-$os-$arch" \
    || { rm -f "$tmp"; echo "téléchargement impossible : mise au point locale sautée" >&2; exit 1; }
  if command -v sha256sum >/dev/null 2>&1; then
    obtenu=$(sha256sum "$tmp" | cut -d' ' -f1)
  else
    obtenu=$(shasum -a 256 "$tmp" | cut -d' ' -f1)
  fi
  [ "$obtenu" = "$attendu" ] \
    || { rm -f "$tmp"; echo "empreinte différente : mise au point locale sautée" >&2; exit 1; }
  mkdir -p "$HOME/.local/bin" && install -m 0755 "$tmp" "$HOME/.local/bin/glci" && rm -f "$tmp"
)
```

Le bloc tourne dans un sous-shell : `exit` l'arrête sans fermer votre terminal. L'adresse est celle que le script d'installation du projet, lu au tag `v0.8.0`, construit lui-même. **Ce script ne se lance pas** : il exécute le binaire (`glci doctor`) juste après l'avoir posé, avant qu'une empreinte ait pu être vérifiée, et il se replie sur `sudo` quand le répertoire cible n'est pas inscriptible.

Les empreintes SHA-256 attendues, relevées le 2026-09-18 :

```text
73e1a1a1b566059ab11f53aaad46c62260842c2b258839be6256752ee9ab5c75  glci-darwin-arm64
cec302176f31c46bc49c7288f872f48cf7271d6c70df1273901e5403c5b2270d  glci-darwin-amd64
fddd8668159e9dbec46145a27c854d15740009373bcba115ba096e881510d88e  glci-linux-arm64
0758d9774ebfe46b5231e77e60b8457346da0ae41e1ffc585e567e4441712ca4  glci-linux-amd64
```

* **Une empreinte qui diffère arrête l'installation**, avant toute exécution du binaire. L'agent supprime le fichier téléchargé, saute la mise au point locale, et le dit.
* L'installation se fait dans `$HOME/.local/bin`, jamais avec `sudo`. L'agent vérifie que ce répertoire est dans le `PATH`, et le dit s'il n'y est pas.
* La mise au point se lance par `glci run --no-token --secrets none`, et **les deux options ne protègent pas de la même chose** — les confondre laisse un trou entier. **`--no-token` retient le jeton de votre poste** : sans elle, `glci` transmet votre `GITLAB_TOKEN` au pipeline comme `CI_JOB_TOKEN`, et un pipeline pas encore relu recevrait votre jeton personnel. **`--secrets none` retient les variables de votre projet** : son défaut est `all`, et `glci` va alors chercher sur la forge les variables CI/CD réelles du projet, de son groupe et de l'instance, pour les faire descendre dans ce même pipeline. Garder l'une en lâchant l'autre ne protège que la moitié. Si un job a besoin d'un secret en local, levez la restriction pour ce seul job, et dites-le dans la merge request.
* **Passez-lui le contexte, sinon il vous ment par omission.** Les commandes sont `glci show --context branch=<votre branche par défaut>` et `glci run --context branch=<votre branche par défaut> --no-token --secrets none`. **Sans `--context`, `glci` simule une demande de fusion** — c'est son défaut —, et GitLab n'y définit légitimement pas `CI_COMMIT_BRANCH`. Toute règle qui mentionne cette variable est donc fausse, **y compris `== "main"` écrit en littéral**, et le job disparaît de la pipeline locale : ni message, ni job marqué ignoré, il n'est simplement pas là. **L'absence n'est pas un avertissement.** `glci` a raison ; c'est le contexte qui était faux.
* **Une version antérieure de ce fichier affirmait le contraire, et se trompait deux fois.** Elle écrivait que le job de déploiement n'entre pas dans la pipeline parce que la règle 1 le gate sur la branche par défaut, et que « c'est structurel, pas un défaut de réglage ». **Ce constat ne tient plus.** Rejoué le 2026-09-20 sur un dépôt jetable, macOS 15.0 arm64, `glci` au commit `50516e8` : `glci show` rend `2 jobs across 1 stages` au défaut et **`3 jobs across 2 stages`** avec `--context branch=main`. Isolé job par job, `CI_DEFAULT_BRANCH` **est** définie et `CI_COMMIT_BRANCH` ne l'est **pas** : la cause n'était pas le portail, et rien n'était structurel.
* **Ce que la mise au point locale ne couvre pas, et c'est plus étroit qu'on ne l'a cru.** Le job de déploiement s'exécute — mesuré le 2026-09-20, `✓ Pipeline PASSED` en 29 secondes à la première tentative, `CI_ENVIRONMENT_URL` résolue —, mais il s'exécute **contre rien** : pas de cluster, pas de registre, aucun identifiant réel. `glci` éprouve la **forme** d'un job — son image, son script, ses variables, sa place dans les stages — et **jamais son effet**. Un déploiement ne se constate que sur une cible.
* **Une version antérieure rapportait un échec de `glci run`, et ce constat ne tient plus non plus.** Elle relevait `fatal: unable to access 'http://glci-mock:39741/…'`, le conteneur n'atteignant pas le serveur git embarqué — trois tentatives, 2 min 20 chacune, `glci doctor` vert partout. Rejoué le 2026-09-20 au commit `50516e8`, l'échec **ne s'est pas reproduit** : une tentative, 29 secondes, pipeline verte. Il reste possible qu'il dépende du poste ou de la version ; ce qui est mesuré est qu'il n'est pas systématique.
* **Un deux-points suivi d'une espace, dans un scalaire YAML non quoté, n'est pas un défaut de `glci`.** Il rend alors `script config should be a string or a nested array of strings`, et c'est votre YAML qui fait une map là où vous vouliez une chaîne. Quotez la ligne. Le signaler ici évite d'accuser l'outil.
* La skill d'agent de `glci` se pose par `glci skill install`, jamais par la clé `skills` de votre `package.json`. Elle se pose dans la configuration de votre agent, hors du dépôt : `glci skill install --agent <agent> --scope global`, par exemple avec `--agent claude-code`. Sans `--scope global`, la commande pose la skill dans le dépôt, sous `.claude/skills/glci/` pour `claude-code`, et elle partirait avec votre prochain commit.

**Sur GitHub, deux outils, et ils s'installent ensemble.** `actionlint` en version `v1.7.12` relit la syntaxe des workflows ; `act` en version `v0.2.89` les exécute sur votre poste. Ce sont deux binaires autonomes, pris dans les *releases* de leur projet — `rhysd/actionlint` et `nektos/act` —, vérifiés par le fichier d'empreintes que chaque projet publie à côté de ses archives, et installés dans `$HOME/.local/bin`, jamais avec `sudo`.

**Les deux projets ne nomment pas leurs archives de la même façon, et c'est le genre de détail qui se paie.** `actionlint` écrit `actionlint_1.7.12_darwin_arm64.tar.gz` : système et architecture en minuscules, `amd64` pour l'Intel. `act` écrit `act_Darwin_arm64.tar.gz` : majuscule initiale au système, et `x86_64` là où l'autre dit `amd64`. Un bloc d'installation qui suppose une convention commune échoue sur l'un des deux. Celui-ci porte donc deux jeux de noms.

```bash
(
  os=$(uname -s | tr '[:upper:]' '[:lower:]')
  case "$(uname -m)" in
    x86_64|amd64) arch=amd64; arch_act=x86_64 ;;
    arm64|aarch64) arch=arm64; arch_act=arm64 ;;
    *) echo "architecture non prise en charge : mise au point locale sautée" >&2; exit 1 ;;
  esac
  case "$os" in
    darwin) os_act=Darwin ;;
    linux)  os_act=Linux ;;
    *) echo "plateforme non prise en charge : mise au point locale sautée" >&2; exit 1 ;;
  esac
  tmp=$(mktemp -d)
  verifie() (
    cd "$tmp" || return 1
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum -c --status attendu.txt
    else
      shasum -a 256 -c --status attendu.txt
    fi
  )
  poser() {
    base=$1; archive=$2; empreintes=$3; binaire=$4
    curl -fsSL -o "$tmp/$archive" "$base$archive" \
      || { echo "téléchargement impossible ($archive) : mise au point locale sautée" >&2; return 1; }
    curl -fsSL -o "$tmp/$empreintes" "$base$empreintes" \
      || { echo "empreintes introuvables ($empreintes) : mise au point locale sautée" >&2; return 1; }
    grep " $archive\$" "$tmp/$empreintes" > "$tmp/attendu.txt" \
      || { echo "aucune empreinte pour $archive : mise au point locale sautée" >&2; return 1; }
    verifie \
      || { echo "empreinte différente ($archive) : mise au point locale sautée" >&2; return 1; }
    tar -xzf "$tmp/$archive" -C "$tmp" "$binaire" \
      || { echo "archive illisible ($archive) : mise au point locale sautée" >&2; return 1; }
    mkdir -p "$HOME/.local/bin" && install -m 0755 "$tmp/$binaire" "$HOME/.local/bin/$binaire"
  }
  poser "https://github.com/rhysd/actionlint/releases/download/v1.7.12/" \
    "actionlint_1.7.12_${os}_${arch}.tar.gz" "actionlint_1.7.12_checksums.txt" actionlint \
    || { rm -rf "$tmp"; exit 1; }
  poser "https://github.com/nektos/act/releases/download/v0.2.89/" \
    "act_${os_act}_${arch_act}.tar.gz" "checksums.txt" act \
    || { rm -rf "$tmp"; exit 1; }
  rm -rf "$tmp"
)
```

Comme celui de `glci`, ce bloc tourne dans un sous-shell : `exit` l'arrête sans fermer votre terminal, il vérifie avant d'exécuter quoi que ce soit, et il ne pose **jamais un binaire** dont l'empreinte ne correspond pas. Le répertoire d'installation est le même, et la même réserve vaut : l'agent vérifie que `$HOME/.local/bin` est dans le `PATH`, et le dit s'il n'y est pas.

**Mais il en pose deux, l'un après l'autre, et l'échec du second n'annule pas le premier.** `actionlint` est posé avant qu'`act` soit téléchargé : si l'empreinte d'`act` ne correspond pas, le bloc s'arrête en le disant — et `actionlint` reste installé, vérifié, utilisable. Ce n'est pas le régime du bloc de `glci`, qui ne pose qu'un outil et ne laisse donc rien derrière lui. **Un message d'échec ne veut pas dire que vous n'avez rien** : lisez lequel des deux il nomme, et regardez ce que `$HOME/.local/bin` porte avant de tout relancer.

**Ce que cette vérification couvre, et ce qu'elle ne couvre pas.** Le fichier d'empreintes voyage avec le binaire : il est publié par le même projet, au même endroit, dans la même *release*. Il attrape donc une **corruption de transport** — un téléchargement tronqué, un miroir qui sert autre chose — et **pas** une compromission de la publication : qui peut remplacer l'archive peut remplacer le fichier qui l'atteste. C'est la différence avec les empreintes de `glci` ci-dessus, qui sont **relevées à la main** à une date écrite, faute que son projet en publie : celles-là couvrent les deux cas, au prix d'un chiffre que personne ne remesure et qui périmera au tag suivant. Aucune des deux formes n'est meilleure dans l'absolu ; elles ne protègent simplement pas de la même chose, et il vaut mieux savoir laquelle vous avez.

**Ce que ces deux outils exigent de votre poste — mesuré le 2026-09-20, macOS 15 arm64, Docker 27.4.0.** `actionlint` n'exige rien : c'est un binaire qui lit des fichiers. `act` n'exige un démon de conteneurs **qu'au palier ③**, celui qui exécute : `act -l`, qui liste les jobs, fonctionne avec un démon **injoignable** — éprouvé avec `DOCKER_HOST` pointé sur une socket qui n'existe pas, il a listé les trois jobs du workflow qu'on lui donnait et rendu 0. **Les paliers ① et ② décrits plus bas — la configuration parse, puis les jobs prédits sont là — sont donc atteignables sans démon de conteneurs** ; seul ③, qui exécute, en demande un. C'est une bonne nouvelle pour un poste qui n'en a pas.

**Passez toujours `-P ubuntu-latest=catthehacker/ubuntu:act-latest` à `act`, en clair, et voici pourquoi.** Sans image nommée, `act` pose au premier lancement une **question interactive** : choisir entre une image `Large` (17 Go de téléchargement, 53,1 Go de stockage), `Medium` (environ 500 Mo) et `Micro` (moins de 200 Mo). **Mesuré le 2026-09-20** : hors terminal, il rend alors `level=fatal msg=EOF` et **rien d'autre** — aucun message ne dit ce qui manquait, ni qu'une question avait été posée —, et un agent, qui n'en a pas, rencontre ce mur **systématiquement**. Le diagnostic lui coûte une tentative pour une option de trente caractères. L'option nomme l'image `Medium` ; la question ne se pose plus, et le téléchargement reste raisonnable.

**`act` ne transmet aucun jeton de forge, et cette protection ne vient pas de la méthode.** Mesuré le 2026-09-20, `act` 0.2.89, macOS 15.0 arm64, Docker 27.4.0, sur un dépôt jetable : il n'en demande aucun, n'en invente aucun, et ne bronche pas quand un `${{ secrets.X }}` reste vide. C'est l'inverse de `glci`, qui transmet le `GITLAB_TOKEN` de votre poste au pipeline comme `CI_JOB_TOKEN` tant qu'on ne l'en empêche pas — d'où le `--no-token` prescrit plus haut, et dont `act` n'a pas besoin d'équivalent. Ce qui vous protège ici est **le défaut d'un outil**, pas une phrase de ce fichier : un défaut régule sans notification et sans que personne ne le lise, ce qui le rend plus fort qu'une consigne écrite — et le met hors de portée de la méthode, qui ne décide pas de ce que `nektos/act` fait par défaut. Une version suivante peut le changer sans prévenir, et rien ici ne s'en apercevra.

**Mais ce défaut ne protège que du jeton, et le généraliser serait faux à l'endroit exact où l'on cesserait de se méfier.** `act` charge par défaut **trois** fichiers de la racine de votre dépôt, et son aide les nomme : `.env`, `.secrets` et `.vars`. Le `.env` est lu sans qu'on le demande, et ses variables **ressortent en clair dans la sortie du job** — mesuré le 2026-09-20 avec une variable témoin, affichée telle quelle, reproduit deux fois. Le `.secrets` alimente `${{ secrets.X }}` : l'affichage est masqué par des astérisques, mais **la valeur est bien dans l'environnement du conteneur**, où l'astérisque ne la protège de rien. Le `.vars` alimente `${{ vars.X }}`, que la convention GitHub réserve à ce qui n'est pas sensible — une convention, et rien qui l'impose. Le scénario est banal, et c'est ce qui le rend sérieux : un dépôt applicatif porte presque toujours un `.env` de développement, la chaîne qu'on éprouve référence des actions tierces, et ces actions lisent l'environnement du conteneur.

**Lancez donc toujours `act` avec `--env-file`, `--secret-file` et `--var-file`, pointés chacun sur un fichier vide** — un fichier vide que vous créez pour l'occasion, hors du dépôt ou ignoré par lui. C'est le pendant exact, côté GitHub, du `--secrets none` de `glci` : des deux côtés, on empêche l'exécuteur local d'alimenter tout seul, avec des valeurs réelles, une chaîne que personne n'a encore relue. **Les deux premières options sont vérifiées** : avec elles, la variable du `.env` devient absente et celle du `.secrets` devient vide — mesuré le 2026-09-20, dans les mêmes conditions, les deux disparaissent. **La troisième ne l'est pas**, et elle figure donc au remède sans porter de date : neutraliser deux défauts sur trois n'a pas de sens, et la convention qui veut `vars` non sensible n'est pas un mécanisme qui l'impose.

**Cette prescription contredit sciemment la documentation d'`act`, et il vaut mieux l'écrire que vous laisser le découvrir.** Sa page d'usage, lue le 2026-09-20, donne la ligne toute prête `act -s GITHUB_TOKEN="$(gh auth token)"` — c'est-à-dire de remettre à l'outil le jeton que son défaut ne demandait pas. **Ne la suivez pas.** Le désaccord est assumé : la documentation d'un outil optimise pour que le job passe, ce fichier pour qu'un workflow que personne n'a relu ne reçoive pas vos droits. Vous la retrouverez — elle est plus accessible que ce fichier, plus facile à copier, et elle arrivera au moment où vous aurez un job rouge devant vous. C'est précisément là qu'il faut savoir que le désaccord est voulu, et non que ce fichier se trompe.

**Ce qu'obéir à l'amont coûterait, mesuré, n'est pas ce qu'on croyait.** `act` n'exécute pas le `git clone` d'`actions/checkout` : il le remplace par une copie du dépôt local, un `docker cp` du répertoire de travail. Le 2026-09-20, l'étape a rendu `✅ Success` en 25 millisecondes, **sans aucun jeton**. Refuser le jeton ne coûte donc rien sur le chemin courant, et l'argument « sinon le job est rouge » est faux tant qu'on éprouve une chaîne ordinaire. Le rouge n'arrive que pour un travail qui atteint **réellement** l'API de GitHub : publier une *release*, commenter une demande de fusion, récupérer **un autre** dépôt que celui qu'on éprouve. Ces travaux-là ne s'éprouvent pas en local, et c'est le même constat que le job de déploiement sous `glci`, qui s'exécute contre rien.

**Les deux forges ne demandent pas le même nombre d'outils, et ce n'est pas un défaut de rédaction.** Sur GitLab, `glci` relit la configuration **et** l'exécute : un binaire, une installation, un jeu d'options. Sur GitHub, il en faut **deux** — `actionlint` relit, `act` exécute —, et aucun ne fait le travail de l'autre. L'asymétrie est dans l'outillage disponible, pas dans ce fichier : elle se paie en une installation de plus, en deux conventions de nommage d'archives, et en un bloc qui peut poser l'un sans l'autre. Un dépôt qui a répondu `github` n'est donc pas moins couvert ; il a une pièce de plus à poser.

**La sortie.** Le job de déploiement affiche l'URL du staging, le commit déployé et une ligne de trace datée, qui nomme le commit. Une trace d'échec porte :

* l'étape en cause : pipeline, synchronisation ou admission ;
* le lien vers le journal du job ;
* les trois causes connues, avec leur remède :
  * **policy refusée** : lire la règle nommée dans le refus, et corriger le manifeste, pas la policy ;
  * **secret absent** : poser la variable nommée à l'endroit qu'indique « Les secrets » plus haut — variables CI/CD du projet sur GitLab, secrets de dépôt ou d'environnement sur GitHub —, protégée et masquée ;
  * **image introuvable** : vérifier que l'image a bien été poussée, et que son digest ou son tag est celui que la chaîne épingle.

**Déroger à une de ces règles se déclare.** Si votre plateforme vous empêche d'en tenir une, par exemple parce qu'elle exige un déploiement depuis une autre branche, écrivez un ADR local qui y déroge, avec son motif. La dérogation se lit alors dans le dépôt. Un contournement silencieux n'en est pas une.

**Ce qui suit ne s'adresse pas à vous au moment où vous statuez, mais juste après.** Les règles ci-dessus disent ce que votre chaîne doit respecter ; ce qui vient maintenant dit **ce que vos réponses commandent dedans**, et sert à l'agent qui l'écrit. Vous pouvez y revenir le jour où la chaîne se met en place.

**Ce que vos réponses commandent dans la chaîne.**

**Six étapes, et leur existence se lit sur vos traits — pas sur le jugement de l'agent.**

| Étape | Existe si | Sa forme vient de |
| --- | --- | --- |
| `lint` | votre dépôt porte une commande de lint, dans un fichier suivi que vous pouvez nommer — un script de `package.json`, une cible de `Makefile`, une section de `pyproject.toml`, ou leur équivalent | la commande lue, et la chaîne cite le fichier où elle l'a été |
| `test` | votre dépôt porte une commande de test, au même titre | la commande lue, fichier cité ; le seuil qui fait échouer vient de `tests.coverage_target` (`SDR-0007`) |
| `build` | toujours | `languages.main.name` (`SDR-0004`), plus le front si `SDR-0013` est tranché |
| `image` | **`hosting.offer: caas` seulement** | sous `paas`, la plateforme fabrique : aucun job d'image |
| `release` | `delivery.release_tool` n'est ni `manuel` ni `aucun` | l'outil retenu (`SDR-0011`) |
| `deploy` | **`deployment.manifests` porte un chemin relatif** — et alors un job par entrée de `delivery.environments` | l'ordre déclaré, et le déclencheur propre à chaque entrée |
| *(proposer ailleurs)* | **`deployment.manifests` porte une URL** — ce job **remplace** `deploy`, il ne s'y ajoute pas | l'adresse elle-même : la chaîne y propose un changement, et la mise en service se décide là-bas |

**`lint` et `test` se lisent sur ce que votre dépôt porte, et sur rien que vous auriez à déclarer ailleurs.** Un dépôt qui teste porte déjà sa commande dans un fichier que son propre outillage lit : c'est lui le signal. **Une étape absente est une réponse pleine** : un dépôt qui ne porte aucune commande de lint n'a pas de job `lint`, et personne n'a à en déclarer une. Une commande nommée dans un fichier de contexte agent ne fait pas exister l'étape — ce fichier est propre à un outil, et la chaîne ne sait pas le lancer.

**La chaîne ne déploie pas toujours, et c'est `deployment.manifests` qui le dit.** Un **chemin relatif** veut dire que les manifestes sont dans ce dépôt et que la chaîne les applique : `deploy` existe, un job par environnement. Une **URL** veut dire qu'ils vivent ailleurs — la chaîne y **propose un changement**, un agent extérieur réconcilie, et **ce dépôt n'a aucun job de déploiement**. La mise en service se décide dans l'autre dépôt, à la fusion de la demande.

**Lisez la forme avant d'écrire un job, et arrêtez-vous si elle ne se lit pas.** Une valeur qui n'est ni un chemin ni une URL avec son schéma, ou **un chemin relatif qui ne désigne aucun répertoire de ce dépôt** — le cas d'une URL écrite sans son schéma —, ne se devine pas : demandez, et n'écrivez rien. [`SDR-0011`](SDR-0011-delivery.md) porte la règle et ses deux formes.

**Une étape absente est une réponse pleine, pas un trou.** Un instrument de lint déclaré « aucun » ne produit pas de job. `hosting.offer: paas` supprime `image`. `delivery.release_tool: manuel` supprime `release`. `environments: []` ne produit **aucun** job de déploiement. Un agent qui ajoute un job dans un de ces cas n'a pas comblé un manque, il a inventé.

**Trois invariants traversent les six**, et ils ne se répètent pas à chaque étape : `forge.vendor` donne la syntaxe du fichier et le lieu des secrets ; `forge.gate` dit si une chaîne rouge empêche la fusion ; et les cinq règles ci-dessus valent pour **chaque** job, pas seulement pour le déploiement.

**Ce tableau s'arrête à l'existence et à la source de la forme. Il n'écrit jamais le job** — aucun extrait de fichier, aucun nom d'image, aucune commande. Ce n'est pas de la prudence : la méthode ne distribue que ce qu'elle exécute. Dire « sous `paas`, il n'y a pas de job d'image » énonce une règle que vous pouvez vérifier en relisant `SDR-0011`. Vous donner le job promettrait qu'un fichier fonctionne quelque part.

**Ce que le tableau ne peut pas vous dire, et qu'il faut demander avant d'écrire.**

**Rien de ce qui suit ne se déduit d'un trait** : ce sont des faits sur votre installation, et la méthode ne les connaît pas.

Sous une offre qui vous donne un cluster : le **nom** des variables qui authentifient la chaîne auprès du registre ; l'**espace de noms** visé ; **ce qui authentifie la chaîne auprès du cluster**, par le nom de la variable qui le porte ; l'**outil qui applique les manifestes**, quand c'est votre chaîne qui applique — `kubectl`, Helm, Kustomize : la méthode n'en prescrit aucun ; **qui relit la demande de fusion** quand votre chaîne propose ailleurs, puisque c'est elle et non votre chaîne qui met en service ; et l'**adresse du service déployé**, que « La sortie » ci-dessus vous demande d'afficher sans dire d'où elle vient.

**Cette liste ne redemande pas ce qu'un trait porte déjà.** L'adresse du registre et celle des manifestes sont des traits de [`SDR-0011`](SDR-0011-delivery.md) : les redemander à chaque chaîne serait exactement la devinette que ce SDR retire ailleurs. Ce qui reste d'elles ici est le **nom** des variables qui les authentifient, jamais leur adresse.

Sous une offre qui vous donne une plateforme : **ce qui déclare le service**, et **ce que la plateforme attend** pour l'accepter.

**Ces questions se posent en une fois, avant la première ligne de chaîne.** Ce qui reste sans réponse s'écrit dans le change, et ne se devine pas. Un agent qui écrit d'abord et découvre au premier rouge qu'il lui manquait l'espace de noms a dépensé une tentative sur une question de trente secondes.

**L'ordre compte** : la liste dépend de l'offre, donc **statuez `SDR-0011`, puis collectez, puis écrivez**. Collecter avant le verdict produit la mauvaise liste.

**On recueille des noms et des adresses, jamais des valeurs.** La règle des secrets ci-dessus le dit déjà pour les variables de la chaîne ; elle vaut identiquement pour ce qui authentifie un cluster ou un registre — **un `kubeconfig`, un jeton de registre, un mot de passe ne s'écrivent ni dans la collecte, ni dans le change, ni dans une réponse faite à l'agent.** Le redire ici n'est pas une précaution de style : un `kubeconfig` ne porte pas le mot « secret », et un agent qui lit « ce qui authentifie la chaîne » demandera raisonnablement le fichier. Il atterrirait dans un artefact versionné. **Aucun instrument ne l'attrape** — ni ici, ni chez vous : la relecture de la demande de fusion est le seul recours.

**Un inconnu reste délibérément hors de cette liste : les policies d'admission de votre cible.** On ne les demande pas, et l'on verra si le cluster refuse quelque chose. C'est le seul inconnu accepté, et le garder seul est ce qui protège votre tentative suivante — un inconnu qu'on ne nomme pas est un oubli, celui-ci est un choix.

**Éprouvez votre chaîne avant de la pousser — trois paliers, dans cet ordre.**

Chaque palier établit **un fait**, et l'outil qui l'établit dépend de votre forge : une boucle écrite en commandes serait vraie pour l'une et muette pour l'autre.

| Palier | Sur GitLab | Sur GitHub |
| --- | --- | --- |
| ① la configuration parse | `glci lint` | `actionlint` |
| ② les jobs prédits sont là | `glci show --context branch=<votre branche par défaut>` | `act -l` |
| ③ ils s'exécutent | `glci run --context branch=<votre branche par défaut> --no-token --secrets none` | `act`, avec l'image nommée et trois fichiers vides |

**Le tableau porte la forme courte ; la prose de chaque palier porte la ligne entière et ce que le palier ne voit pas.** La commande d'`act` au palier ③ ne tient pas dans une case : elle est écrite en entier là-bas, et la case ci-dessus ne fait que la nommer.

**① La configuration parse.** C'est le palier le plus bête et celui qui vous fera gagner le plus de temps.

```bash
glci lint     # sur GitLab
actionlint    # sur GitHub
```

`actionlint` sans argument trouve tout seul le répertoire `.github/workflows` le plus proche : vous n'avez ni chemin ni drapeau à lui donner.

**Le piège du deux-points suivi d'une espace mord ici aussi, et `actionlint` le nomme mieux.** Dans un scalaire YAML non quoté — la ligne d'un `run:`, par exemple —, ces deux caractères font une map là où vous vouliez une chaîne, sur GitHub exactement comme sur GitLab. `actionlint` rend alors, code de sortie 1, `could not parse as YAML: mapping values are not allowed in this context`, sous sa règle `syntax-check`, **avec la colonne pointée par un caret** — là où `glci` parle d'une configuration de script sans montrer l'endroit. Mesuré le 2026-09-20. Le remède est le même des deux côtés : quotez la ligne.

**② Les jobs que la dérivation prédit sont là, et aucun de ceux qu'elle exclut.** Appliquez à vos traits le tableau des six étapes, plus haut, puis comptez :

```bash
glci show --context branch=<votre branche par défaut>   # sur GitLab
act -l                                                  # sur GitHub
```

La chaîne doit porter **au moins les jobs que le tableau des six étapes prédit**, et **aucun de ceux qu'il exclut**.

**Ce n'est pas une égalité de comptes.** Un job de plus, que la méthode ne couvre pas, ne dévie de rien — le traiter en écart transformerait une chaîne plus riche en défaut. Ce qui est un écart est un job que le tableau **exclut** : un job d'image sous une offre qui n'en veut pas.

**Le contexte fait partie du palier.** Joué au défaut, il rendrait moins de jobs que le tableau n'en prédit, et accuserait le tableau d'un défaut qui n'est pas le sien — voir le piège décrit plus haut.

**Sur GitHub, ce palier a son angle mort à lui, et aucun drapeau ne le referme.** `act -l` **n'évalue pas les `if:`**. Mesuré le 2026-09-20, `act` 0.2.89, macOS 15.0 arm64, Docker 27.4.0, sur un dépôt jetable de trois jobs dont un déploiement borné par `if: github.ref == 'refs/heads/main'` : joué depuis une branche de fonctionnalité, où cette condition est fausse, il liste quand même les trois. Il rend le graphe **statique** des jobs déclarés, jamais les jobs qui tourneraient. Ce n'est pas un défaut de contexte comme chez `glci` — c'est ce que `-l` fait, et il n'y a donc rien à lui passer pour le corriger.

**Le contrôle du palier reste valide sur les deux forges, et il faut savoir pourquoi.** La dérivation des six étapes exclut sur vos **traits**, jamais sur une branche : un job d'image sous une offre qui n'en veut pas se voit dans les deux outils, listé alors qu'il n'aurait pas dû exister. Ce que ce palier ne dit pas sur GitHub, c'est la **règle 1** — un `deploy` listé n'est pas un `deploy` qui tournerait. C'est la commande de la section **Confirmation**, plus bas, qui la vérifie, en vous faisant lire à l'œil le `on:` du workflow et le `if:` du job.

**Les deux angles morts sont les opposés l'un de l'autre**, et c'est pourquoi une phrase unique pour les deux forges serait fausse pour l'une des deux. `glci show` rend les jobs qui **tourneraient** dans le contexte qu'on lui donne, et son défaut `merge_request` en **cache** un : il en montre trop peu, et un drapeau y remédie. `act -l` rend le graphe déclaré et en montre un **en trop** : rien n'y remédie, et seule une autre commande, ailleurs, tranche. Sur GitLab, méfiez-vous d'un job **absent** ; sur GitHub, d'un job **présent**.

**③ Ils s'exécutent — mais pas tous, et c'est normal.**

```bash
glci run --context branch=<votre branche par défaut> --no-token --secrets none   # sur GitLab

: > "${TMPDIR:-/tmp}/act-vide"                                                   # sur GitHub
act -P ubuntu-latest=catthehacker/ubuntu:act-latest \
  --env-file "${TMPDIR:-/tmp}/act-vide" \
  --secret-file "${TMPDIR:-/tmp}/act-vide" \
  --var-file "${TMPDIR:-/tmp}/act-vide"
```

**La ligne d'`act` est longue, et chacun de ses morceaux a été prescrit plus haut.** `-P` nomme l'image, et c'est ce qui évite la question interactive qui, hors terminal, ne rend qu'un `EOF` sans rien expliquer ; les trois fichiers vides empêchent `act` d'aller chercher tout seul les `.env`, `.secrets` et `.vars` de votre dépôt — avec la réserve écrite plus haut, que seules les deux premières options ont été vérifiées. Le `: >` crée ce fichier vide, ou le vide s'il existait déjà.

**Sur Apple Silicon, ajoutez `--container-architecture linux/amd64`.** C'est dans cette configuration que la mesure ci-dessous a été faite, et `act` vous en avertit lui-même sur ces machines. Sur un poste `amd64`, elle ne sert à rien : c'est une option conditionnée par votre matériel, pas une prescription qui vaudrait partout.

**Attendez le vert des jobs qui ne visent aucune cible** : lint, test, construction. **Le job qui déploie, ou celui qui propose un changement à une autre adresse, échouera** — il n'a ni cluster, ni registre, ni identifiant réel sous l'outil local. **Cet échec est attendu ; ce n'est pas un défaut de votre chaîne.**

**Le verdict global sera rouge des deux côtés, et c'est cohérent.** L'un comme l'autre compte un job échoué comme un échec d'ensemble : vous lirez un rouge alors que tout ce qui pouvait passer est passé. **Lisez le détail par job, pas la bannière.** Sur GitLab, mesuré le 2026-09-20 sur un pipeline d'essai à trois jobs dont un de déploiement : `2 passed`, `1 failed`, verdict global `FAILED`, en 17 secondes. Pour obtenir un vert franc, lancez nommément les jobs qui ne visent aucune cible — `glci run job_un job_deux` — plutôt que la pipeline entière.

**Sur GitHub, une chaîne d'essai de même forme rend le même verdict, et l'échec ne dit pas ce qu'on croit.** Mesuré le 2026-09-20, `act` 0.2.89, macOS 15.0 arm64, Docker 27.4.0, sur le dépôt jetable de trois jobs décrit au palier ② : `lint` au vert, `test` au vert, `deploy` au rouge sur `kubectl: command not found` — `exitcode '127'`, c'est-à-dire une commande absente du conteneur, et **non** un défaut d'authentification —, puis `Error: Job 'deploy' failed` et un code de sortie de 1, le tout en 44 secondes. **Le chemin de sortie existe ici aussi** : `act -j lint` rend 0 en 3 secondes, image déjà tirée. Là où `glci` prend les jobs nommément, `act` en prend un par `-j`.

**Ne levez rien pour obtenir ce vert-là, et ce que vous ne devez pas lever dépend de votre forge.** Sur GitLab, **gardez les deux options**, qui ne protègent pas de la même chose : `--no-token` retient le jeton de votre poste, `--secrets none` retient les variables réelles de votre projet. En lâcher une pour décrocher un vert livre entièrement ce qu'elle retenait à un pipeline que personne n'a relu. Sur GitHub, `act` ne transmet aucun jeton — il n'y a rien à retenir de ce côté-là —, mais retirer `--env-file`, `--secret-file` ou `--var-file` lui rend les fichiers de votre dépôt, et les donne aux actions tierces que le workflow appelle. Le paragraphe sur la mise au point locale le dit déjà dans les deux cas ; c'est ici qu'on est tenté de l'oublier, parce que c'est ici qu'un vert manque.

**L'ordre des trois n'est pas un rangement, c'est leur coût.** ① est instantané sur les deux forges. ③ tire des images et s'exécute : sur une chaîne d'essai de **même forme** — trois jobs dont un déploiement qui échoue —, **17 secondes sous `glci` et 44 sous `act`, le 2026-09-20**. Les deux restent du même ordre de grandeur, des dizaines de secondes, et `act` coûte environ **deux fois et demie** son pendant GitLab. L'argument tient donc sur les deux forges, et il tient **mieux** sur GitHub. Ce coût croît ensuite avec votre chaîne — une chaîne qui construit et teste se compte en minutes —, et un agent qui commence par ③ paie tout ça pour découvrir une virgule mal placée. Le motif ne dépend pas du chiffre : il tient dès que ③ coûte plus que ①.

**Sur GitHub, un coût s'ajoute une fois et une seule : le premier tirage d'image.** Il ne se repaie pas au palier ③ suivant — c'est ce que dit la mention « image déjà tirée » de la mesure ci-dessus. Son volume dépend de l'image que `-P` nomme : la ligne prescrite nomme la `Medium`, et le paragraphe sur `-P` plus haut dit ce que la `Large` aurait coûté en téléchargement et en stockage.

**Ce que les trois paliers réunis ne sauvent pas, et c'est le plus important.** Ils ne jugent que la **présence** d'un job, jamais sa justesse : une chaîne qui rend six jobs peut être fausse sur le contenu des six. Et ils sont **aveugles au contenu du job de déploiement** — l'outil local l'exécute **contre rien**. L'authentification au registre, l'invocation de l'outil qui applique, l'espace de noms, les règles d'admission de votre cible : tout cela traverse les trois verts sans être touché.

**Trois paliers au vert ne veulent donc pas dire que votre déploiement marchera.** Ils veulent dire que ce qui pouvait se constater sans cible a été constaté. Le reste se découvre à la poussée, et c'est pour ça que le SDR vous fait poser les questions de la collecte avant d'écrire.

**Rien ne lance cette boucle**, et rien ne vérifie que vous vous arrêtez au premier palier rouge. C'est la relecture de la demande de fusion qui la réclame, comme tout le reste de ce fichier.

**Décision, et où elle s'écarte de la proposition.** `github` au lieu de `gitlab` : le dépôt est public sur GitHub, et sa CI, ses réglages et ses releases y vivent. La porte `bloquante` est adoptée telle quelle.

**Provenance.** Constatées : `.github/workflows/`, et le ruleset de `.github/settings.json`, qui exige les checks `lint`, `test`, `security`, `image` et `pr-title` avant toute fusion sur `main`.

### Consequences

Rien n'arrive sur `main` sans les cinq checks verts ; le socle CI est partagé avec `knock` et `uske` (`socle-drift.yml`).
Le coût : un check instable bloque toutes les pull requests jusqu'à sa correction.

### Confirmation

**Une commande, et c'est un plancher, pas une garantie.** Rien ne la lance : c'est la relecture de la merge request qui la réclame.

**Le job de déploiement ne tourne que sur la branche par défaut** (règle 1). **Une commande par forge** : la vôtre lit le fichier de chaîne que vous avez, et celle de l'autre forge ne vous sert à rien. Depuis la racine du dépôt.

Sur **GitLab** :

```bash
grep -nE '^[a-zA-Z0-9_.-]+:' .gitlab-ci.yml | cut -d: -f1 | while read -r l; do
  sed -n "${l},/^[a-zA-Z0-9_.-]*:/p" .gitlab-ci.yml | grep -q 'environment:' \
    && sed -n "${l}p" .gitlab-ci.yml
done
```

Sur **GitHub** — même clé, autre fichier : `environment:` est aussi ce qu'un job de GitHub Actions déclare.

```bash
grep -rn --include='*.yml' --include='*.yaml' 'environment:' .github/workflows/
```

Sortie attendue, dans les deux cas : **les seuls endroits portant `environment:`**. Pour chacun, vous vérifiez à l'œil qu'il est borné à la branche par défaut — par ses `rules:` sur GitLab ; par le `on:` du workflow et le `if:` du job sur GitHub.

**Ce qu'elles n'attrapent pas** : un déploiement fait par un job qui ne déclare pas `environment:` — rien ne l'y oblige ; une condition de branche écrite ailleurs que là où vous la cherchez ; **une protection d'environnement ou un *ruleset*, qui ne vivent pas dans le dépôt** et qu'aucun `grep` ne verra ; et tout ce qui relève des règles 2, 3, 4 et 5, que `grep` ne sait pas juger.

**Ce qu'elle accuse à tort** : un job qui porte `environment:` **sans être un déploiement**. Un job qui publie un site de documentation en est l'exemple — il publie un site, il n'a pas à être borné à la branche par défaut pour les raisons de la règle 1. Un signalement n'est donc pas un défaut : c'est une ligne à regarder.

## More Information

| Clé | Ce qu'elle porte | Valeurs admises |
| --- | --- | --- |
| `forge.vendor` | où vivent le dépôt et ses demandes de fusion, **et donc la syntaxe du fichier de chaîne** | `gitlab`, `github`. **Rien d'autre** : une troisième forge se dit par `rejected`, dont le motif la nomme |
| `forge.gate` | ce qu'une chaîne rouge empêche | `bloquante` — rien ne fusionne au rouge ; `informative` — elle rapporte, la relecture décide ; `aucune` — il n'y a pas de chaîne |

**Les deux clés sont vérifiables**, toutes deux portant un ensemble fermé. `.mdschema.yml` **nomme** une valeur hors de l'ensemble ; il ne refuse pas, et le code de sortie ne change pas. Une forge que ce fichier n'admet pas ne se corrige donc pas en écrivant sa valeur ici : elle se dit par `rejected`.

**`forge.gate: aucune` n'est pas un aveu.** C'est la réponse d'un dépôt qui n'a rien à exécuter — de la documentation, des schémas, de la configuration relue à la main. Elle se prend, comme les autres.

**Et c'est elle qu'il faut pour une absence de chaîne, pas `rejected`.** Un dépôt sans chaîne répond `forge.gate: aucune` et **garde son bloc `traits:`** ; il ne rejette pas. `rejected` a ici **un seul emploi** : une forge que l'ensemble n'admet pas. Prenez-le en sachant ce qu'il emporte — voir plus haut, « Ce verdict coûte plus qu'il n'y paraît ».

**Ce que ces clés ne couvrent pas** : ni ce que la chaîne exécute — les instruments de test et de lint se déclarent ailleurs, et [`SDR-0007`](SDR-0007-tests.md) porte le seuil de couverture — ni comment on contribue au dépôt, qui est dans [`SDR-0009`](SDR-0009-branching.md).

**La valeur s'écrit dans ce fichier, et nulle part ailleurs.** Aucun autre fichier ne la recopie : celui qui en a besoin renvoie ici. C'est ce qui garantit qu'elle ne peut pas être contredite ailleurs.

**Une clé laissée vide n'est pas une réponse** — les trois sont exigées. Vous n'avez pas à le vérifier à l'œil. Depuis la racine de votre dépôt :

```bash
( cd docs/adr && npx @jackchuka/mdschema@0.15.1 check '*.md' )
```

**Si votre dépôt n'a ni Node ni `npm`, cette ligne ne vous sert à rien**, et le dire vaut mieux que le supposer. **Elle peut aussi échouer alors que Node est là.** Mesuré le 2026-09-20 sur macOS arm64, avec `npm` 10.9.8 puis 11.6.0 : `npx` rend `sh: mdschema: command not found`, parce que `npm` n'installe pas le lien du binaire — sur un répertoire neuf, avec `bin-links` à `true` et `ignore-scripts` à `false`. Le paquet est pourtant posé, sa dépendance de plateforme aussi, et son point d'entrée existe.

Dans les deux cas, `mdschema` est un binaire autonome : prenez-le dans les *releases* de [son dépôt](https://github.com/jackchuka/mdschema) et lancez `mdschema check '*.md'` depuis ce répertoire. **C'est le chemin sûr**, et non un repli de second choix. La ligne ci-dessus n'est qu'un raccourci, qui évite d'installer quoi que ce soit — quand il fonctionne.

Le schéma qu'elle applique est le `.mdschema.yml` de ce même répertoire, posé par la méthode. Elle nomme, fichier par fichier : une clé restée vide, une valeur hors de l'ensemble admis, un `status:` resté `proposed`, une `date:` absente, et le mode d'emploi qu'on aurait oublié de supprimer. **Elle reconnaît ce dernier à sa première phrase**, pas au tableau : le tableau a le droit de rester, et le garder ne déclenche rien. Elle ne juge pas votre décision — seulement qu'elle est prise.
