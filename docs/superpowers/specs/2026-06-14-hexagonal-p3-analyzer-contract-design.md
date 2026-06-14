# P3 — Bascule du contrat analyzer vers `analyze(ctx)` (use-cases + composition root)

> Raffinement de phase de la spec maîtresse
> [`2026-06-13-hexagonal-architecture-design.md`](./2026-06-13-hexagonal-architecture-design.md) (§4.3, §5.3, §5.4).
> Ce document fait autorité pour la phase **P3** et son découpage en sous-PRs.

## 1. Contexte

P0→P2c sont sur `main` : tous les ports (`ImageInspector`, `ToolRunner`, `ReportSink`,
`AnalyzerProvider`) et leurs adaptateurs driven existent (`RegistryImageInspector`,
`RegctlImageInspector`, `SubprocessToolRunner`, `FileReportSink`, `EntryPointAnalyzerProvider`),
mais **aucun n'est encore consommé**. P3 est la bascule : les analyzers passent du contrat legacy
`analyze(self, client, repository, tag, platform=None)` au contrat hexagonal
`analyze(self, ctx: AnalysisContext)`, et un use-case `AnalyzeImage` + une composition root câblent
les adaptateurs. **Rupture nette du contrat plugin** (pré-v1, assumée ; doc upgrade en P5).

Les 14 analyzers se répartissent en 4 groupes selon ce qu'ils consomment réellement de `client` :

| Groupe             | Analyzers                                  | Usage actuel de `client`                       | Besoin hexagonal                                                          |
| ------------------ | ------------------------------------------ | ---------------------------------------------- | ------------------------------------------------------------------------- |
| **Scanners**       | cve, sbom, secrets, dockle                 | creds seuls (`username`/`password`/`registry`) | `ctx.tools` (creds dans `SubprocessToolRunner`) ; inspector **inutilisé** |
| **regctl**         | oci, hadolint, size, freshness, versioning | `registry` + `run_regctl`                      | `ctx.inspector` (regctl) ; hadolint aussi `ctx.tools`                     |
| **HTTP-inspector** | provenance, scorecarddev                   | `client.get_manifest`/`get_blob`               | `ctx.inspector`                                                           |
| **External-only**  | popularity, endoflife, metadata            | rien / API externe                             | ni inspector ni tools (juste `ctx.image`)                                 |

`MetadataAnalyzer` est doublement spécial : construit via `__init__(metadata=...)` et son
`analyze(client=None, …)` **ignore** ses arguments.

## 2. Décisions (tranchées au brainstorming, 2026-06-14)

1. **Un seul ImageInspector au runtime : `RegctlImageInspector`** (« tout sur regctl »). `ctx.inspector`
   est toujours regctl-backed. `provenance`/`scorecarddev` migrent de l'API HTTP vers les méthodes du
   port servies par regctl (`get_manifest`/`get_blob` — données équivalentes). `RegistryClient`
   **reste** (porteur de creds pour regctl + scanners, coordonnées du `RegctlImageInspector`) ;
   `RegistryImageInspector` (P2a) devient **vestigial** (suppression = nettoyage ultérieur, hors P3).
   Conséquence thread-safety : le `RegctlImageInspector` est **subprocess-based** (creds = chaînes
   immuables) donc partageable entre threads ; le souci de `requests.Session` par thread ne subsiste
   que pour la branche **legacy HTTP** pendant la migration et disparaît à P3d.
2. **Le use-case `AnalyzeImage` existe dès P3a** (pas différé en dernier). Il orchestre la boucle
   d'analyzers ; la composition root le câble et la CLI bascule dessus dès P3a.

## 3. Contrat cible

```python
@dataclass
class AnalysisContext:                 # déjà en core/domain (P1)
    image: ImageReference
    inspector: ImageInspector
    tools: ToolRunner

class BaseAnalyzer(ABC):
    name: str = ""
    schema_file: str = ""
    uses_context: bool = False         # marqueur de pont temporaire (retiré en P3d)

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]: ...
    @abstractmethod
    def analyze(self, ctx: AnalysisContext) -> dict[str, Any]: ...   # NOUVEAU contrat
    def validate(self, report: dict[str, Any]) -> None: ...          # inchangé
```

