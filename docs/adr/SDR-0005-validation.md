---
adr: SDR-0005
slug: validation
title: Validation
status: accepted
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
traits:
  validation:
    boundary: jsonschema
    data_files: json-schema
---

# Validation

> **Qu'est-ce que ce fichier ?** Un ADR — *Architecture Decision Record* — est une décision consignée : son contexte, les options pesées, ce qui a été retenu, et ce que ça coûte. **Tant qu'il porte `status: proposed`, il s'écrit et se corrige librement.**
>
> **La ligne `revision:` de l'en-tête date la question, pas le fichier.** Elle n'avance que si la question posée ici change — jamais pour une reformulation, une coquille ou un lien réparé. Vous ne la remplissez pas : elle arrive avec le fichier, et votre verdict lui reste attaché. Elle existe pour qu'on reconnaisse, plus tard, un verdict rendu contre une question qui a depuis bougé.
>
> **`rejected` est une réponse pleine, pas un abandon.** Quand la question ne se pose pas dans ce dépôt, l'ADR reçoit le verdict `rejected` avec son motif, et le bloc `traits:` disparaît en entier — une clé sans objet ne se laisse pas vide. Le motif dit alors **ce qui en tient lieu**, pour qu'un agent qui le lit sache à quoi s'en tenir. **Un ADR `rejected` sans bloc `traits:` passe la vérification** — c'est mesuré, pas supposé.

## Context and Problem Statement

**Concrètement, ce que statuer change.** Tant que ces clés sont vides, un agent qui écrit un point d'entrée — une route HTTP, une commande, un lecteur de configuration — ne sait pas **avec quoi** décrire la forme de ce qui entre. Il écrit alors une vérification à la main, différente à chaque frontière, ou il n'en écrit aucune et laisse un champ absent devenir une valeur par défaut que personne n'a voulue.

**Une frontière est un point où une donnée entre sans que le code en train de s'exécuter l'ait produite.** Corps de requête, fichier de configuration, message de file, variable d'environnement, argument de ligne de commande. Deux cas moins évidents en font aussi partie : **une ligne lue en base**, qui a pu être écrite par une version antérieure du code, et **une colonne semi-structurée** — `jsonb`, blob — même à l'intérieur d'une ligne par ailleurs validée.

**Pourquoi déclarer plutôt que vérifier à la main.** Trois raisons, dans l'ordre où elles mordent :

1. **Une vérification écrite à la main est opt-in, et sa couverture se dégrade toute seule.** Ajouter un champ ajoute un champ non validé, en silence. **L'argument vaut plein pour `boundary`**, où le modèle *est* le type : ajouter un champ au modèle le valide, il n'y a pas de geste séparé. **Il ne vaut qu'à moitié pour `data_files`** — ajouter une clé à un fichier sans l'ajouter au schéma reste possible, et le geste séparé existe bel et bien. Ce qui change là est autre chose : l'oubli **se voit**, parce que le schéma est un artefact posé à côté du fichier, et non une vérification enfouie dans une fonction.
2. **Un schéma se lit sans être exécuté.** Une vérification enfouie dans une fonction ne dit ce qu'elle accepte qu'à qui lit le code et le fait tourner. Un schéma le dit à qui l'ouvre.
3. **Un schéma est un contrat lisible par une machine.** Un agent qui doit produire une donnée conforme lit le schéma ; sans schéma, il devine depuis un exemple — et **un exemple ne dit jamais ce qui est obligatoire**, seulement ce qui était présent ce jour-là.

**Deux moments, deux garanties, et elles ne se remplacent pas.** `boundary` valide **quand le programme lit** la donnée : c'est la seule qui protège à l'exécution, y compris contre un fichier modifié après coup. `data_files` valide **statiquement**, à l'écriture : c'est la seule qui fait sortir l'erreur dans l'éditeur de qui la commet, et la seule qu'un relecteur peut exercer **sans lancer le programme** qui lit la donnée. Un validateur tourne quand même — c'est l'éditeur qui le lance pour vous, et un poste qui n'a pas l'extension ne voit rien. Un dépôt qui tient des fichiers de données a besoin des deux.

