---
adr: SDR-0011
slug: delivery
title: Delivery
status: accepted
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
traits:
  hosting:
    offer: caas
  delivery:
    environments:
      - name: ghcr.io
        trigger: tag
    release_tool: release-please
    registry: ghcr.io
---

# Delivery

> **Qu'est-ce que ce fichier ?** Un ADR — *Architecture Decision Record* — est une décision consignée : son contexte, les options pesées, ce qui a été retenu, et ce que ça coûte. **Tant qu'il porte `status: proposed`, il s'écrit et se corrige librement.**
>
> **La ligne `revision:` de l'en-tête date la question, pas le fichier.** Elle n'avance que si la question posée ici change — jamais pour une reformulation, une coquille ou un lien réparé. Vous ne la remplissez pas : elle arrive avec le fichier, et votre verdict lui reste attaché. Elle existe pour qu'on reconnaisse, plus tard, un verdict rendu contre une question qui a depuis bougé.
>
> **`rejected` est une réponse pleine, pas un abandon.** Quand la question ne se pose pas dans ce dépôt, l'ADR reçoit le verdict `rejected` avec son motif, et le bloc `traits:` disparaît en entier — une clé sans objet ne se laisse pas vide. Le motif dit alors **ce qui en tient lieu**, pour qu'un agent qui le lit sache à quoi s'en tenir. **Un ADR `rejected` sans bloc `traits:` passe la vérification** — c'est mesuré, pas supposé.

## Context and Problem Statement

**Concrètement, ce que statuer change.** Tant que ces clés sont vides, un agent qui termine un change ne sait pas si le fusionner **le met devant des utilisateurs** ou seulement dans `main`, ni ce qui **fabrique une version**. Il fusionne donc sans savoir ce qu'il déclenche — et c'est la seule des questions de l'adoption dont se tromper a des conséquences pour quelqu'un d'autre que l'équipe. Une fois ces trois valeurs écrites, il sait ce que sa fusion fait.

**Livrer et déployer ne sont pas le même geste**, et les deux clés le disent : `delivery.release_tool` fabrique une version nommée et son journal, le déclencheur de chaque environnement la met en service. Un dépôt peut faire l'un sans l'autre.

## Considered Options

**Ces options ne pèsent que le déclencheur d'un environnement**, la seule part de ces clés qui ait un ensemble fermé. Le reste se lit dans `## More Information`.

**Elles se pèsent environnement par environnement**, pas une fois pour le dépôt : la même équipe veut souvent `merge` sur son intégration et `tag` sur sa production.

* **Déployer sur tag** — ce qui tourne porte un nom. Un geste de plus après la fusion, et un retour arrière qui a une cible.
* **Déployer sur fusion** — la fusion suffit, le délai est minimal. « Ce qui tourne » devient un SHA que personne n'a en tête, et le retour arrière n'a plus de cible évidente.
* **Déployer à la main** — quelqu'un décide et lance. Honnête pour un dépôt qui livre rarement ; le coût est que le geste n'est écrit nulle part.

## Decision Outcome

**La réponse que la méthode propose, et ses motifs.**

| Clé | Valeur proposée | Motif |
| --- | --- | --- |
| `hosting.offer` | `caas` | un cluster Kubernetes est l'offre la plus courante. **C'est le seul trait de ce fichier qui décide de ce que l'agent écrit** — voir ci-dessous |
| `delivery.environments` | `staging` sur `merge`, `production` sur `tag` | **la question se pose, elle ne se devine pas** : la méthode ne sait pas ce que vous servez, mais elle sait quelle paire marche presque toujours — voir ci-dessous |
| `delivery.release_tool` | `releaser-pleaser` | c'est le seul outil de sa famille qui **couvre les deux forges**. La réponse ne dépend donc pas de `forge.vendor` — voir ci-dessous |
| `delivery.registry` | **une adresse** — c'est une forme, pas une valeur | la méthode ne peut pas proposer votre registre. Elle dit seulement qu'il en faut un dès que vous recevez un cluster — voir ci-dessous |
| `deployment.manifests` | **une URL** — c'est une forme, pas une valeur | même chose : votre adresse ne se devine pas. La forme, si — et c'est cette forme qui décide si votre chaîne porte un job de déploiement. Voir ci-dessous |