Exemples de bascule :

- **cve** : `run_grype(full, client.username, client.password, platform)` →
  `ctx.tools.scan_vulnerabilities(ctx.image)`.
- **provenance** : `client.get_manifest(ref)` / `client.get_blob(digest)` →
  `ctx.inspector.get_manifest(ref)` / `ctx.inspector.get_blob(digest)`.
- **oci** (regctl) : `run_regctl(client, ["manifest","get",ref,"--format","raw-body"])` +
  traversée d'index `--platform` → `ctx.inspector.get_manifest(ref)` + **traversée d'index explicite
  en domaine** (récupérer l'index, choisir le digest de chaque plateforme, `get_manifest`/`get_blob`
  par digest — l'analyzer OCI le fait déjà par digest).
- **metadata** : `__init__(metadata=...)` conservé ; `analyze(ctx)` ignore `ctx`.

## 4. Pont temporaire

Pendant la migration par groupes, le use-case dispatche selon le marqueur `uses_context`. **Le
use-case (`core/application`) ne référence aucun type d'adaptateur** : la construction du client
legacy et de l'inspector est déléguée à des **callables injectés** par la composition root (§5/§7) :

```python
# dans AnalyzeImage, par analyzer (worker thread) — self._* sont injectés
if analyzer.uses_context:
    ctx = AnalysisContext(image, self._inspector_factory(image), self._tools)
    report = analyzer.analyze(ctx)
else:                                            # branche legacy + factory, retirées en P3d
    client = self._legacy_client_factory(image)  # opaque (Any) côté core
    report = analyzer.analyze(client, image.repository, image.tag, platform=image.platform)
analyzer.validate(report)
```

- `self._tools` : le port `ToolRunner` injecté (un `SubprocessToolRunner(user, password)` **partagé**,
  sans état mutable — construit par la composition root).
- `self._inspector_factory : Callable[[ImageReference], ImageInspector]` : produit un
  `RegctlImageInspector` frais par tâche (creds capturées).
- `self._legacy_client_factory : Callable[[ImageReference], Any]` : **temporaire**, produit le
  `RegistryClient` par tâche (sessions HTTP non partageables) pour la branche legacy.

À P3d : suppression du marqueur, de la branche legacy et de `legacy_client_factory` ; il ne reste que
le runner + l'inspector (partageable car subprocess-based).

## 5. Composition root

Une **fonction de câblage** dans l'adaptateur CLI (`adapters/driving/cli/…`, pas de conteneur DI)
assemble, depuis l'`ImageReference` + les creds résolues :

- `provider = EntryPointAnalyzerProvider()` ;
- `tools = SubprocessToolRunner(user, password)` ;
- un builder de `RegistryClient` par tâche (creds capturées) — temporaire, pour le pont ;
- et injecte le tout dans `AnalyzeImage`. La CLI appelle `AnalyzeImage.run(...)` puis poursuit avec
  playbooks / émission / verdict (inchangés en P3a — voir §7).

## 6. Découpage en sous-PRs

| PR      | Périmètre                                                                                                                                                                                                                                             | Difficulté    |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| **P3a** | use-case `AnalyzeImage` (boucle analyzers) + composition root + bascule CLI + pont + migration **groupe Scanners** (cve, sbom, secrets, dockle)                                                                                                       | moyenne       |
| **P3b** | migration **HTTP + External** (provenance, scorecarddev → inspector regctl ; popularity, endoflife, metadata)                                                                                                                                         | basse-moyenne |
| **P3c** | migration **groupe regctl** (oci, hadolint, size, freshness, versioning) — traversée d'index en domaine + dédup hadolint (`ctx.tools.lint_dockerfile`)                                                                                                | **haute**     |
| **P3d** | folder playbooks + émission (`ReportSink`) + verdict dans `AnalyzeImage`/`Evaluate` ; retrait du pont + branche legacy + marqueur ; migration `utils/{grype,syft,trufflehog,regctl,process} → ToolError` ; suppression de `click` de la couche outils | moyenne       |

Chaque sous-PR garde la suite verte + le double gate couverture + `lint-imports` KEPT, et reste
indépendamment mergeable (la CLI fonctionne à chaque étape).

## 7. P3a en détail

**Portée du use-case (bornée) :** `AnalyzeImage` couvre **uniquement la boucle d'analyzers** —
`run(image, *, skip, max_workers) -> dict[str, dict[str, Any]]` (nom → rapport). Il construit le
`ThreadPoolExecutor` (déplacé depuis `commands/analyze.py`), bâtit `ctx`/`client` par tâche,
dispatche via le pont (§4), valide. Les étapes **post-boucle** (assemblage du rapport final,
`run_playbooks`, émission, verdict) **restent dans la CLI** en P3a et basculeront dans le use-case en
P3d.

**Fichiers (indicatif) :** `regis/core/application/analyze_image.py` (use-case) ;
`regis/adapters/driving/cli/composition.py` (composition root) ; `regis/commands/analyze.py`
(remplace la boucle inline `_run_analyzer`+ThreadPool par un appel à `AnalyzeImage`) ;
`regis/analyzers/base.py` (ajout `uses_context`) ; `cve.py`/`sbom.py`/`secrets.py`/`dockle.py`
(bascule `analyze(ctx)` + `uses_context=True`). Le `metadata` reste legacy en P3a (migré en P3b).

**Layering :** `AnalyzeImage` est en `core/application` — il ne peut PAS importer les adaptateurs ni
`RegistryClient`/`RegctlImageInspector` directement. Le pont legacy (qui construit un `RegistryClient`

- `RegctlImageInspector`) crée une tension : ces types sont des **adaptateurs**. **Résolution** : le
  use-case reçoit le pont sous forme de **callables injectés** par la composition root —
  `legacy_client_factory: Callable[[ImageReference], Any]` et
  `inspector_factory: Callable[[ImageReference], ImageInspector]` — de sorte que `core/application`
  ne référence aucun type d'adaptateur. Les deux factories sont **temporaires** (le pont meurt en P3d ;
  ne restera que `inspector_factory` ou un inspector partagé). `import-linter` reste vert.