**Ce qui n'est pas concerné.** Les structures internes que votre propre code produit et consomme. Y imposer un schéma coûterait plus qu'il ne rapporte : la donnée n'a franchi aucune frontière, et le langage la vérifie déjà.

## Considered Options

* **Un schéma déclaré, validé automatiquement** — la forme est écrite une fois, et la validation en découle.
* **Une vérification écrite à la main à chaque frontière** — aucune dépendance nouvelle, et une couverture qui dépend de la discipline de chacun, frontière par frontière, champ par champ.
* **Rien** — faire confiance à ce qui entre. Tenable pour un dépôt qui n'a aucune frontière ; c'est alors `rejected` qu'il faut, pas une clé vide.

## Decision Outcome

**La réponse que la méthode propose, et ses motifs.**

| Clé | Valeur proposée | Motif |
| --- | --- | --- |
| `validation.boundary` | *dépend de votre langage* | `pydantic` en Python, `go-playground/validator` en Go. Ce sont les deux que la méthode a réellement pesés — voir ci-dessous |
| `validation.data_files` | `json-schema` | c'est le seul format que les éditeurs consomment déjà, et YAML comme TOML s'y ramènent. Un seul schéma sert le fichier, l'éditeur, la relecture et l'agent |

**L'exigence n'est pas ce qui se décide ici.** Ce qui vous revient est le **mécanisme**. Un dépôt qui ne peut appliquer aucun des mécanismes proposés — chemin critique en performance, contrainte de dépendance zéro — en nomme un autre et dit pourquoi : il déroge au moyen, jamais à l'exigence. La validation aux frontières reste due.

**Sur `validation.boundary`, la méthode n'a pas de réponse pour tous les langages, et c'est une information.** Elle a pesé Python et Go, options écartées comprises. Pour TypeScript — que `SDR-0004` recommande pourtant au même titre — **elle n'a rien décidé** : nommez l'outil que vous retenez et dites en une ligne pourquoi, votre réponse vaudra plus que la sienne.

**Voici la grille avec laquelle elle a écarté les autres**, pour que vous n'ayez pas à la deviner. Ce qui fait tomber une option, dans cet ordre : elle **décrit sans valider** à l'exécution ; elle valide **à la main**, donc par champ et par frontière, si bien qu'un champ ajouté est un champ non couvert ; elle n'expose **aucun schéma** exportable ; et, à égalité par ailleurs, son écosystème est le plus étroit. Appliquez-la à votre langage.

**Le format de la valeur** : le nom sous lequel on installe la bibliothèque — `pydantic`, `zod`, `go-playground/validator`. Sans version : elle vit dans votre fichier de dépendances, et recopiée ici elle vieillirait sans que rien ne le dise.

**`json-schema` ne contredit pas le choix de `pydantic`, et il faut le dire parce que ça en a l'air.** La méthode écarte les schémas JSON **pour typer du Python**, au motif que le schéma et les types deviendraient deux sources qui divergent. Ce motif tient quand un type décrit déjà la donnée. Un fichier de données que ne lit aucun type n'a pas de seconde source : il n'y a rien avec quoi diverger. Là où les deux coexistent — un fichier lu par un modèle — **c'est le modèle qui fait foi**, et le schéma s'en dérive ou s'aligne à la main dans la même merge request.

**Décision, et où elle s'écarte de la proposition.** `boundary: jsonschema` au lieu de `pydantic` : `regis` valide déjà ses entrées (playbooks, sorties d'analyseurs, rapport) contre des JSON Schemas publiés sous `regis/schemas/`, qui sont aussi un contrat pour les consommateurs du rapport. Introduire `pydantic` créerait la seconde source que la méthode veut éviter.

**Provenance.** Constatées : dépendance `jsonschema>=4.20` dans `pyproject.toml`, schémas sous `regis/schemas/`.

### Consequences

Un seul mécanisme : le schéma valide à l'exécution, sert l'éditeur et se publie dans `docs/reference/` (`make reference`).
Le coût : les types Python ne dérivent pas du schéma ; leur alignement se tient en revue et par les tests.

## More Information

| Clé | Ce qu'elle porte | Valeurs admises |
| --- | --- | --- |
| `validation.boundary` | ce qui décrit et valide la forme d'une donnée **quand le programme la lit** | un nom de bibliothèque, par exemple `pydantic` ou `zod` ; ou `aucun` — voir juste en dessous |
| `validation.data_files` | ce qui valide **statiquement** un fichier de données, sans exécuter le programme qui le lit | `json-schema`, un autre mécanisme nommé, ou `aucun` |

