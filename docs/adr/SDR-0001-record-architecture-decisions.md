---
adr: SDR-0001
slug: record-architecture-decisions
title: Record architecture decisions
status: accepted
revision: 1
date: 2026-08-29
authors: [Tristan Rivoallan]
supersedes: []
traits:
    record-architecture-decisions:
        format: MADR
        limit: 500
---
# Record architecture decisions

> **Cet ADR-ci n'est pas une question.** Les autres arrivent `status: proposed` et attendent que votre équipe statue. Celui-ci arrive `accepted`, parce qu'il décrit la mécanique avec laquelle vous allez statuer sur les autres. Vous pouvez le dépasser comme n'importe quel autre — par un nouvel ADR qui le cite dans son `supersedes:` — mais tant qu'il tient, c'est lui qui dit comment les ADR s'écrivent ici.

## Context and Problem Statement

Une décision d'architecture qui ne vit que dans une conversation se rediscute tous les six mois, avec les mêmes arguments et sans le contexte qui l'avait décidée. Un ADR — *Architecture Decision Record* — est cette décision consignée : son contexte, les options pesées, ce qui a été retenu, et ce que ça coûte.

Reste à décider **comment** on les tient, et c'est là que se glisse l'erreur la plus courante : croire qu'un outil couvre le travail des deux autres.

## Considered Options

- **Des ADR à la main, sans outil.** Rien à installer, et la numérotation dérive dès le deuxième contributeur.
- **`adr-tools` seul.** Le fichier est fabriqué correctement, mais rien n'est lisible par une machine : reconstruire l'historique des dépassements demande d'analyser du texte libre.
- **`adr-tools` + frontmatter + `mdschema`**, chacun sur son travail.

## Decision Outcome

Le troisième. Les trois outils se partagent la tâche et ne se recouvrent pas.

**1. Le geste est `adr-tools`.** Les fichiers se nomment `NNNN-titre.md`, quatre chiffres, et le numéro est le suivant du plus haut présent.

```bash
adr new "Titre de la décision"   # crée NNNN-titre-de-la-decision.md
adr new -s 7 "Titre"             # crée le suivant ET marque le 0007 dépassé
adr list
```

**Un ADR dépassé ne quitte pas le répertoire.** Il reste, marqué. Un répertoire d'ADR n'est pas la liste de ce qui est en vigueur : c'est un **journal**, et c'est ce qui permet de lire l'histoire des décisions plutôt que leur seul état final.

**2. Le corps gèle à `accepted` ; le statut, non.** À partir de `accepted`, la décision fait foi et le texte ne bouge plus — la rouvrir demande un nouvel ADR. Une seule chose continue de s'écrire dans un ADR gelé : son `status`. C'est la contrepartie du point 1 — un journal doit pouvoir dire qu'une entrée a été dépassée sans réécrire ce qu'elle disait.

**3. Le frontmatter est la source machine.** `adr-tools` écrit le dépassement en toutes lettres, dans les deux fichiers. C'est lisible, et ce n'est pas calculable. Le frontmatter porte l'arête une seule fois :

```yaml
adr: SDR-0008           # doit correspondre au nom du fichier
status: accepted        # accepted ou rejected — jamais vide sur un ADR qui porte son verdict
revision: 1             # écrite par la méthode — datez la question, pas le fichier
date: 2026-08-29
supersedes: ["SDR-0003"]
```

**L'arête inverse ne s'écrit pas, elle se calcule** : un ADR est dépassé si un autre le nomme dans son `supersedes:`. La stocker en double donnerait deux endroits à tenir d'accord, et rien ne les comparerait.

**4. `mdschema` atteste, il ne refuse rien.** Le `.mdschema.yml` de ce répertoire vérifie qu'un ADR **porte son verdict** — statut décidé, date renseignée, aucune clé de trait laissée vide — et que sa structure suit MADR : en-têtes en anglais, corps dans votre langue.

```bash
cd docs/adr && npx @jackchuka/mdschema@0.15.1 check '*.md'
```

Il **nomme** ce qui manque et s'arrête là. Si cette ligne rend `sh: mdschema: command not found` — mesuré le 2026-09-20 sur macOS arm64, `npm` ne liant pas le binaire du paquet —, prenez le binaire autonome dans les *releases* de [son dépôt](https://github.com/jackchuka/mdschema).

**5. Un ADR `SDR-` porte une question de la méthode, pas sa réponse.** Le préfixe le dit : la question vient d'amont, **la réponse appartient à ce dépôt**. Les ADR que vous écrirez vous-mêmes ne portent pas ce préfixe et gardent leur propre numérotation, dans ce même répertoire.

Ils arrivent donc `status: proposed`, et le rester est un état, pas un oubli — celui-ci fait exception, il arrive avec son verdict parce qu'il ne pose aucune question.

**Le `traits:` du frontmatter est la part machine de la réponse.** Un trait est une clé que la méthode transporte et dont la valeur vous appartient : elle pose la question, vous écrivez la réponse au même endroit. La prose explique et justifie ; le trait se lit sans avoir à être interprété.

**Et si la méthode a tort de poser la question ainsi**, la voie est un ADR à vous — sans préfixe — écrit **dans ce même répertoire**, citant celui dont il dévie et disant en quoi. Il ne dépend d'aucun réseau : la trace vit là où la décision s'applique.

### Consequences

**Ce que ça achète.** Une décision se retrouve avec son contexte et son prix. Le graphe des dépassements se calcule. Un ADR resté à moitié rempli se voit quand on lance la commande.

**Ce que ça coûte.** Trois conventions, dont une seule est outillée : `adr-tools` fabrique le fichier, mais ni la cohérence entre `adr:` et le nom du fichier, ni l'appel à `mdschema`, ne sont automatiques.

**Ce que rien ne tient.** Aucun contrôle ne lance `mdschema` : ni `adr new`, ni un commit, ni une merge request. Si personne ne tape cette commande, rien ne regarde vos ADR. Et `adr new` calcule le numéro suivant **localement** : deux branches ouvertes en parallèle produisent deux fois le même, sans que rien ne le signale avant la fusion. La relecture est le seul contrôle sur ces deux-là.

## More Information

Le format des sections est [MADR](https://adr.github.io/madr/) ; l'idée d'origine est celle de Michael Nygard, et l'outil celui de [Nat Pryce](https://github.com/npryce/adr-tools).
