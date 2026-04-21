# Regis Roadmap

> Supplemental file: this is a planning artifact that complements the core Memory Bank files.

> Last updated: 2026-04-21 · Current version: v0.28.6

## Status Overview

v0.28.6 shipped · Chemin v1.0.0-alpha défini · Cible : pilote équipes internes

## Memory Bank Alignment

- Keep roadmap items synchronized with `docs/memory-bank/projectbrief.md` and `docs/memory-bank/progress.md`.
- Treat `decisionLog.md` and `roadmap.md` as supplemental planning history, not the primary operational context.

---

## Cible v1.0.0-alpha — Pilote

La v1 est la première version déployée auprès d'équipes pilotes réelles :

- **Direction Expertise Applicative** — architectes et experts sécurité
- **Équipe projet**

### Contexte d'usage

- Registres d'images : **Harbor**
- Distribution des rapports : **GitLab Pages** (primaire) ou cluster Kubernetes (fallback)
- Langue : **français** — onboarding équipes internes
- UX/DevEx : critiques — premiers utilisateurs sont des architectes, pas des SREs

### Trois playbooks cibles

| Playbook               | Porteur        | Objectif                                                      |
| ---------------------- | -------------- | ------------------------------------------------------------- |
| **Validation import**  | Architectes    | Go/no-go binaire sur une image avant import dans le catalogue |
| **Contrôle catalogue** | Architectes    | Surveillance continue + preuve de qualité pour audit          |
| **Progression projet** | Équipes projet | Amélioration progressive par tiers (bronze → argent → or)     |

### Feature set v1 (Must-have)

| Feature                             | Pourquoi v1                                               |
| ----------------------------------- | --------------------------------------------------------- |
| Playbook bundle format              | Fondation des 3 playbooks métier                          |
| Intégration Harbor native           | skopeo non garanti en infra interne fermée                |
| Trois playbooks métier              | Livrables directs du pilote                               |
| Doc en français (pipeline LLM)      | Onboarding équipes internes sans barrière linguistique    |
| Finitions site de doc               | UX/DevEx — première impression architectes, design system |
| GitLab Pages / K8s deployment guide | Distribution des rapports en contexte GitLab interne      |
| Moratoire snapshots doc             | Cleanup avant v1                                          |

### Déféré post-v1

| Feature                | Raison                                      |
| ---------------------- | ------------------------------------------- |
| Policy versioning      | Complexe, non bloquant pour le pilote       |
| SARIF export           | Utile selon usage GitLab SAST — à confirmer |
| Custom analyzer guide  | Docs développeur, hors périmètre pilote     |
| Multi-image comparison | Builds on `regis diff` — post-v1            |
| Tailwind v4 migration  | Bloqué upstream                             |

---

## Pré-sprint — 21 avr → 29 avr _(7j ouvrés)_

_Objectif : un livrable concret avant les congés._

| Item                                | Description                                                                                                         | Status      |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------- |
| **One-pager Regis**                 | Une page claire expliquant ce que fait Regis, pour qui, et comment — à destination des architectes et stakeholders. | Not Started |
| **Playbook "validation import" v1** | Premier playbook métier : règles + README. Go/no-go binaire pour valider une image avant import dans le catalogue.  | Not Started |

> Congés : 30 avr → 17 mai

---

## Sprint 1 — 19 mai → 2 juin

_Objectif : fondations — nettoyer, stabiliser, poser la base playbook._

| Item                        | Description                                                                                                                                               | Status      |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **Moratoire snapshots doc** | Arrêter la génération de snapshots versionnés. Purger les versions anciennes (garder 3 dernières). Désactiver `release-snapshot.yml`.                     | Not Started |
| **Playbook bundle format**  | Playbooks sous forme de répertoire : `playbook.yaml` + `README.md` + `inputs.schema.json`. Nouveau `InputsAnalyzer`.                                      | Not Started |
| **Finitions site de doc**   | Branding, CI hardening (Trivy pinning, archives résilientes), navigation sidebar, SEO baseline. Plan : `thoughts/shared/plans/PLAN-finitions-doc-site.md` | Not Started |
| **Guide GitLab CI**         | Process d'intégration regis dans un pipeline GitLab, multi-archives, déploiement rapport sur GitLab Pages / K8s.                                          | Not Started |

---

## Sprint 2 — 2 juin → 16 juin

_Objectif : enablement Harbor + playbooks._

| Item                              | Description                                                                                                                                                                     | Status      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **Intégration Harbor native**     | `RegistryProvider` abstrait, Harbor-first via OCI Distribution v2. Coexistence skopeo (opt-in `--native-registry`). Plan : `thoughts/shared/plans/PLAN-registry-integration.md` | Not Started |
| **Playbook "contrôle catalogue"** | Playbook architectes : surveillance continue + preuve de qualité pour audit.                                                                                                    | Not Started |
| **Playbook "progression projet"** | Playbook équipes projet : amélioration progressive par tiers (bronze → argent → or).                                                                                            | Not Started |

---

## Sprint 3 — 16 juin → 30 juin

_Objectif : traduction + design._

| Item                                    | Description                                                                                    | Status      |
| --------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------- |
| **Traduction française (pipeline LLM)** | CI auto-translate via OpenAI/GPT interne. Plan : `thoughts/shared/plans/PLAN-traduction-fr.md` | Not Started |
| **Design system**                       | Identité visuelle Regis générée avec Claude (couleurs, logo, typographie, custom CSS).         | Not Started |
| **Playbook creation skill**             | Skill OMC guidant la création interactive d'un playbook bundle.                                | Not Started |

---

## Sprint 4 — 30 juin → 12 juil

_Objectif : polish v1 + préparation pilote._

| Item                        | Description                                                                | Status      |
| --------------------------- | -------------------------------------------------------------------------- | ----------- |
| **UX review + corrections** | Retours des premières démos pilote — corrections ergonomie CLI et rapport. | Not Started |
| **v1.0.0-alpha release**    | Packaging, release notes, annonce pilote.                                  | Not Started |

> Congés : 13 juil → 17 juil

---

## Post-v1 / Backlog

| Item                              | Description                                                                                                                                            | Notes                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- |
| **Policy versioning**             | Versionner les playbooks indépendamment avec ranges de compatibilité.                                                                                  | Design spike requis                       |
| **SARIF export**                  | Export SARIF pour GitLab/GitHub Advanced Security.                                                                                                     | À confirmer selon usage                   |
| **Custom analyzer guide**         | Docs développeur pour créer des analyzers custom.                                                                                                      | v1.x                                      |
| **Multi-image comparison**        | Comparer la posture sécurité d'une flotte d'images.                                                                                                    | Builds on `regis diff`                    |
| **Import mise à jour de version** | Playbook allégé pour importer une nouvelle version d'une image déjà au catalogue — checklist réduite, focus sur le delta CVE/licences.                 | Après `regis diff`                        |
| **Fusion catalogue existant**     | Intégrer le catalogue d'images existant dans Regis — migration/import des images déjà référencées sous gouvernance Regis.                              | Design spike requis                       |
| **Self-scan CI**                  | `regis analyze ghcr.io/trivoallan/regis:latest` dans la CI GitHub — Regis s'analyse lui-même à chaque release. Gate bloquant ou rapport d'information. | Signal de maturité — post-v1              |
| **Tailwind v4 migration**         | Migration dashboard vers Tailwind v4.                                                                                                                  | **Bloqué** — `@headlessui/tailwindcss` v4 |
