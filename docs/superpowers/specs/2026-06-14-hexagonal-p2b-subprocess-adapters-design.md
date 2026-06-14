# P2b — Adaptateurs driven « subprocess » (`SubprocessToolRunner` + `RegctlImageInspector`)

> Raffinement de phase de la spec maîtresse
> [`2026-06-13-hexagonal-architecture-design.md`](./2026-06-13-hexagonal-architecture-design.md)
> (PR #758, encore en draft à la rédaction). Ce document **fait autorité** pour la phase P2b et
> **supersède** le placement de regctl décrit en §5.1 de la spec maîtresse.

## 1. Contexte

P0, P1 et P2a sont sur `main` (`7d60327`, `06a20ed`, `ae1df91`). P2a a livré les deux adaptateurs
délégateurs triviaux (`RegistryImageInspector`, `EntryPointAnalyzerProvider`). P2b livre les
adaptateurs driven restants qui encapsulent du **subprocess** — non triviaux : ils enveloppent les
wrappers réels et tranchent un point de design laissé ouvert par la spec maîtresse (« le jeu exact
de méthodes capacité sera figé au plan »).

L'exploration des wrappers et de leurs consommateurs (2026-06-14) a établi deux faits :

1. **Le port `ToolRunner` (P1) ment sur ses types.** Tout est typé `dict[str, Any]` alors que
   `run_trufflehog → list[dict]`, le lint hadolint → `list[dict]`, et `run_regctl → str`.
2. **`run_regctl` n'est pas un scanner.** Il est appelé par cinq analyzers (`oci`, `hadolint`,
   `size`, `freshness`, `versioning`) pour `image inspect`, `manifest get`, `manifest head` et
   `tag ls` — exactement les opérations que le port `ImageInspector` déclare déjà
   (`get_manifest`/`get_blob`/`get_digest`/`list_tags`).

## 2. Décision clé — regctl devient un 2ᵉ `ImageInspector`

regctl est une **alternative CLI au client registry HTTP**, pas un outil de scan. Il implémente le
même contrat d'inspection que `RegistryClient`. P2b le promeut donc en **seconde implémentation du
port `ImageInspector`** (`RegctlImageInspector`), et **retire `inspect_platforms` du port
`ToolRunner`**. `ToolRunner` redevient purement « scanners ».

Conséquence : le port `ImageInspector` **reste inchangé** (4 méthodes, agnostique plateforme). La
résolution par-plateforme que `run_regctl --platform` fait aujourd'hui en un appel devient de la
**traversée d'index explicite** côté analyzer (récupérer l'index via `get_manifest`, choisir le
digest de la plateforme, puis `get_manifest`/`get_blob` sur ce digest). C'est de la logique domaine,
migrée en **P3** ; l'analyzer OCI le fait déjà par digest pour le cas index.

Alternatives écartées : (a) garder `inspect_platforms` dans `ToolRunner` comme le dit la spec
maîtresse — laisse une méthode étroite qui ne couvre pas tag-ls / config / digest ; (b) paramétrer
le port `ImageInspector` par plateforme — déborde sur `RegistryClient` (l'API HTTP ne sait pas
résoudre une plateforme), casse la symétrie des deux backends.

## 3. Périmètre & découpage

Deux PR courtes (préférence repo + machinerie autorebase), une par adaptateur :

- **P2b-1** — `SubprocessToolRunner` (port `ToolRunner`, scanners) + révision honnête du port +
  mise à jour de `FakeToolRunner`.
- **P2b-2** — `RegctlImageInspector` (2ᵉ implémentation de `ImageInspector`).