**Tests P3a :** `AnalyzeImage` testé avec les fakes (`FakeImageInspector`/`FakeToolRunner` +
`StubAnalyzerProvider`) + un faux analyzer `uses_context=True` et un legacy → vérifier le dispatch,
le `skip`, la collecte, la validation, le parallélisme. Les 4 scanners migrés : adapter leurs tests
existants au nouveau contrat (`analyze(ctx)` avec un `FakeToolRunner` cannée). Suite verte, double
gate ≥ 90 %.

## 8. Hors périmètre (différés)

- Folding playbooks/émission/verdict dans le use-case → **P3d**.
- Suppression de `RegistryImageInspector` vestigial + `RegistryClient` réduit à un porteur de creds →
  **P4/P5** (décision séparée).
- Déménagement physique des modules (`analyzers/` → emplacement final) → **P4**.
- Docs (CLAUDE.md patch-targets, guide upgrade plugins, decisionLog) → **P5**.
- `Evaluate` use-case (chemin `regis evaluate`) : esquissé en P3d, détaillé à sa propre passe.

## 9. Definition of Done (P3, à la fin de P3d)

- [ ] Les 14 analyzers implémentent `analyze(ctx)` ; `uses_context` et la branche legacy supprimés.
- [ ] `AnalyzeImage`/`Evaluate` orchestrent la boucle + playbooks + émission ; CLI = adaptateur driving fin.
- [ ] `utils/{grype,syft,trufflehog,regctl,process}` lèvent `ToolError`/`RegistryError` ; plus de `click` hors CLI.
- [ ] `lint-imports` KEPT ; suite verte ; couverture ≥ 90 % (double gate) à chaque sous-PR.
