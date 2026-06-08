# Gouvernance de la mémoire — constellation Regis

- **Date** : 2026-06-08
- **Statut** : design validé (brainstorming), prêt pour plan d'implémentation
- **Portée** : `regis` (cœur) + `regis-backstage`, `regis-gitlab`, `regis-action` (sous-projets)

## Problème

Le « produit » Regis est éclaté en 4–5 dépôts (cœur + intégrations). La gestion de la
mémoire de projet souffre de quatre douleurs simultanées, toutes confirmées :

1. **Duplication / dérive** — les décisions transverses (contrat report schema,
   conventions de commit, qui consomme `spec.presentation`) sont re-notées ou
   divergent entre dépôts.
2. **Encombrement des dépôts** — les plans d'exécution superpowers (20–80 Ko)
   restent versionnés après livraison et polluent repo + historique.
3. **Onboarding agent/humain** — un nouvel arrivant ne sait pas où chercher : deux
   systèmes de mémoire coexistent dans le cœur, deux répertoires de plans, rien de
   transverse.
4. **Contexte agent trop lourd** — charger memory-bank + superpowers à chaque session
   sature le contexte avec de l'échafaudage périmé (plans de features déjà livrées).

### État des lieux constaté

- **`regis` (cœur)** porte DEUX systèmes qui se chevauchent :
  - `docs/memory-bank/` — protocole « Memory Bank » (RULES.md immuable + ~20 fichiers)
    **+** `docs/memory-bank/plans/` (12 fichiers, mélange plans _et_ designs).
  - `docs/superpowers/` — `specs/` (10 designs) **+** `plans/` (15 plans).
  - Incohérence figée : `CLAUDE.md` affirme « Plans live in
    `docs/memory-bank/plans/` » alors que la skill superpowers écrit dans
    `docs/superpowers/plans/`.
- **Sous-projets** : `regis-backstage` et `regis-gitlab` n'ont que `docs/superpowers/`
  et un `CLAUDE.md` (conventions partiellement copiées-collées) — pas de memory-bank.
  `regis-action` est absent du disque ; `regis-dashboard` est abandonné.
- **Hébergement** : `regis` et `regis-backstage` sur GitHub ; `regis-gitlab` est
  **dual-host** (origin gitlab.com, miroir public github.com). Pas de monorepo.
- **Mémoire commune _de fait_** : la mémoire auto Claude de l'utilisateur porte déjà
  le savoir transverse (extraction GitLab, généralisation `spec.presentation`, abandon
  dashboard) — mais elle est privée à l'utilisateur, hors des dépôts.

## Principe directeur : une taxonomie à deux axes

Le désordre vient de l'absence de grille. On range tout artefact de mémoire selon
deux questions :

|                                | **Durable** (vérité de référence)                                          | **Éphémère** (échafaudage de travail)               |
| ------------------------------ | -------------------------------------------------------------------------- | --------------------------------------------------- |
| **Local** (à un repo)          | memory-bank du repo (systemPatterns, decisionLog, techContext) + **specs** | **plans d'exécution** → supprimés au merge          |
| **Constellation** (transverse) | **zone constellation** dans le cœur : contrat + conventions + glossaire    | **état programme** cross-repo → mémoire auto Claude |

Règle mentale, en une phrase :

> _« Est-ce vrai pour toute la constellation ? → cœur. Est-ce que ça survit à la
> PR ? → memory-bank/spec, sinon plan jetable. »_

Correspondance douleurs → grille :

- Duplication/dérive → colonne **Durable/Constellation** (source unique).
- Encombrement + contexte lourd → colonne **Éphémère** (les plans ne survivent pas au merge).
- Onboarding → la grille elle-même : on sait _où chaque chose vit_.

## Décisions de design

### D1 — Mécanisme de distribution : le cœur `regis` est la source de vérité

Pas de nouveau dépôt (`regis-memory` écarté par YAGNI), pas de submodule (douleur
pour zéro bénéfice : on veut lire la cible _à jour_, pas une version pinnée). Le
savoir transverse durable vit dans le cœur, dont les sous-projets dépendent déjà
fonctionnellement. Les sous-projets y renvoient par un **lien HTTP absolu vers
GitHub**, qui fonctionne depuis n'importe quel clone (y compris le clone gitlab.com
de `regis-gitlab`).

### D2 — La zone constellation : `regis/docs/memory-bank/constellation/`

Un sous-dossier dédié trace nettement la frontière « interne regis » vs « transverse ».
Trois fichiers durables :

- **`contract.md`** — _le normatif inter-repos._ `REPORT_SCHEMA_VERSION` courant +
  politique de bump, schéma `spec.presentation`, entry-points `regis.analyzers`,
  contrat de compatibilité. **À lire avant toute modification touchant la
  sérialisation/consommation d'un report.**