`FileReportSink` (l'ancien P2c de la spec maîtresse) reste en aval, hors périmètre P2b.

## 4. P2b-1 — `ToolRunner` (scanners) + `SubprocessToolRunner`

### 4.1 Port révisé (`regis/core/ports/tool_runner.py`)

Touche du code P1 mergé, mais purement interne et pré-release. Aucun consommateur n'existe encore
(les analyzers n'ont pas basculé sur `ctx` — P3).

| Méthode | Type de retour | Wrapper / source |
| --- | --- | --- |
| `scan_vulnerabilities(image)` | `dict[str, Any]` | `run_grype` |
| `generate_sbom(image)` | `dict[str, Any]` | `run_syft` |
| `scan_secrets(image)` | **`list[dict[str, Any]]`** | `run_trufflehog` (pas d'arg `platform`) |
| `lint_dockerfile(dockerfile: str)` | **`list[dict[str, Any]]`** | inline hadolint extrait |
| `audit_image(image)` | `dict[str, Any]` | inline dockle extrait |
| `run(tool, args, *, timeout=None)` | `ToolResult` | échappatoire plugins |
| ~~`inspect_platforms`~~ | — | **supprimée** (partait sur regctl) |

### 4.2 `SubprocessToolRunner` (`regis/adapters/driven/tools/subprocess_tool_runner.py`)

- Détient les **credentials** (registry user/password) injectés par la composition root (P3). Un
  analyzer ne voit plus jamais de mot de passe.
- Construit la référence `registry/repo:tag` à partir de l'`ImageReference` (qui ne porte pas de
  creds) ; passe `image.platform` aux outils qui le supportent (grype, syft) ; pas à trufflehog.
- `scan_vulnerabilities`/`generate_sbom`/`scan_secrets` délèguent aux wrappers existants
  `run_grype`/`run_syft`/`run_trufflehog`.
- `lint_dockerfile(contents)` : **réplique** la portion subprocess de `HadolintAnalyzer.analyze`
  (`regis/analyzers/hadolint.py:52`) — `ensure_tool("hadolint")` + `subprocess.run([…, "-f",
  "json", "-"], input=contents)` + parse → **liste brute d'issues hadolint**. Ne fait QUE le
  subprocess. La reconstruction du pseudo-Dockerfile depuis `config.history` et le mapping
  issues/`issues_by_level`/report **restent dans l'analyzer** (domaine, P3).
- `audit_image(image)` : **réplique** la portion subprocess de `DockleAnalyzer.analyze`
  (`regis/analyzers/dockle.py:52`) — `ensure_tool("dockle")` + `subprocess.run([…, "-f", "json",
  target])` (+ env `DOCKER_USER`/`DOCKER_PASSWORD`) + parse → **dict dockle brut**
  (`{summary, details}`). Le mapping vers le report reste dans l'analyzer (domaine, P3).

> **Réplication, pas réécriture.** Il n'existe pas de wrapper `utils/{hadolint,dockle}.py` : le
> subprocess est inline dans les analyzers. P2b **recopie** cette portion subprocess dans
> l'adaptateur (testée isolément) ; les analyzers `hadolint`/`dockle` **gardent leur code inline
> inchangé** jusqu'à P3. L'adaptateur est construit mais **pas encore consommé** — exactement comme
> `RegistryImageInspector` en P2a. La déduplication (l'analyzer délègue via `ctx.tools`) se fait en
> P3, quand le contrat `analyze(ctx)` injecte enfin un `ToolRunner`.
- `run(tool, args, timeout)` : échappatoire générique via `run_cmd`, renvoie un `ToolResult`.
- **Erreurs** : lève `ToolError` (core). Traduit les échecs subprocess (non-zéro, timeout, JSON
  invalide, outil manquant).

## 5. P2b-2 — `RegctlImageInspector`

Seconde implémentation du port `ImageInspector` **inchangé**, backend regctl CLI
(`regis/adapters/driven/registry/regctl_image_inspector.py`) :

| Port (inchangé) | Appel regctl |
| --- | --- |
| `list_tags()` | `tag ls <reg>/<repo>` → `splitlines` |
| `get_manifest(reference)` | `manifest get <ref> --format raw-body` → JSON |
| `get_blob(digest)` | `blob get <reg>/<repo> <digest>` → JSON |
| `get_digest(reference)` | `manifest head <ref>` → `strip` |

- Construit `<ref>` via `image_ref(registry, repository, reference)` (`regis/utils/regctl.py`).
- Réutilise `run_regctl(client, …)` pour les credentials + le docker-config temporaire (déjà
  testés). Construit avec un `RegistryClient` (coordonnées + creds), comme `RegistryImageInspector`.
- **Erreurs** : traduit `AnalyzerError` / `subprocess.CalledProcessError` legacy en `RegistryError`
  core, via un contextmanager (même pattern que P2a).
- Non consommé par les analyzers en P2b (comme `RegistryImageInspector` en P2a) ; le câblage par la
  composition root et la bascule des analyzers regctl arrivent en P3.

## 6. Gestion d'erreurs

Les **nouveaux** adaptateurs lèvent les erreurs *core* (`ToolError` pour le runner, `RegistryError`
pour l'inspector regctl). Les wrappers legacy `regis/utils/{grype,syft,trufflehog,regctl}.py`
**conservent `AnalyzerError`** tant que les analyzers les appellent directement — leur migration
vers `ToolError` est reportée en **P3** (sinon ripple sur le `except AnalyzerError: raise` de
`hadolint`). `core/*` n'importe toujours pas `click` ; le contrat import-linter reste vert.

## 7. Stratégie de test

- `FakeToolRunner` (`tests/fakes.py:50`) : retirer `inspect_platforms` ; corriger les types de
  `scan_secrets`/`lint_dockerfile` (→ `list`). Vérifier qu'aucun test P1 n'asserte
  `inspect_platforms`.
- `SubprocessToolRunner` : tester chaque capacité avec un subprocess mocké (stdout canné) +
  les chemins d'erreur/traduction (`ToolError`). Pour `lint_dockerfile`/`audit_image`, vérifier que
  seule la sortie brute est renvoyée (pas de mapping).
- `RegctlImageInspector` : `run_regctl` mocké, une assertion par méthode (args regctl attendus +
  parse) + traduction `RegistryError`.
- Suite verte ; double gate de couverture ≥ 90 % (global + par fichier).

## 8. Hors périmètre (différés)

- Bascule du contrat analyzer `analyze(ctx)` + traversée d'index domaine + migration des wrappers
  legacy vers `ToolError` → **P3**.
- Déménagement physique des modules → **P4**.
- `FileReportSink` → phase dédiée (ex-P2c spec maîtresse).
- Câblage composition root + factory inspector par thread → **P3**.

## 9. Definition of Done (P2b)

- [ ] `ToolRunner` révisé (types honnêtes, `inspect_platforms` retirée), `FakeToolRunner` aligné.
- [ ] `SubprocessToolRunner` livré + testé (6 capacités, erreurs `ToolError`).
- [ ] `RegctlImageInspector` livré + testé (4 méthodes, erreurs `RegistryError`).
- [ ] Analyzers `hadolint`/`dockle` **strictement inchangés** (code inline conservé ; l'adaptateur
      réplique mais ne rewire pas — dédup en P3). Suite d'analyzers existante toujours verte.
- [ ] `lint-imports` vert ; suite verte ; couverture ≥ 90 % (double gate).
- [ ] 2 PR mergées (P2b-1, P2b-2), branchées juste avant commit sur `main` à jour.
</content>
</invoke>
