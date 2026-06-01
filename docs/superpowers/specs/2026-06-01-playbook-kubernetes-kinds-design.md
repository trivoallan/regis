# Design — Format de playbook aligné sur les _kinds_ Kubernetes

|                             |                                                                                                                                                                  |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Date**                    | 2026-06-01                                                                                                                                                       |
| **Statut**                  | Validé (brainstorming) — prêt pour `writing-plans`                                                                                                               |
| **Auteur**                  | Tristan Rivoallan (+ Claude)                                                                                                                                     |
| **Remplace / fait évoluer** | [`2026-05-31-playbook-versioning-design.md`](2026-05-31-playbook-versioning-design.md) (l'entier `schemaVersion` introduit là est ici remplacé par `apiVersion`) |
| **Type de changement**      | Breaking, pré-v1 → `feat(playbook)!:` (bump mineur via `bump-minor-pre-major`, 0.33 → 0.34)                                                                      |

## Contexte

Le format de playbook actuel est un YAML **à plat** : `schemaVersion` (entier) + `version` (SemVer) + `name`, puis `tiers`, `rules`, `badges`, `integrations`, `links` (et `pages`/`sections`/`sidebar` dépréciés). Il est chargé par `regis/playbook/loader.py`, qui dispatche sur l'entier `schemaVersion` vers un schéma JSON (`regis/schemas/playbook/v1/definition.schema.json`) via `schema_registry.py`.

L'écosystème cible de Regis est K8s-adjacent : la roadmap mentionne un déploiement des rapports sur cluster Kubernetes, et un **plugin Backstage** est en cours dans un dépôt dédié. Or les entités Backstage **comme** les ressources Kubernetes partagent la même enveloppe : `apiVersion` / `kind` / `metadata` / `spec`. Adopter cette convention rend les playbooks immédiatement familiers aux équipes plateforme/GitOps et cohérents avec le reste de l'outillage.

## Objectif et périmètre

**Objectif** : adopter l'enveloppe `apiVersion` / `kind` / `metadata` / `spec` sur le playbook existant — un changement **structurel/cosmétique**. La **sémantique d'évaluation reste strictement inchangée** (mêmes règles, mêmes tiers, mêmes badges, même moteur JSON Logic).

**Hors périmètre (YAGNI)** — explicitement reportés :

- **Décomposition multi-_kinds_** (un `RuleSet`, un `Tier`, une `Integration` comme ressources séparées et référençables). Un seul _kind_ : `Playbook`.
- **CRD réelles / opérateur in-cluster / réconciliation / `kubectl apply`**.
- **Modèle Python typé** (`Playbook` dataclass) — voir « Approches écartées ».
- Toute évolution de la **sémantique des règles**.

## Décisions verrouillées (issues du brainstorming)

1. **Enveloppe familière**, _kind_ unique `Playbook`, sémantique inchangée.
2. **Remplacement net** du versionnage : `apiVersion` devient l'unique source de version du format ; l'entier `schemaVersion` disparaît. L'ancien format à plat **n'est plus accepté** par le loader ; `regis playbook upgrade` convertit les bundles existants. (Justifié : pré-v1, très peu de fichiers à migrer, et en K8s `apiVersion` _est_ le mécanisme de version.)
3. **`apiVersion: regis.trivoallan.dev/v1alpha1`**, `kind: Playbook`. La maturité `v1alpha1` assume le churn récent du format et réserve le droit de casser avant `v1`.
4. **Mapping `metadata` de style Backstage** : `metadata.name` (id machine), `metadata.title` (affichage), `metadata.description`, et version SemVer du bundle → label `app.kubernetes.io/version`.
5. **Stratégie de lecture côté code : normalisation au chargement** (approche A) — le loader renvoie un dict aplati ; les consommateurs ne changent pas.

## Format cible

### Avant → Après

**Avant** (`regis/playbooks/default/playbook.yaml`, abrégé) :

```yaml
# yaml-language-server: $schema=../schemas/playbook/v1/definition.schema.json
schemaVersion: 1
version: 1.0.0
name: RegiS Default Playbook
tiers: [...]
rules: [...]
badges: [...]
integrations: { gitlab: { ... } }
links: [...]
```

**Après** :

```yaml
# yaml-language-server: $schema=../../schemas/playbook/v1alpha1/playbook.schema.json
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: default # id machine (ex-`slug`, ou `name` slugifié)
  title: RegiS Default Playbook # nom d'affichage (ex-`name`)
  # description: ...                     # optionnel (ex-`description`)
  labels:
    app.kubernetes.io/version: "1.0.0" # version SemVer du bundle (ex-`version`)
spec:
  tiers: [...]
  rules: [...]
  badges: [...]
  integrations: { gitlab: { ... } }
  links: [...]
```

### Règles de mapping

| Ancien champ                                                  | Nouveau emplacement                            |
| ------------------------------------------------------------- | ---------------------------------------------- |
| `schemaVersion` (entier) + `version` (versionnage **format**) | `apiVersion: regis.trivoallan.dev/v1alpha1`    |
| _(implicite)_                                                 | `kind: Playbook`                               |
| `slug` (ou `name` slugifié si absent)                         | `metadata.name`                                |
| `name` (affichage)                                            | `metadata.title`                               |
| `description`                                                 | `metadata.description`                         |
| `version` (SemVer du **bundle**)                              | `metadata.labels["app.kubernetes.io/version"]` |
| `tiers`, `rules`, `badges`, `integrations`, `links`           | `spec.*`                                       |

### Nettoyages inclus

Le format change de toute façon — on solde la dette dépréciée :

- **Suppression de `pages` / `sections` / `sidebar`** (et de leurs `$defs` `page`/`section`/`display`/`widget`/`level`/`scorecard`), déjà dépréciés et ignorés par le viewer Docusaurus. Conséquence : le cookiecutter `playbook/`, encore en `pages:`, est réécrit en `spec.rules`.
- **Correction de la directive `$schema`** : l'actuelle `../schemas/...` est erronée d'un niveau depuis `playbooks/default/` (résout vers `playbooks/schemas/`, inexistant). Le nouveau pointe `../../schemas/playbook/v1alpha1/playbook.schema.json`.

## Schéma & nommage

- **Dossier** : `regis/schemas/playbook/v1/` → **`regis/schemas/playbook/v1alpha1/`**. **Fichier** : `definition.schema.json` → **`playbook.schema.json`** (reflète le _kind_).
- `jsonlogic.schema.json` et `result.schema.json` **restent** à la racine `regis/schemas/playbook/` ; la référence relative `../jsonlogic.schema.json` depuis `v1alpha1/playbook.schema.json` continue de résoudre correctement (mémoïsation du registre `referencing` inchangée dans `loader._build_validator_registry`).
- **`$id`** : `https://trivoallan.github.io/regis/schemas/playbook/v1alpha1/playbook.schema.json`.
- **Structure du nouveau schéma** :
  - `required: ["apiVersion", "kind", "metadata", "spec"]`, `additionalProperties: false`.
  - `apiVersion` : `const: "regis.trivoallan.dev/v1alpha1"`.
  - `kind` : `const: "Playbook"`.
  - `metadata` : objet, `required: ["name"]`.
    - `name` : pattern DNS-1123 label strict K8s `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`, `maxLength: 63`.
    - `title`, `description` : string optionnels.
    - `labels` : objet `string → string` ; **requiert** la clé `app.kubernetes.io/version` (préserve l'invariant « tout playbook déclare une version » du design versionnage). Valeur validée en SemVer (`^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$`) — ce pattern réutilise celui de l'ancien champ `version`.
    - `annotations` : objet `string → string` optionnel.
  - `spec` : objet `additionalProperties: false` portant `tiers`, `rules`, `badges`, `integrations`, `links` — les définitions actuelles sont déplacées **telles quelles** sous `spec` (mêmes `$defs` `checklist_item`, mêmes shapes rule/tier/badge/integration).

> **Note de conception** : exiger une clé de label précise (`app.kubernetes.io/version`) est légèrement inhabituel en K8s pur (les labels y sont optionnels). On le conserve pour ne pas régresser l'invariant de version récemment introduit. Alternative envisagée puis écartée : rendre la version optionnelle (apiVersion portant déjà la version du _format_). Réexaminable post-v1.

## Implémentation

### A. Stratégie : normalisation au chargement _(approche retenue)_

`load_playbook()` parse l'enveloppe, valide contre le schéma, puis renvoie un **dict interne aplati** où `spec.*` remonte au top-level et `metadata` est projeté en `name`/`slug`/`version`/`description`. **Aucun des ~12 consommateurs ne change.** L'enveloppe reste une préoccupation purement _fichier_.

### B. Normalisation concrète

Nouvelle fonction dans `loader.py`, appelée par `load_playbook()` juste avant le `return` :

```python
def normalize_playbook(raw: dict[str, Any]) -> dict[str, Any]:
    meta, spec = raw.get("metadata", {}), raw.get("spec", {})
    labels = meta.get("labels", {})
    return {
        # enveloppe conservée pour l'audit / propagation
        "apiVersion": raw["apiVersion"],
        "kind": raw["kind"],
        "metadata": meta,
        "spec": spec,
        # projection « plate » consommée par evaluator / integrations / report
        "name": meta.get("title") or meta.get("name"),
        "slug": meta.get("name"),
        "version": labels.get("app.kubernetes.io/version"),
        "description": meta.get("description"),
        **spec,  # tiers, rules, badges, integrations, links
    }
```

(`spec` ne contient aucune clé en collision avec `name`/`slug`/`version`/`description`, donc le `**spec` est sûr.)

### C. Loader & registre

- `loader.py` : `_extract_schema_version()` → `_extract_api_version()` qui lit `apiVersion` (str) **et** `kind`, vérifie `kind == "Playbook"`, et renvoie l'`apiVersion` comme clé de dispatch. Messages d'erreur réécrits :
  - champ manquant → « playbook '…' is missing required field 'apiVersion'. Add `apiVersion: regis.trivoallan.dev/v1alpha1` and `kind: Playbook` at the top of the file. Supported: … ».
  - `kind` absent/incorrect → message dédié.
  - `apiVersion` inconnu → « declares apiVersion=… but this regis (vX) only supports […] ».
- L'exception `PlaybookVersionError` est conservée (sémantique « erreur de version/format ») ; renommage facultatif en `PlaybookFormatError` à trancher au plan (impact : imports dans `commands/playbook.py`).
- `schema_registry.py` : clé `int` → clé `str` (apiVersion). `_SCHEMAS = {"regis.trivoallan.dev/v1alpha1": _load_schema_v1alpha1}` ; `_load_schema_v1alpha1()` lit `regis.schemas.playbook.v1alpha1` / `playbook.schema.json`. `supported_versions()` renvoie la liste des apiVersions.

### D. `regis playbook upgrade` (réécriture)

Passe d'une **injection** de scalaires à une **restructuration** (toujours `ruamel.yaml` pour préserver les commentaires au mieux) :

1. crée `apiVersion` / `kind` en tête ;
2. construit `metadata` : `name` ← `slug` existant, sinon `slugify(name)` ; `title` ← `name` ; `description` ← `description` ; `labels["app.kubernetes.io/version"]` ← `version` existant, sinon `"1.0.0"` ;
3. déplace `tiers`/`rules`/`badges`/`integrations`/`links` sous `spec` ;
4. supprime `pages`/`sections`/`sidebar` (avec un message listant ce qui a été retiré).

Reste **idempotent** : no-op si le document est déjà une enveloppe (`apiVersion` présent). Gère aussi bien les fichiers « legacy plat à `schemaVersion: 1` » que les très anciens à `pages:`.

### E. `regis playbook validate` & propagation rapport

- `validate` : remplace l'affichage `schemaVersion=… version=…` par `apiVersion=… kind=… version=<label>`.
- `evaluator.py:195-197` (seul point lisant les champs méta du playbook pour le contexte d'éval) :
  - `playbook_name` ← `playbook.get("name")` — **inchangé** (`name` ← `metadata.title`).
  - `playbook_version` ← `playbook.get("version")` — **inchangé** (← label).
  - `"schema_version": playbook.get("schemaVersion")` → **`"api_version": playbook.get("apiVersion")`**.

### F. Fichiers in-repo à migrer

- `regis/playbooks/default/playbook.yaml` → enveloppe.
- `regis/cookiecutters/playbook/{{cookiecutter.project_slug}}/playbook.yaml` → enveloppe **+ réécriture depuis `pages:` vers `spec.rules`**.
- `regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/playbook.yaml` → enveloppe.
- Directives `# yaml-language-server: $schema=…` mises à jour (chemin local pour le défaut ; URL `raw.githubusercontent.com/.../v1alpha1/playbook.schema.json` pour les cookiecutters).

### G. Tests (~15 fichiers touchent les playbooks)

- `test_playbook_loader.py` : dispatch sur `apiVersion`/`kind`, normalisation, messages d'erreur (apiVersion manquant, kind incorrect, apiVersion inconnu).
- Schéma : un cas valide + cas invalides (`metadata.name` non conforme, label version manquant/non-SemVer, `additionalProperties` au niveau `spec`).
- `tests/commands/test_playbook_upgrade.py` : flat→enveloppe (avec et sans `slug`/`version`/`pages`), idempotence.
- `tests/commands/test_playbook_validate.py` : sortie mise à jour.
- Fixtures inline en format plat (dans `test_playbook_engine.py`, `test_coverage_engine.py`, `test_remote_playbook.py`, `test_analyze_rerun.py`, `test_bootstrap*.py`, `test_cli.py`, `test_utils_report.py`) migrées vers l'enveloppe.
- Couverture ≥ 90 % (gate CI).

### H. Documentation & skill

- Doc concepts + référence playbooks (`docs/website/docs/...`) : exemples et tableau de champs réécrits.
- **Skill `/create-playbook`** : génère désormais l'enveloppe (apiVersion/kind/metadata/spec) au lieu du format à plat.

## Approches écartées

- **B — Propager l'enveloppe** : les consommateurs lisent `playbook["spec"]["rules"]`, `playbook["metadata"]["title"]`… ~12 sites édités, aucun bénéfice fonctionnel vu la sémantique inchangée. Écarté.
- **C — Modèle Python typé** (`Playbook` dataclass exposant `.rules`, `.metadata`, …) : meilleure ergonomie/type-hints long terme, mais c'est le plus gros chantier et ça dépasse « cosmétique ». Reporté ; redeviendra pertinent si l'on décompose un jour en multi-_kinds_.

## Migration & compatibilité

- **Rupture nette, sans fenêtre de transition** : le loader rejette l'ancien format à plat (message d'erreur orientant vers `regis playbook upgrade`). Acceptable car pré-v1 et surface minuscule.
- **Bump** : `feat(playbook)!:` → mineur `bump-minor-pre-major` (0.33 → 0.34).
- Les utilisateurs externes (playbooks hors dépôt) migrent via `regis playbook upgrade <fichier>`.

## À vérifier au moment du plan

1. Aucune **règle JSON Logic** ni le code dashboard ne lit `report.playbook.schema_version` (le champ d'audit renommé en `api_version`). Risque faible — `github_cli.py` lit le **résultat** évalué (`report_data["playbook"]`), pas la définition.
2. Le concept distinct de **`schemaVersion` du `report.json`** (contrat dashboard Phase 0, `REPORT_SCHEMA_VERSION`) **n'est pas** affecté — ne pas le confondre avec le `schemaVersion` du playbook qu'on supprime. Confirmer qu'aucun renommage ne fuit dans l'enveloppe rapport.
3. Le fichier d'override `--rules` (lu par `analyze.py`/`rules.py` via `data.get("rules")`) est une **liste de règles nue**, pas un _kind_ `Playbook` → **hors périmètre**, laissé tel quel.
4. Présence éventuelle de playbooks en format plat dans des fixtures non détectées par le grep initial.

## Critères d'acceptation

- [ ] `regis/playbooks/default/playbook.yaml` est au format enveloppe et passe `regis playbook validate`.
- [ ] Un playbook à l'ancien format plat est **rejeté** par le loader avec un message orientant vers `upgrade`.
- [ ] `regis playbook upgrade` convertit un playbook plat (legacy `pages:` inclus) en enveloppe valide, et est idempotent.
- [ ] Le rapport généré porte `playbook_name`, `playbook_version` et `api_version` corrects ; la sémantique d'évaluation (scores, tiers, badges) est **identique** à l'avant-refonte sur le playbook par défaut.
- [ ] Les deux cookiecutters scaffoldent des playbooks au format enveloppe valides.
- [ ] Le skill `/create-playbook` produit l'enveloppe.
- [ ] Suite de tests verte, couverture ≥ 90 %.