- **`conventions.md`** — _la partie partageable des CLAUDE.md._ Commit scopes,
  workflow de branches (rebase, jamais merge-back), stack de skills, style guides.
  Défini une fois ici ; les CLAUDE.md locaux ne gardent que le spécifique au repo.
- **`glossary.md`** — _le modèle mental._ criterion vs rule, playbook, analyzer,
  presentation, report ; + un C4 contexte d'ensemble (Mermaid) cœur ↔ intégrations.

### D3 — L'état programme vivant reste dans la mémoire auto Claude

L'avancement des migrations transverses (ex : généralisation presentation = #2 gitlab,
#3 backstage, #4 action) **ne va pas** dans un fichier versionné. Il vit dans la
mémoire auto Claude — là où il change vite, sans cérémonie de PR. Un `program.md`
versionné serait périmé en permanence et générerait des PR de pur statut. **Pas de
`program.md`** (YAGNI ; réévaluable si un statut visible aux humains devient un besoin).

### D4 — Cycle de vie : deux lieux à rôle unique

On passe de trois lieux qui se chevauchent à deux :

- **`docs/superpowers/specs/`** — _durable, local._ Le « quoi/pourquoi ». Conservé
  (convention de la skill brainstorming).
- **`docs/superpowers/plans/`** — _éphémère, local._ Le « comment » d'exécution TDD.
  **Supprimé au merge.** Vit sur la branche (exécution multi-session), retiré dans la
  PR qui livre. Avec le squash-merge du projet, `main` ne le porte jamais ; la trace
  reste consultable sur la PR.
- **`docs/memory-bank/plans/` disparaît.**

### D5 — Plan jetable ≠ note de recherche durable

Distinction à inscrire noir sur blanc : un _plan d'exécution_ est jetable ; une _note
de recherche_ (un probe, un benchmark, un « pourquoi on a écarté X ») est durable.
Avant toute suppression, les notes de recherche (ex : `regctl-probe-notes`,
`grype-probe-notes`) sont **promues** vers `decisionLog.md` ou un spec. **Ne jamais
supprimer une conclusion sous prétexte qu'elle vivait dans un fichier de plan.**

### D6 — Branchement des sous-projets

Aucun sous-projet ne duplique la zone constellation. Chaque `CLAUDE.md` gagne un bloc :

```markdown
## Mémoire transverse (constellation Regis)

Le contrat inter-repos, les conventions de travail et le glossaire vivent dans le cœur :
https://github.com/trivoallan/regis/tree/main/docs/memory-bank/constellation/
Lis `contract.md` AVANT toute modification touchant la sérialisation/consommation d'un report.
Ce CLAUDE.md ne contient que le spécifique à CE repo.
```

On retire des CLAUDE.md sous-projets les conventions désormais centralisées (commit
scopes, workflow branches, skill stack) pour ne pas re-créer la dérive. Le
`regis/CLAUDE.md` _pointe_ vers `constellation/conventions.md` plutôt que de le
dupliquer dans son corps.

## Plan de migration (exécuté dans le plan d'implémentation)

1. Créer `docs/memory-bank/constellation/{contract,conventions,glossary}.md` dans le
   cœur, peuplés depuis les sources existantes (schemas, systemPatterns, CLAUDE.md).
2. Trier `docs/memory-bank/plans/` : designs → `specs/`, notes de probe →
   `decisionLog.md`, plans déjà mergés → suppression.
3. Mettre à jour `regis/CLAUDE.md` : corriger l'emplacement des plans, inscrire la
   règle « supprimés au merge », pointer vers `constellation/`.
4. Ajouter le bloc « Mémoire transverse » aux CLAUDE.md de `regis-backstage` et
   `regis-gitlab` (et `regis-action` à sa création) ; en retirer les conventions
   centralisées.
5. Documenter la taxonomie dans `systemPatterns.md` (PAS dans `RULES.md`, immuable).

## Non-objectifs (YAGNI)

- Pas de dépôt `regis-memory` dédié.
- Pas de submodule git cross-repo.
- Pas de `program.md` versionné pour l'état programme.
- Pas de memory-bank complet dans les sous-projets (ils ont specs/ + plans/ + pointeur).
- Pas de modification de `RULES.md`.

## Critères de succès

- Une décision transverse n'existe qu'à **un seul endroit** (zone constellation).
- `main` de chaque repo ne porte **aucun** plan d'exécution de feature livrée.
- Un agent en début de session sait, via la taxonomie, où lire et où écrire **sans
  ambiguïté** ; `CLAUDE.md` et la réalité des répertoires concordent.
- Un contributeur humain de n'importe quel sous-projet atteint contrat + conventions +
  glossaire en **un clic**.