**Deux de ces lignes proposent une forme et non une valeur, et c'est délibéré.** Quand un trait porte une **adresse**, la méthode ne peut pas la proposer : elle est propre à votre dépôt. Laisser la case vide se lirait comme un oubli ; elle porte donc ce que la méthode sait dire — la forme qu'elle recommande, et le constat daté qui la fonde.

**`hosting.offer` commande le livrable, et pas seulement son étiquette.** Deux valeurs, et rien d'autre :

* **`caas`** — vous recevez un cluster. Des manifestes Kubernetes décrivent votre déploiement, et la chaîne pousse une image dans un registre. **Ce trait ne dit ni où vivent ces manifestes, ni qui les applique** : `deployment.manifests` le dit, et c'est lui qui décide si votre agent en écrit dans ce dépôt — voir plus bas.
* **`paas`** — vous recevez une plateforme. L'agent **n'écrit aucun manifeste** : il déclare un service, et la plateforme fabrique le reste.

**La variante ne se déclare pas ici.** Que votre `caas` soit un cluster AWS, AKS ou sur site, **écrivez-le en prose dans un ADR local**, pas dans ce trait. Tant qu'aucune règle de la méthode ne diffère d'une variante à l'autre, en faire une clé produirait une valeur que personne n'applique — et une clé que rien ne vérifie est une étiquette, pas une décision. Le jour où une règle en dépendra, elle deviendra un trait, et cet ADR sera rouvert.

**Un déclencheur unique ne décrit pas ce que font les équipes.** C'est pourquoi il vit désormais **dans** chaque environnement plutôt qu'à côté d'eux.

La paire proposée : **`staging` part à la fusion sur `main`**, parce qu'un environnement d'intégration doit refléter ce que la branche porte, sans geste supplémentaire — et **`production` part sur un tag**, parce qu'une version en service est une version **nommée** : on sait ce qui tourne, on peut le dire à quelqu'un, et un retour arrière a une cible.

**La liste, elle, se demande.** La méthode ne connaît pas vos environnements : un dépôt peut n'en servir aucun, un autre en servir quatre. **Écrivez-les dans l'ordre où une version les traverse** — c'est cet ordre qui dit ce qu'un déploiement en production a déjà franchi.

**Aucun environnement est une réponse pleine.** Une bibliothèque ne déploie pas : elle publie. `environments: []` le dit, et `delivery.release_tool` porte alors tout le sujet.

**Sur `delivery.release_tool`, la réponse ne dépend pas de la forge**, et vous n'avez pas besoin d'avoir statué [`SDR-0010`](SDR-0010-forge-and-ci.md) pour répondre ici.

Les deux outils de cette famille font la même chose : ils lisent les messages de commit, ouvrent une demande de fusion de release portant le journal des changements et la version calculée, puis posent le tag à la fusion. **Ce qui les distingue est leur couverture, pas leur intérêt.**

