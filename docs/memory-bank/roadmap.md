# Regis Roadmap

> Supplemental file: this is a planning artifact that complements the core Memory Bank files.

> Last updated: 2026-06-25 · Current version: v0.37.x · Stage: pre-v1

## Positionnement

Sécurité conteneur & policy-as-code, avec un pivot vers la **provenance
supply-chain** : les verdicts Regis (SARIF, `result.kind` discriminant
policy/vuln) sont consommables comme attestations signées à la porte d'entrée
d'un registre.

Format : **Now / Next / Later** — pas de dates dures (évite la fausse précision).

## Memory Bank Alignment

- Garder les items synchronisés avec `docs/memory-bank/projectbrief.md` et `progress.md`.
- Traiter `decisionLog.md` et `roadmap.md` comme historique de planification supplémentaire, pas comme contexte opérationnel primaire.

---

## Récemment livré

| Item                                                                              | Statut |
| --------------------------------------------------------------------------------- | ------ |
| Migration hexagonale (ports & adapters, imposée par import-linter)                | Done   |
| Sortie SARIF des verdicts playbook (`result.kind` policy/vuln) + `ruleset_hash`   | Done   |
| Images conteneur multi-arch (linux/amd64 + arm64)                                 | Done   |
| Automatisation des dépendances → Renovate                                         | Done   |
| Intégration GitLab CI-native extraite vers un template dédié                      | Done   |
| Format playbook → enveloppe Kubernetes (`apiVersion` / `kind`)                    | Done   |
| Réduction taille image (variantes slim/full, fetch outils paresseux)              | Done   |

---

## Now — engagé / en cours

| Item                                                                                          | Statut    | Réf        |
| --------------------------------------------------------------------------------------------- | --------- | ---------- |
| Réparer l'install getting-started (Docker → `ghcr.io`, `pip` → `uv`)                          | On Track  | PR #808    |
| Cache registry par-run + handoff SBOM syft → grype (performance de scan)                       | Planned   | issue #806 |
| Refacto de la commande `analyze.py` + resserrer le layering `utils/`                          | Planned   | issue #807 |
| Santé projet : `SECURITY.md`, `CONTRIBUTING.md`, templates d'issues                           | Planned   | issue #810 |
| **Format bundle playbook** (`playbook.yaml` + `README.md` + `inputs.schema.json` + `InputsAnalyzer`) | Planned | sprint     |
| Finitions site de doc (branding, navigation, SEO) + arrêt des snapshots versionnés            | Planned   | sprint     |

---

## Next — planifié (≈ 1-3 mois)

| Item                                                                                                          | Note                                                          |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **Intégration provenance** : verdicts Regis → attestations signées à la porte d'un registre (houba)           | contrat SARIF déjà conforme ; dépend de la maturité houba    |
| Support **Harbor natif** (abstraction `RegistryProvider`)                                                     | feature produit générique                                    |
| Archétypes de playbook réutilisables : gate d'admission d'image · conformité catalogue continue · progression par tiers (bronze → argent → or) | bâtis sur le format bundle                  |
| Distribution : `uv tool install` + nom de distribution PyPI non-collisionnant                                | issu du fix d'install (#809)                                 |
| Pipeline i18n de la documentation (traduction automatisée)                                                    | générique                                                    |

---

## Later — directionnel (≈ 3-6+ mois)

| Item                                                          | Note                          |
| ------------------------------------------------------------ | ----------------------------- |
| Comparaison de posture multi-image / flotte (`regis diff`)   | directionnel                  |
| Versioning playbook/policy avec ranges de compatibilité      | design spike requis           |
| Agrégation de score org-level + reporting                    | directionnel                  |
| Guide développeur : création d'analyzers custom              | directionnel                  |
| Self-scan CI (Regis s'analyse lui-même à chaque release)     | signal de maturité            |
| Import / fusion d'un catalogue d'images existant             | design spike requis           |

---

## Risques & dépendances

- **Maturité houba (pré-prod)** cadence le calendrier de l'intégration provenance. Mitigation : le contrat SARIF est **gelé**, donc Regis intègre contre une interface stable pendant que houba durcit.
- **Capacité** : Now porte déjà 6 items ; Next / Later sont directionnels, pas engagés. Tout ajout en Now implique qu'un item en sorte (zéro-somme contre la capacité).
- **Dépendances bloquées** : migration dashboard Tailwind v4 — **coupée** (la dashboard standalone est abandonnée ; la visibilité passe par `report.json` + l'outillage de provenance).
