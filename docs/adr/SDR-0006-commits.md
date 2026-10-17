---
adr: SDR-0006
slug: commits
title: Commits
status: accepted
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
traits:
  commits:
    scopes: [cli, playbook, schema, registry, analyzer, analyzer/cve, analyzer/secrets, analyzer/sbom, analyzer/hadolint, analyzer/dockle, analyzer/skopeo, analyzer/freshness, analyzer/size, analyzer/popularity, analyzer/endoflife, analyzer/scorecarddev, analyzer/provenance, report, templates, ci, deps, docs]
    tool: aucun
---

# Commits

> **Qu'est-ce que ce fichier ?** Un ADR — *Architecture Decision Record* — est une décision consignée : son contexte, les options pesées, ce qui a été retenu, et ce que ça coûte. **Tant qu'il porte `status: proposed`, il s'écrit et se corrige librement.**
>
> **La ligne `revision:` de l'en-tête date la question, pas le fichier.** Elle n'avance que si la question posée ici change — jamais pour une reformulation, une coquille ou un lien réparé. Vous ne la remplissez pas : elle arrive avec le fichier, et votre verdict lui reste attaché. Elle existe pour qu'on reconnaisse, plus tard, un verdict rendu contre une question qui a depuis bougé.
>
> **`rejected` est une réponse pleine, pas un abandon.** Quand la question ne se pose pas dans ce dépôt, l'ADR reçoit le verdict `rejected` avec son motif, et le bloc `traits:` disparaît en entier — une clé sans objet ne se laisse pas vide. Le motif dit alors **ce qui en tient lieu**, pour qu'un agent qui le lit sache à quoi s'en tenir. **Un ADR `rejected` sans bloc `traits:` passe la vérification** — c'est mesuré, pas supposé.

## Context and Problem Statement

**Concrètement, ce que statuer change.** Tant que ces clés sont vides, un agent qui rédige un message de commit **invente une portée** — `fix(api)`, puis `fix(backend)`, puis `fix(server)` pour le même endroit. L'historique devient illisible par filtre, et une release engendrée depuis les messages range mal. Une fois la liste écrite, il choisit dedans.