[`releaser-pleaser`](https://github.com/apricote/releaser-pleaser) **couvre les deux forges** — c'est sa raison d'être, et c'est ce qui en fait une réponse unique possible.

[`release-please`](https://github.com/googleapis/release-please) ne couvre que GitHub : il est profondément lié à l'API de cette forge, et son support GitLab reste une demande ouverte. Il ne peut donc pas être la réponse unique, là où l'autre le peut.

**Ce que la méthode propose n'est pas ce qu'elle admet.** L'ensemble de `delivery.release_tool` reste ouvert, et un dépôt qui fabrique déjà ses versions avec un autre outil de cette famille — `release-please` sur GitHub, typiquement — **n'a aucune raison d'en changer**. La proposition dit où va la méthode ; elle n'ordonne pas la migration d'une chaîne qui marche.

**SemVer n'est pas ici, et ce n'est pas un oubli.** La numérotation découle mécaniquement des types de commit — `feat` donne une mineure, `fix` et `perf` une corrective, une rupture une majeure. C'est une **norme de la méthode**, pas une question ouverte : il n'y a pas de clé pour elle parce qu'il n'y a rien à décider. Choisir `calver` serait une déviation, à écrire dans un ADR à vous.

**La vérification ne s'arrête pas à un refus.** Dès que ce fichier est `accepted` et qu'un fichier de chaîne existe — `.gitlab-ci.yml` sur GitLab, un workflow sous `.github/workflows/` sur GitHub —, la dernière tâche d'un plan vérifie que la chaîne passe sur la merge request — la pull request, sur GitHub —, même sans job de déploiement visible, et même après un « pas maintenant ».

**Pour refuser sans statuer, répondez « pas maintenant ».** L'agent écrit alors, dans le `tasks.md` du change qui se termine, une ligne datée, en début de ligne :

```text
Proposition refusée : pipeline (AAAA-MM-JJ)
```

La vraie ligne porte une date en chiffres ; le modèle ci-dessus n'en est pas une. Tant qu'elle est la plus récente, l'agent se tait. Pour qu'il propose de nouveau, écrivez, en début de ligne, `Proposition rouverte : pipeline (AAAA-MM-JJ)` dans un change en cours. Pour ne jamais déployer par une chaîne, statuez `rejected`.

**Rien de tout cela ne s'écrit dans ce fichier.** Une version antérieure de ce texte faisait écrire ici une ligne « Mise en place de la chaîne proposée le … » : si vous la trouvez, elle ne compte plus, et vous pouvez la supprimer.

**Sur `deployment.manifests`, la forme de votre réponse décide de votre chaîne.** Trois réponses possibles, et deux d'entre elles sont des adresses.

| Ce que vous écrivez | Ce que ça veut dire |
| --- | --- |
| un **chemin relatif** à la racine de votre dépôt, `deploy/` par exemple | les manifestes vivent **ici**, votre chaîne **les applique elle-même**, et elle porte **un job de déploiement par environnement** déclaré plus haut |
| une **URL** | les manifestes vivent **ailleurs**. Votre chaîne **propose un changement à cette adresse** et **ne porte aucun job de déploiement** : un agent extérieur réconcilie l'état, et c'est la fusion de votre demande là-bas qui met en service |
| `aucun` | rien ne se déploie. Cohérent avec `environments: []`, qu'une bibliothèque écrit déjà |

**Il n'y a pas de clé qui déclare le modèle, et c'est voulu.** La forme de l'adresse le dit déjà, et [`SDR-0010`](SDR-0010-forge-and-ci.md) applique la même règle à son outil de chaîne : une clé qu'un agent peut calculer est une clé qu'on vous fait remplir pour rien.

**Écrivez l'URL avec son schéma** — `https://`, `ssh://`, ou la forme `git@hôte:chemin`. C'est ce qui rend la lecture sûre : sans schéma, `forge.exemple.test/groupe/depot` est un chemin relatif parfaitement valide, et rien ne distingue plus les deux réponses.

**Deux situations font que l'agent s'arrête et vous demande, au lieu d'écrire un job.** La première : une valeur qui n'est ni l'une ni l'autre — un chemin absolu, par exemple. La seconde, et c'est elle qui rattrape le schéma oublié : **un chemin relatif qui ne désigne aucun répertoire de votre dépôt**. Dans les deux cas il n'écrit rien. Une lecture qui devine écrit le mauvais job, et un mauvais job de déploiement se constate en production.

**Une combinaison n'est pas portée par cette clé, et il faut le savoir** : garder la source de vos manifestes **ici** tout en poussant leur rendu **ailleurs**. Une adresse ne dit pas les deux. Si c'est votre cas, écrivez-le en prose dans un ADR local, comme toute dérogation.

**Sous une URL, ce que `trigger` décrit change.** Il dit ce qui déclenche **la proposition** — le tag, la fusion, ou votre geste. Ce qui déclenche le **déploiement** est la fusion de votre demande dans l'autre dépôt, et ce fichier ne gouverne pas ce dépôt-là. L'ensemble de `trigger` reste fermé à `tag`, `merge` et `manuel` : lui ajouter une quatrième valeur pour ce cas produirait une valeur que rien ne vérifie.

**Sur `delivery.registry`, l'adresse du registre où votre chaîne dépose son image**, ou `aucun` sous une offre qui ne vous donne pas de cluster — la plateforme fabrique alors elle-même, et il n'y a pas de job d'image.

**Elle vit sous `delivery.` et non sous `deployment.`, pour deux raisons.** Déposer une image **fabrique un artefact** : ça ne met rien en service, et ce fichier écrit plus haut que livrer et déployer ne sont pas le même geste. Et cette adresse **ne change pas avec la forme de `deployment.manifests`** : que votre chaîne applique ou qu'elle propose ailleurs, elle pousse la même image au même endroit.

**Un registre nommé par ce trait ne devient pas pour autant un environnement.** `delivery.environments` ordonne ce qui est **en service**, et un registre d'images ne l'est pour personne : votre cluster y tire, vos usagers n'y vont pas. Un dépôt qui **publie un paquet** est l'autre cas, et celui-là répond bien par un environnement — c'est écrit plus bas.

**Pourquoi `hosting.offer` reste dû alors que le modèle, lui, se dérive.** Parce qu'il ne se dérive pas : `deployment.manifests: aucun` ne distingue pas une offre qui ne vous donne pas de cluster d'un dépôt qui ne déploie rien du tout. La question reste donc posée.

**Ce que le schéma attrape sur ces deux clés, et ce qu'il n'attrape pas.** Il **nomme une clé restée vide** — c'est son office, et c'est l'oubli le plus probable. Il **ne distingue pas** un chemin d'une URL, et ne vous dira donc jamais qu'une forme a été écrite là où l'autre était voulue. Ce qui reste est la relecture de votre demande de fusion, plus l'arrêt de l'agent décrit ci-dessus.

**Ce que ce fichier décide depuis le retrait de l'ADR du déploiement.** Il décidait **quand et où** l'on déploie — les environnements et leur déclencheur. Il décide désormais aussi **sur quoi**, par `hosting.offer`. Les règles de la chaîne elle-même, elles, vivent dans [`SDR-0010`](SDR-0010-forge-and-ci.md) avec la forge dont elles dépendent.

**Décision, et où elle s'écarte de la proposition.** `regis` publie un paquet et une image ; il ne se déploie pas. `hosting.offer: caas` est retenu parce que c'est la valeur sous laquelle la méthode rend dû le job `image` (`SDR-0010`), et que `regis` en porte un. Aucun cluster ne reçoit pourtant `regis` : la valeur décrit son livrable, une image, pas un hébergement. `deployment.manifests` est retiré, rien n'étant déployé. Son seul environnement est le registre où il publie, sur tag. `release-please` au lieu de `releaser-pleaser` : la chaîne existe et marche sur GitHub, et la méthode dit elle-même qu'elle n'ordonne pas sa migration.

**Provenance.** `release_tool` et `registry` sont constatées : `.github/workflows/release.yml` (Release Please, puis push de l'image `ghcr.io/${GITHUB_REPOSITORY}`). `environments` et le retrait de `deployment.manifests` sont répondus le 2026-10-17 (onboarding, cadrage passe 2) ; `hosting.offer: caas` est répondu le même jour, pendant l'application du change.

### Consequences

Une version est nommée par construction : le tag posé par Release Please déclenche la publication.
Le coût : aucun environnement de pré-production ; une image défectueuse se corrige par une nouvelle version, pas par un retour arrière.

## More Information

| Clé | Ce qu'elle porte | Valeurs admises |
| --- | --- | --- |
| `hosting.offer` | l'offre d'hébergement de ce dépôt, qui décide si l'agent écrit des manifestes | `caas` — vous recevez un cluster, l'agent écrit des manifestes Kubernetes ; `paas` — vous recevez une plateforme, il n'en écrit aucun. **Rien d'autre** : la variante s'écrit en prose dans un ADR local |
| `delivery.environments` | ce que ce dépôt sert, dans l'ordre où une version les traverse, **chacun avec son déclencheur** | une liste de paires — voir l'exemple ci-dessus. Déclencheurs admis : `tag`, `merge`, `manuel` |
| `delivery.release_tool` | ce qui fabrique une version et son journal des changements | `release-please`, `releaser-pleaser`, un autre outil, `manuel`, ou `aucun` |
| `delivery.registry` | l'adresse du registre où la chaîne dépose son image | une adresse, ou `aucun` — sous une offre qui ne donne pas de cluster, il n'y a pas de job d'image |
| `deployment.manifests` | où vivent les manifestes de déploiement, **et donc si votre chaîne déploie elle-même** | un **chemin relatif** à la racine du dépôt — la chaîne applique ; une **URL avec son schéma** — la chaîne propose un changement là-bas et ne déploie pas ; ou `aucun` |

**`manuel` et `aucun` ne disent pas la même chose.** `manuel` veut dire qu'une version est bien fabriquée, mais à la main : quelqu'un décide du numéro, écrit le journal, pose le tag. `aucun` veut dire qu'**il n'y a pas de version du tout** — rien n'est numéroté, rien n'est tagué. Un dépôt qui publie un paquet répond `manuel`, jamais `aucun`, même s'il tape lui-même la commande de publication.

**Un outil qui ne fait que la moitié compte quand même.** `delivery.release_tool` nomme ce qui fabrique la version ; si votre outil la publie sans écrire le journal des changements, écrivez-le tout de même et dites en une ligne, sous **Consequences**, que le journal se tient à la main.

**Un dépôt qui publie un paquet plutôt qu'il ne sert un service répond quand même.** Son environnement est le registre où il publie — `[npm]`, `[pypi]`, une instance interne — et `tag` y est la norme, une version publiée étant une version nommée par construction.

**`rejected` ici veut dire que rien ne sort de ce dépôt** : ni service, ni paquet, ni image. Ça arrive — un dépôt de documentation, de schémas, de configuration relue à la main. Ce n'est pas la même chose que déployer à la main, qui se répond `manuel`.

**Deux de ces clés ont un ensemble fermé, et le schéma n'en contrôle qu'une.** `hosting.offer` est vérifiée : une valeur hors de `caas` et `paas` est nommée. Le `trigger` d'un environnement a lui aussi un ensemble fermé — `tag`, `merge`, `manuel` —, mais **le schéma ne voit pas l'intérieur de la liste** : mesuré le 2026-09-20 avec `mdschema` 0.15.1, un `trigger: release` rend `✓ No violations found`. Il se relit donc à l'œil, dans votre demande de fusion. **Une version antérieure de ce fichier écrivait que le `trigger` était la seule part contrôlée de ces clés** : c'était faux deux fois, et cette phrase la remplace. Le reste est libre — un registre, un nom d'outil, un nom d'environnement ne se laissent pas énumérer d'avance. Le schéma vérifie que vous avez répondu, jamais que la réponse est la bonne.

**Ce que ces clés ne couvrent pas** : ni le format des messages dont la version se déduit, qui est dans [`SDR-0006`](SDR-0006-commits.md), ni ce qui s'exécute avant le déploiement, qui est dans [`SDR-0010`](SDR-0010-forge-and-ci.md).

**La valeur s'écrit dans ce fichier, et nulle part ailleurs.** Aucun autre fichier ne la recopie : celui qui en a besoin renvoie ici. C'est ce qui garantit qu'elle ne peut pas être contredite ailleurs.

**Une clé laissée vide n'est pas une réponse** — les trois sont exigées. Vous n'avez pas à le vérifier à l'œil. Depuis la racine de votre dépôt :

```bash
( cd docs/adr && npx @jackchuka/mdschema@0.15.1 check '*.md' )
```

**Si votre dépôt n'a ni Node ni `npm`, cette ligne ne vous sert à rien**, et le dire vaut mieux que le supposer. **Elle peut aussi échouer alors que Node est là.** Mesuré le 2026-09-20 sur macOS arm64, avec `npm` 10.9.8 puis 11.6.0 : `npx` rend `sh: mdschema: command not found`, parce que `npm` n'installe pas le lien du binaire — sur un répertoire neuf, avec `bin-links` à `true` et `ignore-scripts` à `false`. Le paquet est pourtant posé, sa dépendance de plateforme aussi, et son point d'entrée existe.

Dans les deux cas, `mdschema` est un binaire autonome : prenez-le dans les *releases* de [son dépôt](https://github.com/jackchuka/mdschema) et lancez `mdschema check '*.md'` depuis ce répertoire. **C'est le chemin sûr**, et non un repli de second choix. La ligne ci-dessus n'est qu'un raccourci, qui évite d'installer quoi que ce soit — quand il fonctionne.

Le schéma qu'elle applique est le `.mdschema.yml` de ce même répertoire, posé par la méthode. Elle nomme, fichier par fichier : une clé restée vide, une valeur hors de l'ensemble admis, un `status:` resté `proposed`, une `date:` absente, et le mode d'emploi qu'on aurait oublié de supprimer. **Elle reconnaît ce dernier à sa première phrase**, pas au tableau : le tableau a le droit de rester, et le garder ne déclenche rien. Elle ne juge pas votre décision — seulement qu'elle est prise.