**`boundary: aucun` existe, et ne veut pas dire « nous ne validons pas ».** Il veut dire que ce dépôt **ne lit aucune donnée à l'exécution** : il tient des fichiers, et rien ne tourne pour les consommer. C'est le cas d'un dépôt de configuration, de schémas ou de textes — qui a pourtant bien besoin de `data_files`. Un dépôt qui exécute du code et choisit de ne pas valider n'écrit pas `aucun` : il n'est pas conforme, et c'est la relecture qui a à le dire.

**Le schéma se rattache au fichier, sinon il ne garde rien.** Un `validation.data_files: json-schema` qui n'est relié à aucun fichier ne produit aucune erreur dans aucun éditeur. Le rattachement se fait par `$schema` dans le fichier quand l'encodage le permet, sinon par la convention de nommage de l'outil retenu. C'est ce lien, pas le schéma, qui rend la garantie réelle.

**Le modèle vit au plus près de la frontière qu'il garde**, pas dans un module de types partagé : c'est le point d'entrée qui décide de ce qu'il accepte.

**Aucune de ces deux clés n'est contrôlée par le schéma.** Les bibliothèques de validation ne forment pas une liste fermée, et en figer une refuserait mécaniquement la dérogation que ce fichier autorise. Le schéma vérifie que vous avez répondu, jamais que la réponse est la bonne : la cohérence est tenue par la **relecture**.

**`rejected` veut dire que ce dépôt n'a aucune frontière de données**, ce qui est rare mais réel — un dépôt de documentation, de schémas, de textes. Ce n'est pas la même chose que « nous validons à la main » : ça, c'est une valeur, et elle s'écrit.

**Ce que ces clés ne couvrent pas** : ni les structures internes, exclues ci-dessus, ni le langage lui-même, qui est dans [`SDR-0004`](SDR-0004-languages.md), ni ce qui exécute la validation à chaque poussée, qui relève de [`SDR-0010`](SDR-0010-forge-and-ci.md).

**La valeur s'écrit dans ce fichier, et nulle part ailleurs.** Aucun autre fichier ne la recopie : celui qui en a besoin renvoie ici. C'est ce qui garantit qu'elle ne peut pas être contredite ailleurs.

**Une clé laissée vide n'est pas une réponse** — les deux sont exigées. Vous n'avez pas à le vérifier à l'œil. Depuis la racine de votre dépôt :

```bash
( cd docs/adr && npx @jackchuka/mdschema@0.15.1 check '*.md' )
```

**Si votre dépôt n'a ni Node ni `npm`, cette ligne ne vous sert à rien**, et le dire vaut mieux que le supposer. **Elle peut aussi échouer alors que Node est là.** Mesuré le 2026-09-20 sur macOS arm64, avec `npm` 10.9.8 puis 11.6.0 : `npx` rend `sh: mdschema: command not found`, parce que `npm` n'installe pas le lien du binaire — sur un répertoire neuf, avec `bin-links` à `true` et `ignore-scripts` à `false`. Le paquet est pourtant posé, sa dépendance de plateforme aussi, et son point d'entrée existe.

Dans les deux cas, `mdschema` est un binaire autonome : prenez-le dans les *releases* de [son dépôt](https://github.com/jackchuka/mdschema) et lancez `mdschema check '*.md'` depuis ce répertoire. **C'est le chemin sûr**, et non un repli de second choix. La ligne ci-dessus n'est qu'un raccourci, qui évite d'installer quoi que ce soit — quand il fonctionne.

Le schéma qu'elle applique est le `.mdschema.yml` de ce même répertoire, posé par la méthode. Elle nomme, fichier par fichier : une clé restée vide, une valeur hors de l'ensemble admis, un `status:` resté `proposed`, une `date:` absente, et le mode d'emploi qu'on aurait oublié de supprimer. **Elle reconnaît ce dernier à sa première phrase**, pas au tableau : le tableau a le droit de rester, et le garder ne déclenche rien. Elle ne juge pas votre décision — seulement qu'elle est prise.
