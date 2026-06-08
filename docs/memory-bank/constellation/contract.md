# Contrat inter-repos — constellation Regis

> NORMATIF. Tout sous-projet qui sérialise ou consomme un report DOIT respecter ce
> contrat. **À lire avant toute modification touchant la sérialisation/consommation
> d'un report.** En cas de conflit entre ce fichier et le code du cœur, le code fait
> foi — ouvrez une PR pour réaligner ce fichier.

## Report schema

- **Version courante : `REPORT_SCHEMA_VERSION = 2`** (`regis/utils/report.py`).
- Le report sérialisé porte `schemaVersion` ; `ensure_schema_version()` le garantit.
- Schéma : `regis/schemas/report/report.schema.json`.
- **Politique de bump** : tout changement cassant de structure du report incrémente
  `REPORT_SCHEMA_VERSION`. Les consommateurs (`regis-backstage`, `regis-gitlab`,
  `regis-action`) lisent `schemaVersion` et doivent gérer le refus/avertissement sur
  version inconnue. Annoncer tout bump dans la PR du cœur et avertir les sous-projets.

## Presentation

- Section neutre **`spec.presentation`** du playbook (ex-`spec.integrations.gitlab`,
  généralisée le 2026-06-06). Schéma : `regis/schemas/playbook/`.
- Les champs report liés à la présentation sont neutres (non couplés à un fournisseur CI).

## Analyzers (entry points)

Les analyzers sont découverts via `project.entry-points."regis.analyzers"`
(`pyproject.toml`). Un sous-projet qui ajoute un analyzer s'enregistre par ce mécanisme.
Liste courante (12) : `versioning`, `scorecarddev`, `oci`, `cve`, `endoflife`,
`popularity`, `size`, `freshness`, `provenance`, `sbom`, `hadolint`, `dockle`.

## Vocabulaire & conventions

- Termes : voir `glossary.md` (finding → metric → criterion → rule).
- Conventions de travail (commits, branches, style) : voir `.agent/rules/` du cœur.