**Le format, lui, ne se décide pas ici.** La méthode impose [Conventional Commits](https://www.conventionalcommits.org/) et ses onze types ; ce qui vous revient est le **vocabulaire des portées** de ce dépôt, et **l'outil** qui le tient — ou son absence.

**Ce que `rejected` veut dire dans cet ADR**, du coup : que vous ne nommez ni portées ni outil — pas que vous refusez le format, qui ne dépend pas de vous. Un dépôt d'une seule zone sans pipeline est le cas type.

## Considered Options

* **Une liste fermée de portées** — un mot par zone du dépôt, décidé une fois.
* **Aucune portée** — `feat:` sans parenthèse. Réponse tenable pour un dépôt à une seule zone ; écrivez `[]`, pas rien.
* **`commitlint`** — la référence, branchée en CI : elle refuse la merge request, donc elle protège aussi ce qui arrive par la forge.
* **`hook`** — un contrôle local, avant le commit. Il vous prévient plus tôt, mais il ne voit pas ce qui est poussé depuis une machine qui ne l'a pas.
* **Aucun outil** — la relecture tient la convention, comme chez la méthode.

## Decision Outcome

**Ce que la méthode fixe, et qui n'est pas négociable :** le format [Conventional Commits](https://www.conventionalcommits.org/), ses **onze types** — `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert` — et la syntaxe de rupture. C'est la seule chose qui rende un historique comparable d'un dépôt à l'autre.

**La réponse que la méthode propose sur l'outil, et ses motifs.**

| Clé | Valeur proposée | Motif |
| --- | --- | --- |
| `commits.tool` | `commitlint` | **si ce dépôt engendre ses versions depuis les messages** — un message hors format produit alors une version fausse, que la relecture n'attrape pas de façon fiable |

**Vérifiez d'abord ce présupposé** : si vos versions se posent à la main, la recommandation tombe et `aucun` est une réponse aussi bonne. C'est le pivot du motif, et il ne vaut que pour les dépôts qu'il décrit.

**La méthode répond `aucun` pour elle-même**, et ce n'est pas une contradiction : elle n'a pas de pipeline et n'engendre pas de version. Un dépôt applicatif en a une. La réponse dépend donc de ce que vous faites, pas de ce qu'elle fait.

**Sur `commits.scopes`, la méthode n'a pas de réponse à proposer**, et c'est une information : les portées nomment **vos** zones, et elle ne les connaît pas. Une liste par défaut serait un aveu déguisé en recommandation. Écrivez un mot par zone que vous voulez pouvoir filtrer, et pas un de plus. **`[]` reste une réponse pleine** : un dépôt d'une seule zone n'a rien à nommer, et une liste inventée à l'adoption vieillit plus mal qu'une liste absente.

**Décision, et où elle s'écarte de la proposition.** `tool: aucun` : aucun commitlint ni hook. La convention est tenue par le workflow `pr-title.yml` (check requis `pr-title`) sur le titre de la pull request, qui devient le message du commit squashé (`squash_merge_commit_title: PR_TITLE`). Les commits intermédiaires d'une branche ne sont pas contrôlés, puisqu'ils disparaissent au squash.

**Provenance.** `scopes` est constatée : la liste de `.agent/rules/commitmessages.md`, source unique des scopes. `tool` est répondue le 2026-10-17 (onboarding, cadrage passe 2), sur le constat de `.github/workflows/pr-title.yml` et `.github/settings.json`.

### Consequences

Seul le message qui arrive sur `main` est contrôlé, ce qui suffit à Release Please.
Le coût : la liste des scopes vit à deux endroits (ici et `.agent/rules/commitmessages.md`) ; le second reste la source, et un scope ajouté là doit l'être ici dans la même pull request.

## More Information

| Clé | Ce qu'elle porte | Valeurs admises |
| --- | --- | --- |
| `commits.scopes` | les portées admises dans ce dépôt | une liste de mots, ou `[]` |
| `commits.tool` | ce qui tient la convention, et **où** | `commitlint` en CI, `hook` en local, ou `aucun` |

**Ce que ces clés ne couvrent pas** : ni les onze types, ni la syntaxe de rupture — ils viennent de la méthode et ne se déclarent pas ici. La liste opposable des types vit dans le corpus, pas dans ce fichier.

**La valeur s'écrit dans ce fichier, et nulle part ailleurs.** Aucun autre fichier ne la recopie : celui qui en a besoin renvoie ici. C'est ce qui garantit qu'elle ne peut pas être contredite ailleurs.

**Une clé laissée vide n'est pas une réponse** — les deux sont exigées. `[]` et `aucun` en sont, le vide non.

```bash
( cd docs/adr && npx @jackchuka/mdschema@0.15.1 check '*.md' )
```

**Si votre dépôt n'a ni Node ni `npm`, cette ligne ne vous sert à rien**, et le dire vaut mieux que le supposer. **Elle peut aussi échouer alors que Node est là.** Mesuré le 2026-09-20 sur macOS arm64, avec `npm` 10.9.8 puis 11.6.0 : `npx` rend `sh: mdschema: command not found`, parce que `npm` n'installe pas le lien du binaire — sur un répertoire neuf, avec `bin-links` à `true` et `ignore-scripts` à `false`. Le paquet est pourtant posé, sa dépendance de plateforme aussi, et son point d'entrée existe.

Dans les deux cas, `mdschema` est un binaire autonome : prenez-le dans les *releases* de [son dépôt](https://github.com/jackchuka/mdschema) et lancez `mdschema check '*.md'` depuis ce répertoire. **C'est le chemin sûr**, et non un repli de second choix. La ligne ci-dessus n'est qu'un raccourci, qui évite d'installer quoi que ce soit — quand il fonctionne.

Le schéma qu'elle applique est le `.mdschema.yml` de ce même répertoire, posé par la méthode. Elle nomme, fichier par fichier : une clé restée vide, une valeur hors de l'ensemble admis, un `status:` resté `proposed`, une `date:` absente, et le mode d'emploi qu'on aurait oublié de supprimer. **Elle reconnaît ce dernier à sa première phrase**, pas au tableau : le tableau a le droit de rester, et le garder ne déclenche rien. Elle ne juge pas votre décision — seulement qu'elle est prise.
