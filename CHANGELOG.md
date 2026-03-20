# Changelog

## [0.17.1](https://github.com/trivoallan/regis-cli/compare/v0.17.0...v0.17.1) (2026-03-20)

### Bug Fixes

- Add step to re-checkout merge ref for pull requests in the Trunk workflow. ([3678043](https://github.com/trivoallan/regis-cli/commit/36780437ade9f5ad69a39cc5596e6f820b34535b))
- Remove `--force` from Docusaurus versioning in CI and correct `versions.json` format. ([4fee11d](https://github.com/trivoallan/regis-cli/commit/4fee11d7d3697570751eb32351febc3bafa4e56d))

## [0.17.0](https://github.com/trivoallan/regis-cli/compare/v0.16.0...v0.17.0) (2026-03-20)

### Features

- **analyzers:** Reusable rules and simplified rule slugs ([#63](https://github.com/trivoallan/regis-cli/issues/63)) ([40d9f63](https://github.com/trivoallan/regis-cli/commit/40d9f63ea63ce8858e31c53c1991c409150ece63))
- **cli:** add rules list command and improve evaluator ([11a9118](https://github.com/trivoallan/regis-cli/commit/11a91189480b84cc0cb71aa35e72c4d9b32ea478))

### Bug Fixes

- **analyzer:** standardize rule names and fix analyzer validation ([#62](https://github.com/trivoallan/regis-cli/issues/62)) ([1a64c24](https://github.com/trivoallan/regis-cli/commit/1a64c24252459519e6765256b4364e140eaf0b9f))
- Correct relative path for the "Understand Playbooks" guide link in the default playbook overview. ([31c4d1b](https://github.com/trivoallan/regis-cli/commit/31c4d1b7b1a9dffeb035b4127a56f27464b9bc70))
- Remove redundant entries from `versions.json`. ([5407d53](https://github.com/trivoallan/regis-cli/commit/5407d5353c3e9d969239be96d6418ee4b4587f0f))
- **schema:** add missing fields to trivy schema and fix id resolution ([8894b25](https://github.com/trivoallan/regis-cli/commit/8894b254336cc82f554831d20ab721c0454e5deb))

### Documentation

- add workflow step to generate rules reference documentation. ([e325793](https://github.com/trivoallan/regis-cli/commit/e325793df08eb713a47038c639845a47cbbdef32))
- Change Docusaurus broken link handling from `throw` to `warn`. ([112bbbb](https://github.com/trivoallan/regis-cli/commit/112bbbb6e61e4c71bd0647aa032a87d43b036e77))
- enable local search and fix broken links ([#60](https://github.com/trivoallan/regis-cli/issues/60)) ([0ebae0f](https://github.com/trivoallan/regis-cli/commit/0ebae0fcaf9bede74eb9d20b1a519eb41292b203))
- overhaul rules documentation by separating concepts from reference, introducing MDX for detailed rule listings, and updating the rules engine explanation. ([721c13a](https://github.com/trivoallan/regis-cli/commit/721c13aa3f3b1601c2346da2627a1bf47929ed07))
- refine usage and concepts documentation ([6e09d1d](https://github.com/trivoallan/regis-cli/commit/6e09d1d9f20c90b32fec3e6bd6298740bb14e4f1))
- Remove old versioned documentation, reorganize current docs, and introduce a new CLI reference. ([b8a0b92](https://github.com/trivoallan/regis-cli/commit/b8a0b9275802e193035166fbcff385f7a74f86ad))
- restructure documentation and update index ([74b9090](https://github.com/trivoallan/regis-cli/commit/74b90905aa3030a3e6cd16b4ed2976235498f6e1))
- standardize rule documentation and add concept tags ([#61](https://github.com/trivoallan/regis-cli/issues/61)) ([3fadb26](https://github.com/trivoallan/regis-cli/commit/3fadb2678dcf9b7cc1949de7eaf2d74df0807ac9))
- **versioning:** setup docusaurus versioning and generate reference docs ([5ec6529](https://github.com/trivoallan/regis-cli/commit/5ec6529dc2d1874399223cd0d844b1939f550e92))
- **website:** fix configuration reload errors ([438dd86](https://github.com/trivoallan/regis-cli/commit/438dd86e3089916276e0c7096984227063664ed7))

## [0.16.0](https://github.com/trivoallan/regis-cli/compare/v0.15.0...v0.16.0) (2026-03-20)

### Features

- **ci:** automate trunk fmt and auto-commit in CI ([#48](https://github.com/trivoallan/regis-cli/issues/48)) ([76070ad](https://github.com/trivoallan/regis-cli/commit/76070ad58a2fce9f87113860e1863cebf04191a3))
- **cli/bootstrap:** display post-install notes after bootstrap ([#52](https://github.com/trivoallan/regis-cli/issues/52)) ([89419bf](https://github.com/trivoallan/regis-cli/commit/89419bf821fc40f9548598dca95ab00f926fb18b))
- implement Playbook Tiers, Dynamic Badges and restore multi-page reporting ([#56](https://github.com/trivoallan/regis-cli/issues/56)) ([ce91c37](https://github.com/trivoallan/regis-cli/commit/ce91c376766f99a0fca7f42ec9f262a1f6ecae07))

### Bug Fixes

- **ci:** fix trunk fmt conflict and resolve HTML syntax errors ([6aa52c1](https://github.com/trivoallan/regis-cli/commit/6aa52c16eb749ba6095bb814d6622c8ec39198c4))
- **ci:** robust auto-formatting and protected branch handling ([#51](https://github.com/trivoallan/regis-cli/issues/51)) ([ae9ae51](https://github.com/trivoallan/regis-cli/commit/ae9ae5144612dfb845371db50cab813888bd089c))
- **ci:** Update Python version to 3.14 in test workflow. ([e260b53](https://github.com/trivoallan/regis-cli/commit/e260b5351e6484357ffa712d8b5e5b16cde4529b))
- **cli:** resolve bootstrap command failure in Docker image ([#46](https://github.com/trivoallan/regis-cli/issues/46)) ([5c6ed6b](https://github.com/trivoallan/regis-cli/commit/5c6ed6b384527dd3c31f4a865872802c4d72acf4))
- resolve Trunk Check `HEAD^2` error by adjusting git checkout depth and auto-commit logic in the lint workflow. ([44100f1](https://github.com/trivoallan/regis-cli/commit/44100f13ec550990e468493105a2a2431912c520))

### Documentation

- implement dynamic documentation versioning and cleanup ([#58](https://github.com/trivoallan/regis-cli/issues/58)) ([98f4d47](https://github.com/trivoallan/regis-cli/commit/98f4d47db682ead6ef394a58597f4b7c88500dce))
- migrate documentation from Antora to Docusaurus ([#57](https://github.com/trivoallan/regis-cli/issues/57)) ([7620e6d](https://github.com/trivoallan/regis-cli/commit/7620e6db51357f053c50458452c8edcd2c6cc0ff))

## [0.15.0](https://github.com/trivoallan/regis-cli/compare/v0.14.2...v0.15.0) (2026-03-11)

### Features

- **ci:** add OCI image labels to Dockerfile ([#39](https://github.com/trivoallan/regis-cli/issues/39)) ([8deeb50](https://github.com/trivoallan/regis-cli/commit/8deeb50114a3a54c841e3fa7bce8ae0cba5a746b))
- **ci:** add standard OCI annotations to Dockerfile ([#43](https://github.com/trivoallan/regis-cli/issues/43)) ([#40](https://github.com/trivoallan/regis-cli/issues/40)) ([6c16c42](https://github.com/trivoallan/regis-cli/commit/6c16c4256143f1139b4d46fcfa25ead7d6cc212a))
- **ci:** allow Docker authentication to prevent rate limits ([#45](https://github.com/trivoallan/regis-cli/issues/45)) ([15f985b](https://github.com/trivoallan/regis-cli/commit/15f985bc13bcdd300746f2653a514cf7745b229f))

## [0.14.2](https://github.com/trivoallan/regis-cli/compare/v0.14.1...v0.14.2) (2026-03-05)

### Documentation

- refine project description and branding ([#37](https://github.com/trivoallan/regis-cli/issues/37)) ([bbe8fc7](https://github.com/trivoallan/regis-cli/commit/bbe8fc7e796df8974a256cdbf83a67978f1f9228))

## [0.14.1](https://github.com/trivoallan/regis-cli/compare/v0.14.0...v0.14.1) (2026-03-05)

### Documentation

- **README:** redesign README.md and update report preview ([#32](https://github.com/trivoallan/regis-cli/issues/32)) ([31d27fb](https://github.com/trivoallan/regis-cli/commit/31d27fb132276e4eaea7dd2c447da6cc011a5870))

## [0.14.0](https://github.com/trivoallan/regis-cli/compare/v0.13.0...v0.14.0) (2026-03-05)

### Features

- **ci:** migrate linting to trunk and add mypy/hadolint ([#29](https://github.com/trivoallan/regis-cli/issues/29)) ([4219843](https://github.com/trivoallan/regis-cli/commit/4219843ff5ecb512f708e6cc8acb3f824e841213))
- **cli:** refactor generate to bootstrap command group ([#28](https://github.com/trivoallan/regis-cli/issues/28)) ([ee9710e](https://github.com/trivoallan/regis-cli/commit/ee9710eae6ea9b92c6e00971ad18fe0742f65904))

### Documentation

- modernize getting started and project generation guides ([#26](https://github.com/trivoallan/regis-cli/issues/26)) ([2603c0c](https://github.com/trivoallan/regis-cli/commit/2603c0c1a1d02ff438953665174324c258229cbb))
- **playbook:** explain how to use bootstrap playbook in documentation ([#30](https://github.com/trivoallan/regis-cli/issues/30)) ([e1d20df](https://github.com/trivoallan/regis-cli/commit/e1d20df294ab9e67013b0d207820d2069d59debe))

## [0.13.0](https://github.com/trivoallan/regis-cli/compare/v0.12.0...v0.13.0) (2026-03-05)

### Features

- **analyzer/versioning:** implement digest-based reporting and release lines hierarchy ([#21](https://github.com/trivoallan/regis-cli/issues/21)) ([e54d04f](https://github.com/trivoallan/regis-cli/commit/e54d04f17077333fbc73d1b133a5b7b61228ed18))
- **ci:** implement gitlab subcommand for CI workflow ([#18](https://github.com/trivoallan/regis-cli/issues/18)) ([515069c](https://github.com/trivoallan/regis-cli/commit/515069cb5263b7addaa47551681cbcb43d3da995))

### Documentation

- **architecture:** add C4 Context and Container diagrams to architecture overview ([#24](https://github.com/trivoallan/regis-cli/issues/24)) ([fa8504e](https://github.com/trivoallan/regis-cli/commit/fa8504e8e2ee2a5c045f652b5a1aa6ce453cb766))
- **integrations:** group GitLab and GitHub documentation into Integrations section ([#22](https://github.com/trivoallan/regis-cli/issues/22)) ([c045323](https://github.com/trivoallan/regis-cli/commit/c04532366de32ec7f5eb07e1bbbde2cb6bc8f55f))
- **integrations:** restructure integration sub-chapter and add cookiecutter tips ([#23](https://github.com/trivoallan/regis-cli/issues/23)) ([1a5616b](https://github.com/trivoallan/regis-cli/commit/1a5616b2cea3851fba2b6f3c5c3091b2e8afcf7f))

## [0.12.0](https://github.com/trivoallan/regis-cli/compare/v0.11.0...v0.12.0) (2026-03-05)

### Features

- **playbook:** add support for multiple titled GitLab MR description checklists with backward compatibility. ([f865cb0](https://github.com/trivoallan/regis-cli/commit/f865cb00735d90a8185bb98f87373d05431b5caf))

### Bug Fixes

- **gitlab:** Improve GitLab CI report path handling ([9a7914f](https://github.com/trivoallan/regis-cli/commit/9a7914f8a5828eb2b8493d517dcc92af4f8df1a4))
- **template:** add missing `format_number` Jinja2 filter ([f76b30b](https://github.com/trivoallan/regis-cli/commit/f76b30b803125177543e2d47098c345f012b3b4d))

## [0.11.0](https://github.com/trivoallan/regis-cli/compare/v0.10.0...v0.11.0) (2026-03-05)

### Features

- **cli:** Add CLI command to check image manifest accessibility. Use it to prevent bogus requests. ([be291ee](https://github.com/trivoallan/regis-cli/commit/be291ee5e475c9617187549df2a88f8b7d229c67))
- **playbook:** Introduce configurable additional MR content generation from templates ([340f44d](https://github.com/trivoallan/regis-cli/commit/340f44d04891039080603fa2a86ba634f49ad82c))

### Documentation

- **playbook:** Document GitLab MR checklists with conditional display and pre-checking based on analysis results. ([9ca7a85](https://github.com/trivoallan/regis-cli/commit/9ca7a85fa885f566591dff68617924337b2cff7b))

## [0.10.0](https://github.com/trivoallan/regis-cli/compare/v0.9.0...v0.10.0) (2026-03-04)

### Features

- **analyzer/size:** add layer digest to the size analysis output for individual layers ([9393b48](https://github.com/trivoallan/regis-cli/commit/9393b48d6ebda82b7be2e9db5aad74a014f415f3))
- **ci:** Add a configurable playbook URL input to GitLab CI/CD. ([801dd3c](https://github.com/trivoallan/regis-cli/commit/801dd3c861b0fbc0af4b279204affd4d06c352cc))
- **ci:** make regis-cli image version configurable in generated GitLab CI. ([8da67d0](https://github.com/trivoallan/regis-cli/commit/8da67d08b4e12433157cb67a9516e269c732a5c3))
- **gitlab:** append review checklist from `report.json` to merge request descriptions and unquote `$REGIS_CLI_IMAGE` in CI. ([08211a2](https://github.com/trivoallan/regis-cli/commit/08211a264c32147c22e4c98aae089fdf02514501))
- **playbook:** Enhance GitLab MR checklist items with `show_if` and `check_if` conditions. ([ccde35e](https://github.com/trivoallan/regis-cli/commit/ccde35eb51a62199cb07113d9da1dda0240e2184))

### Bug Fixes

- **gitlab:** Fix report generation path ([4a1cfe7](https://github.com/trivoallan/regis-cli/commit/4a1cfe7f141b41736dbc928abcf4367c93b5476d))

## [0.9.0](https://github.com/trivoallan/regis-cli/compare/v0.8.0...v0.9.0) (2026-03-04)

### Features

- **playbook:** Implement GitLab MR description checklist feature for custom compliance checks. ([c22402e](https://github.com/trivoallan/regis-cli/commit/c22402ec2cab75ad19c2ba227d56eec2eb9d35a6))

### Bug Fixes

- **ci:** Fix broken Publish Documentation workflow ([300e313](https://github.com/trivoallan/regis-cli/commit/300e3133246ded1ff55b7aac01ee265ffada76e4))

## [0.8.0](https://github.com/trivoallan/regis-cli/compare/v0.7.0...v0.8.0) (2026-03-04)

### Features

- **analyzer/dockle:** add Dockle analyzer for container image security and best practices linting with supporting schema, tests, and documentation. ([e32c1f2](https://github.com/trivoallan/regis-cli/commit/e32c1f2f375e284619b521d37a8f05b4f8e75fff))
- **playbook:** Implement named addressing for playbook pages and sections ([cdbaefa](https://github.com/trivoallan/regis-cli/commit/cdbaefae55c5a25b828944dc8ec1f0f41e7fc0d6))
- **playbook:** integrate Dockle security analysis with a new policy, dedicated UI, and updated documentation. ([7806a53](https://github.com/trivoallan/regis-cli/commit/7806a53d52c30027926a24bc5fa18da08c7506e3))

### Documentation

- Add script to generate example reports and update documentation with new report data and publishing workflow. ([3598a1e](https://github.com/trivoallan/regis-cli/commit/3598a1e79f47bc177e94e7a5ca10111beb08b50a))
- Configure Antora to generate a documentation website for each release ([077497b](https://github.com/trivoallan/regis-cli/commit/077497bd962b5906bcf0e43715eb7a7588fe1e16))
- Implemented automated generation of schema documentation and integrate it into the Antora build workflow. ([11b9399](https://github.com/trivoallan/regis-cli/commit/11b93999f0dd063df64a1fc22aac25ba7a2b4c61))

## [0.7.0](https://github.com/trivoallan/regis-cli/compare/v0.6.0...v0.7.0) (2026-02-23)

### Features

- add --cache option to the analyze command to load and use an existing report.json, skipping re-analysis. ([3a7a710](https://github.com/trivoallan/regis-cli/commit/3a7a710c9329e4f5d812804044bf8bb190b9f416))
- add `--theme` option for HTML report generation and ignore the `/reports` directory ([8bb9e7b](https://github.com/trivoallan/regis-cli/commit/8bb9e7bec6268d5219d37818f0177846cc6aa81f))
- add Dockerfile and GitHub Actions workflow for building and publishing regis-cli Docker images. ([dfc66c6](https://github.com/trivoallan/regis-cli/commit/dfc66c6d6231748e5a893f6b38f4caba4c3be69b))
- add domain-trusted scorecard ([41ca994](https://github.com/trivoallan/regis-cli/commit/41ca994967acca90e4d410acae5a6317f97c4f9f))
- Add extensive test coverage for analyzers and core components, integrate Ruff linter, and refine Skopeo schema. ([ec215e0](https://github.com/trivoallan/regis-cli/commit/ec215e0bedb0adafda66ddfa57b01eb39e17e164))
- add GitHub Actions workflows for Super-Linter and automated releases. ([d8c8a28](https://github.com/trivoallan/regis-cli/commit/d8c8a282afdd1a5959ed8cc3b4f08daf3b54a65b))
- Add Hadolint analyzer to lint Dockerfiles and display results. ([b8802cb](https://github.com/trivoallan/regis-cli/commit/b8802cb29cee41ab08d70c87945d3265cdc505ca))
- Add initial HTML report for image health scores generated by regis-cli. ([419c65a](https://github.com/trivoallan/regis-cli/commit/419c65a8583704ec9e3d28dbd7448901c3374663))
- add Skopeo analyzer and refactor versioning analyzer to use Skopeo for tag listing. ([b933931](https://github.com/trivoallan/regis-cli/commit/b9339312aae5a1a3c42aabb7347bfa71f99436a0))
- add support for multiple output formats and templated output paths for the `run` command. ([6a70c93](https://github.com/trivoallan/regis-cli/commit/6a70c93d842609a4d091f413acc4f8aa0de94238))
- add support for passing metadata via CLI to reports and update report schema. ([07050ea](https://github.com/trivoallan/regis-cli/commit/07050ea6ceb8bc5e3c19d1c22f5249db1b9531dc))
- add support for templated links in scorecards and reports ([bc191af](https://github.com/trivoallan/regis-cli/commit/bc191afb2c8fad75dde499531533f35abf691fb7))
- add time formatting and recursive metadata rendering to improve report request details display. ([f86862e](https://github.com/trivoallan/regis-cli/commit/f86862e7289083562ad348dd0a4ac96127d64f8b))
- Add user and digest extraction and display to Skopeo image analysis. ([4cbacba](https://github.com/trivoallan/regis-cli/commit/4cbacba1b3e1ef3e4ce066dfaf32280884b25693))
- add variant detection and reporting to the versioning analyzer ([8c61394](https://github.com/trivoallan/regis-cli/commit/8c613946148fbd8d095de1ebc1bb27269b6532b8))
- **analyzers:** Enable private registry authentication for Trivy-based analyzers and update documentation. ([06c35eb](https://github.com/trivoallan/regis-cli/commit/06c35eb80a95a94846c29154ff658861c0331d5f))
- **ci:** introduce GitLab CI workflow for image analysis with MR-driven triggers and review app deployments. ([d85449d](https://github.com/trivoallan/regis-cli/commit/d85449d19e9e6cb6232b72cb5940e297c4608261))
- **cli:** Implement `generate` command with `cookiecutter` for project scaffolding and update project templates. ([44bfdf6](https://github.com/trivoallan/regis-cli/commit/44bfdf6e87070d4515ac685d43b1bf1d0974f948))
- **cli:** Implement a CLI version command, refactor `importlib.metadata` imports, and update tests and GitLab CI artifact handling. ([d508b53](https://github.com/trivoallan/regis-cli/commit/d508b53f72bf9396f060663fc1262ccc4e62a292))
- configure Antora Mermaid extension with a specific library URL and script stem. ([190fcc4](https://github.com/trivoallan/regis-cli/commit/190fcc49632bc50a466a2c56b8bcaf8d5ae6937d))
- **cookiecutter:** integrate GitHub Actions metadata into analysis reports for improved traceability and remove unused scorecard levels. ([4113efb](https://github.com/trivoallan/regis-cli/commit/4113efbecb2a92497c1de451b4efc09feee96934))
- **cookiecutter:** introduce Cookiecutter template for bootstrapping new image analysis projects with documentation, workflows, and default scorecards. ([391d74f](https://github.com/trivoallan/regis-cli/commit/391d74fa53f45e93dbb2204104a7a1869f70ad03))
- **cookiecutter:** Introduce Cookiecutter template for project bootstrapping and add its comprehensive usage guide, refining the template's analysis workflow input. ([9ef6351](https://github.com/trivoallan/regis-cli/commit/9ef6351574929e9f217c5c1eae2fae597cf3286e))
- display structured analyzer errors in the UI and store them in reports. ([f3dd654](https://github.com/trivoallan/regis-cli/commit/f3dd654fd8533147fef78550d72126ca3bd1a1d3))
- **doc:** Add 'Get Started' and 'Understand Playbooks' documentation pages and update navigation. ([e791354](https://github.com/trivoallan/regis-cli/commit/e791354736aad353c06c60189e040bd9f61c0f48))
- **docs:** initialize Antora documentation ([6ca4154](https://github.com/trivoallan/regis-cli/commit/6ca41541c17a0a942d8407c6256a59004d26805c))
- dynamically set cookiecutter image URL and simplify release-please extra-files configuration. ([b86853a](https://github.com/trivoallan/regis-cli/commit/b86853a7f9a7b032a1171e5ff7e9dbbe724c6fbf))
- embed regis-cli version in analysis reports and update cookiecutter image URLs. ([3ab5430](https://github.com/trivoallan/regis-cli/commit/3ab543048e4972ff9ec6c461f710c93991ad8924))
- enhance default playbook overview with new recommendation and compliance widgets and update widget styling. ([6737a68](https://github.com/trivoallan/regis-cli/commit/6737a6839152fea82141eda59241792cb5a59985))
- enhance registry credential resolution by normalizing Docker Hub aliases and remove the `score.html` report file. ([c2dd0e1](https://github.com/trivoallan/regis-cli/commit/c2dd0e17ab0810a247df8148d0c10f5ccf3ef682))
- enhance report output with per-scorecard HTML files, `slug` support, and improved file writing logic. ([895c46b](https://github.com/trivoallan/regis-cli/commit/895c46bbc98d8fe650ed3a657eb98b415abb4266))
- Enhance scorecard rule evaluation to track missing data, provide detailed condition stringification, and include rule tags in results and UI. ([cd94912](https://github.com/trivoallan/regis-cli/commit/cd949129cd65c20584c6a258c765bc8b4a378e34))
- enhance Trivy report display for multiple targets and refine report layout with dedicated sections for links and scorecards. ([9a29bad](https://github.com/trivoallan/regis-cli/commit/9a29bad85018b3fa93bf49ce4b204d99e1cca374))
- Implement conditional widget rendering, add new widget styling options including alignment and subvalues, and introduce new CSS for recommendations and header elements. ([78ade17](https://github.com/trivoallan/regis-cli/commit/78ade17344380013a2429d8bf519728d7d346415))
- implement flexible registry credential resolution via new `--auth` CLI option and dedicated module ([ac5afb3](https://github.com/trivoallan/regis-cli/commit/ac5afb33639d018d4d04611777c95b194f11d6dc))
- implement registry authentication using environment variables and add new tests. ([1894969](https://github.com/trivoallan/regis-cli/commit/18949692ac8c493f3ea62d0485efea75661e38e3))
- initialize regis-cli project with image analysis, scorecard engine, schema validation, and comprehensive project setup. ([3af2207](https://github.com/trivoallan/regis-cli/commit/3af2207ef86d5265c7fc32997219b3841172b0bb))
- Integrate scorecard evaluation directly into the `analyze` command, supporting multiple custom scorecards, and remove the dedicated `score` command. ([8301c36](https://github.com/trivoallan/regis-cli/commit/8301c36f77c897057a44b03abaeaf525067a4163))
- introduce new HTML report structure and styling with updated templates and CSS. ([94f5130](https://github.com/trivoallan/regis-cli/commit/94f5130d1c7dd0e0ad34098de757242e5d81a37b))
- Introduce OpenSSF Scorecard, Freshness, and Popularity analyzer reports with supporting configuration and robustness improvements. ([df311cc](https://github.com/trivoallan/regis-cli/commit/df311ccc38bb6c99c6c0ad0eaa9fd77fd21f49a0))
- introduce SBOM analysis using Trivy and CycloneDX, replacing the license analyzer. ([8fa1d24](https://github.com/trivoallan/regis-cli/commit/8fa1d24166324d4224287250b3456db7251924e2))
- introduce scorecard pages to group sections and add new size and versioning analyzers. ([2dd6b31](https://github.com/trivoallan/regis-cli/commit/2dd6b315c41cc440d57b349187acaa8e1a783b5b))
- Introduce section-based scorecards with a new schema and remove the dependency analyzer. ([e7adbea](https://github.com/trivoallan/regis-cli/commit/e7adbeab5a8404a2b983be5dad715b3f310f66fa))
- **playbooks:** Add support for loading playbooks from remote URLs and update cookiecutters to utilize this feature. ([69ef82f](https://github.com/trivoallan/regis-cli/commit/69ef82f57b4704135c0f3a4809a11be5294aa19b))
- refactor cookiecutter templates to support both GitHub and GitLab platforms with dedicated CI configurations and documentation. ([295db88](https://github.com/trivoallan/regis-cli/commit/295db881cd1b2eae17f595d567fe182fef087623))
- Refine scorecard reporting by updating schemas, engine logic, templates, and removing old report files. ([f3abf1f](https://github.com/trivoallan/regis-cli/commit/f3abf1f9a94faa638039bc959566315acf014b8f))
- render error cards for all unhandled analyzer errors in the report ([9bf27db](https://github.com/trivoallan/regis-cli/commit/9bf27db38e8bc9a542f286aa7638dc92e19be87e))
- replace single achieved level with a detailed summary by level in scorecard results, CLI output, and HTML report. ([c81c2ce](https://github.com/trivoallan/regis-cli/commit/c81c2ce854c25896765c2e9938361b02569c005e))
- **report:** Embed regis-cli version into analysis reports and schema ([ac3efb5](https://github.com/trivoallan/regis-cli/commit/ac3efb55d70263c5417c02df59522201e7ca501e))
- **reports:** Implement automatic versioning of analysis reports in GitLab CI and document its configuration. ([c985942](https://github.com/trivoallan/regis-cli/commit/c9859427c88ce06ae0cde3a64566fe6dc961a788))
- **review:** enhance GitLab CI report delivery by committing to `reports/`, posting direct links to MR comments, and updating documentation. ([d934913](https://github.com/trivoallan/regis-cli/commit/d934913c7451a9565ce3f8a2626ae3b54f24002a))
- **review:** enhance GitLab CI/CD to specify output filename, run site generation on the default branch, and dynamically configure Pages deployments for review apps and main branch, while updating the project backlog. ([342d0b8](https://github.com/trivoallan/regis-cli/commit/342d0b86d4b9111f5dc4d43a680c53ec4af7a335))
- **review:** Expose analysis reports as Merge Request artifacts instead of deploying to Review Apps and update documentation accordingly. ([c4850be](https://github.com/trivoallan/regis-cli/commit/c4850be3bbd6548d6d854529a59f2353bbc595b5))
- **review:** Implement and document a self-service analysis workflow in GitLab CI, including optional report commits to the branch and dynamic Review App links. ([016659d](https://github.com/trivoallan/regis-cli/commit/016659d34cf87e68b1af8e68e4806372c923979a))
- **review:** Introduce automated GitLab MR labeling and conditional playbook links based on analysis outcomes. ([86e5986](https://github.com/trivoallan/regis-cli/commit/86e59862895324ebb6276d31b94b99ec53f432bf))
- **review:** use GitLab API for merge request creation to enable setting reviewers and assignees, and add `curl` dependency. ([32f98f2](https://github.com/trivoallan/regis-cli/commit/32f98f226263ed577fd649743af69f0f7f2eff85))
- set default output directory template to include the tag. ([157f425](https://github.com/trivoallan/regis-cli/commit/157f425cca42a71afb089dd4fff6d1944abf9c95))
- Track and display involved data analyzers for scorecard rule evaluations in the schema, engine, and HTML report. ([42bcace](https://github.com/trivoallan/regis-cli/commit/42bcace830ae4aebb83b23c17486c79c867fc61d))
- **ui:** Implement a new report rendering engine with a sidebar layout and dedicated pages for various analysis results. ([e1faaf9](https://github.com/trivoallan/regis-cli/commit/e1faaf92dadc215bbcdfecf90d164b5a2658ad64))
- **ui:** Introduce new analyzer display templates and enhance the playbook engine to support section widgets. ([b998f63](https://github.com/trivoallan/regis-cli/commit/b998f63f50691a9a186ba83b1a3ebe42cb21751e))

### Bug Fixes

- **analyzers:** Expose analyzer results at the root of the scorecard evaluation context and update default Trivy rules. ([460871b](https://github.com/trivoallan/regis-cli/commit/460871ba19698bfff3b33f40183f742501d80045))
- **analyzers:** prevent Skopeo analyzer from failing on index image inspection and formalize commit message guidelines. ([c80f88c](https://github.com/trivoallan/regis-cli/commit/c80f88c0dc4dcefa2610c959812d8232649629a3))
- **build:** install git in Dockerfile ([dfffabd](https://github.com/trivoallan/regis-cli/commit/dfffabd778a1fbbe8d371f2d8713f95568427d04))
- **ci:** add workflow_dispatch trigger and refine tag matching for Docker publish workflow. ([21b7549](https://github.com/trivoallan/regis-cli/commit/21b754967ad212cea23c0a13d623ce06902c0058))
- **ci:** configure releaser-pleaser action with release token ([ed8a1f2](https://github.com/trivoallan/regis-cli/commit/ed8a1f2ff386d0f54b91b4b2cde3c07b770c73aa))
- **docker:** address permission denied errors in Docker by setting user UID/GID, ensuring directory writability, and adding a report output fallback. ([ddaba2c](https://github.com/trivoallan/regis-cli/commit/ddaba2ceb4c931fca1f68555e63e6408a32baec6))
- **docker:** Resolve Docker container permission issues by creating a home directory for the `regis` user and setting report directory permissions, and update the analysis workflow. ([9cf4087](https://github.com/trivoallan/regis-cli/commit/9cf408788e2923524da428b0eb19f2eb90f763bf))
- Prevent `AttributeError` in scorecard link processing by adding type checks and update `regis-cli` workflow flags to long form. ([a02caa3](https://github.com/trivoallan/regis-cli/commit/a02caa33bb8fc47fbed119bdd797ad84eeb7cdc0))

### Dependencies

- Populate Pipfile.lock with resolved dependency versions. ([e87ee2c](https://github.com/trivoallan/regis-cli/commit/e87ee2cd971b4d35c8cf4ccbf1ad5ee574701d58))

### Documentation

- Add a comprehensive architectural overview, update documentation structure, and refine the GitLab CI template. ([194d574](https://github.com/trivoallan/regis-cli/commit/194d5744a5bf45f316f757bcce05aa0e5cc4047e))
- add documentation for the default playbook, detailing its rules and report organization, and link it in the navigation. ([e67daab](https://github.com/trivoallan/regis-cli/commit/e67daabd9cb32faa2672a0deae48d0e7d95482d8))
- Add new example report assets and update documentation pages. ([a247d93](https://github.com/trivoallan/regis-cli/commit/a247d93417d32419e3cc89b1c944a4318a618b93))
- **commitmessages:** add Google Blockly commit style guide link ([8c61162](https://github.com/trivoallan/regis-cli/commit/8c611621d59b4600f0cfcea2d6970387b40ccb2c))
- Enhance GitHub Actions and GitLab CI integration guides with comprehensive examples, CI metadata, and deployment to respective pages services. ([3ae83e5](https://github.com/trivoallan/regis-cli/commit/3ae83e54fc89f8254602687afe4871cf379a4296))
- enhance Python, CI/CD, commit message, and documentation rules with new tools, scope definitions, and process clarifications. ([6f1d111](https://github.com/trivoallan/regis-cli/commit/6f1d11119d40d556b0a0bff7c963939b49f6421a))
- **gitlab-workflow:** add section on GitLab Review Apps for Premium/Ultimate tiers with CI/CD configuration example ([c919743](https://github.com/trivoallan/regis-cli/commit/c91974304d212da4f55139ba9124c3fa73336e25))
- **rules:** add commit message guidelines and refine CI/CD semantic versioning and conventional commit references. ([376c16e](https://github.com/trivoallan/regis-cli/commit/376c16eb2ac1cd1d9f5c47dfb51bf6c1eaabaeb5))
- **ui:** enable mermaid diagram rendering ([8edd450](https://github.com/trivoallan/regis-cli/commit/8edd4505f23d26cbb34441e8f5424ee481558c1b))
- **ui:** use correct mermaid extension package ([c622961](https://github.com/trivoallan/regis-cli/commit/c6229618d30d9629194ab74fe8a21b383f2e6cc1))
- **ui:** use correct mermaid extension package in playbook ([e7fed19](https://github.com/trivoallan/regis-cli/commit/e7fed19ea0f9dbc7c30d1dff9a05a2831fbbcb94))
- Update TIP block formatting in playbooks and add documentation versioning and CLI control to notes. ([544e51c](https://github.com/trivoallan/regis-cli/commit/544e51ca75c2dcb9430009d6b859921caeb30715))

## [0.6.0](https://github.com/trivoallan/regis-cli/compare/regis-cli-v0.5.0...regis-cli-v0.6.0) (2026-02-21)

### Features

- add --cache option to the analyze command to load and use an existing report.json, skipping re-analysis. ([3a7a710](https://github.com/trivoallan/regis-cli/commit/3a7a710c9329e4f5d812804044bf8bb190b9f416))
- add `--theme` option for HTML report generation and ignore the `/reports` directory ([8bb9e7b](https://github.com/trivoallan/regis-cli/commit/8bb9e7bec6268d5219d37818f0177846cc6aa81f))
- add Dockerfile and GitHub Actions workflow for building and publishing regis-cli Docker images. ([dfc66c6](https://github.com/trivoallan/regis-cli/commit/dfc66c6d6231748e5a893f6b38f4caba4c3be69b))
- add domain-trusted scorecard ([41ca994](https://github.com/trivoallan/regis-cli/commit/41ca994967acca90e4d410acae5a6317f97c4f9f))
- Add extensive test coverage for analyzers and core components, integrate Ruff linter, and refine Skopeo schema. ([ec215e0](https://github.com/trivoallan/regis-cli/commit/ec215e0bedb0adafda66ddfa57b01eb39e17e164))
- add GitHub Actions workflows for Super-Linter and automated releases. ([d8c8a28](https://github.com/trivoallan/regis-cli/commit/d8c8a282afdd1a5959ed8cc3b4f08daf3b54a65b))
- Add Hadolint analyzer to lint Dockerfiles and display results. ([b8802cb](https://github.com/trivoallan/regis-cli/commit/b8802cb29cee41ab08d70c87945d3265cdc505ca))
- Add initial HTML report for image health scores generated by regis-cli. ([419c65a](https://github.com/trivoallan/regis-cli/commit/419c65a8583704ec9e3d28dbd7448901c3374663))
- add Skopeo analyzer and refactor versioning analyzer to use Skopeo for tag listing. ([b933931](https://github.com/trivoallan/regis-cli/commit/b9339312aae5a1a3c42aabb7347bfa71f99436a0))
- add support for multiple output formats and templated output paths for the `run` command. ([6a70c93](https://github.com/trivoallan/regis-cli/commit/6a70c93d842609a4d091f413acc4f8aa0de94238))
- add support for passing metadata via CLI to reports and update report schema. ([07050ea](https://github.com/trivoallan/regis-cli/commit/07050ea6ceb8bc5e3c19d1c22f5249db1b9531dc))
- add support for templated links in scorecards and reports ([bc191af](https://github.com/trivoallan/regis-cli/commit/bc191afb2c8fad75dde499531533f35abf691fb7))
- add time formatting and recursive metadata rendering to improve report request details display. ([f86862e](https://github.com/trivoallan/regis-cli/commit/f86862e7289083562ad348dd0a4ac96127d64f8b))
- Add user and digest extraction and display to Skopeo image analysis. ([4cbacba](https://github.com/trivoallan/regis-cli/commit/4cbacba1b3e1ef3e4ce066dfaf32280884b25693))
- add variant detection and reporting to the versioning analyzer ([8c61394](https://github.com/trivoallan/regis-cli/commit/8c613946148fbd8d095de1ebc1bb27269b6532b8))
- **analyzers:** Enable private registry authentication for Trivy-based analyzers and update documentation. ([06c35eb](https://github.com/trivoallan/regis-cli/commit/06c35eb80a95a94846c29154ff658861c0331d5f))
- **ci:** introduce GitLab CI workflow for image analysis with MR-driven triggers and review app deployments. ([d85449d](https://github.com/trivoallan/regis-cli/commit/d85449d19e9e6cb6232b72cb5940e297c4608261))
- **cli:** Implement `generate` command with `cookiecutter` for project scaffolding and update project templates. ([44bfdf6](https://github.com/trivoallan/regis-cli/commit/44bfdf6e87070d4515ac685d43b1bf1d0974f948))
- **cli:** Implement a CLI version command, refactor `importlib.metadata` imports, and update tests and GitLab CI artifact handling. ([d508b53](https://github.com/trivoallan/regis-cli/commit/d508b53f72bf9396f060663fc1262ccc4e62a292))
- configure Antora Mermaid extension with a specific library URL and script stem. ([190fcc4](https://github.com/trivoallan/regis-cli/commit/190fcc49632bc50a466a2c56b8bcaf8d5ae6937d))
- **cookiecutter:** integrate GitHub Actions metadata into analysis reports for improved traceability and remove unused scorecard levels. ([4113efb](https://github.com/trivoallan/regis-cli/commit/4113efbecb2a92497c1de451b4efc09feee96934))
- **cookiecutter:** introduce Cookiecutter template for bootstrapping new image analysis projects with documentation, workflows, and default scorecards. ([391d74f](https://github.com/trivoallan/regis-cli/commit/391d74fa53f45e93dbb2204104a7a1869f70ad03))
- **cookiecutter:** Introduce Cookiecutter template for project bootstrapping and add its comprehensive usage guide, refining the template's analysis workflow input. ([9ef6351](https://github.com/trivoallan/regis-cli/commit/9ef6351574929e9f217c5c1eae2fae597cf3286e))
- display structured analyzer errors in the UI and store them in reports. ([f3dd654](https://github.com/trivoallan/regis-cli/commit/f3dd654fd8533147fef78550d72126ca3bd1a1d3))
- **doc:** Add 'Get Started' and 'Understand Playbooks' documentation pages and update navigation. ([e791354](https://github.com/trivoallan/regis-cli/commit/e791354736aad353c06c60189e040bd9f61c0f48))
- **docs:** initialize Antora documentation ([6ca4154](https://github.com/trivoallan/regis-cli/commit/6ca41541c17a0a942d8407c6256a59004d26805c))
- dynamically set cookiecutter image URL and simplify release-please extra-files configuration. ([b86853a](https://github.com/trivoallan/regis-cli/commit/b86853a7f9a7b032a1171e5ff7e9dbbe724c6fbf))
- embed regis-cli version in analysis reports and update cookiecutter image URLs. ([3ab5430](https://github.com/trivoallan/regis-cli/commit/3ab543048e4972ff9ec6c461f710c93991ad8924))
- enhance default playbook overview with new recommendation and compliance widgets and update widget styling. ([6737a68](https://github.com/trivoallan/regis-cli/commit/6737a6839152fea82141eda59241792cb5a59985))
- enhance registry credential resolution by normalizing Docker Hub aliases and remove the `score.html` report file. ([c2dd0e1](https://github.com/trivoallan/regis-cli/commit/c2dd0e17ab0810a247df8148d0c10f5ccf3ef682))
- enhance report output with per-scorecard HTML files, `slug` support, and improved file writing logic. ([895c46b](https://github.com/trivoallan/regis-cli/commit/895c46bbc98d8fe650ed3a657eb98b415abb4266))
- Enhance scorecard rule evaluation to track missing data, provide detailed condition stringification, and include rule tags in results and UI. ([cd94912](https://github.com/trivoallan/regis-cli/commit/cd949129cd65c20584c6a258c765bc8b4a378e34))
- enhance Trivy report display for multiple targets and refine report layout with dedicated sections for links and scorecards. ([9a29bad](https://github.com/trivoallan/regis-cli/commit/9a29bad85018b3fa93bf49ce4b204d99e1cca374))
- Implement conditional widget rendering, add new widget styling options including alignment and subvalues, and introduce new CSS for recommendations and header elements. ([78ade17](https://github.com/trivoallan/regis-cli/commit/78ade17344380013a2429d8bf519728d7d346415))
- implement flexible registry credential resolution via new `--auth` CLI option and dedicated module ([ac5afb3](https://github.com/trivoallan/regis-cli/commit/ac5afb33639d018d4d04611777c95b194f11d6dc))
- implement registry authentication using environment variables and add new tests. ([1894969](https://github.com/trivoallan/regis-cli/commit/18949692ac8c493f3ea62d0485efea75661e38e3))
- initialize regis-cli project with image analysis, scorecard engine, schema validation, and comprehensive project setup. ([3af2207](https://github.com/trivoallan/regis-cli/commit/3af2207ef86d5265c7fc32997219b3841172b0bb))
- Integrate scorecard evaluation directly into the `analyze` command, supporting multiple custom scorecards, and remove the dedicated `score` command. ([8301c36](https://github.com/trivoallan/regis-cli/commit/8301c36f77c897057a44b03abaeaf525067a4163))
- introduce new HTML report structure and styling with updated templates and CSS. ([94f5130](https://github.com/trivoallan/regis-cli/commit/94f5130d1c7dd0e0ad34098de757242e5d81a37b))
- Introduce OpenSSF Scorecard, Freshness, and Popularity analyzer reports with supporting configuration and robustness improvements. ([df311cc](https://github.com/trivoallan/regis-cli/commit/df311ccc38bb6c99c6c0ad0eaa9fd77fd21f49a0))
- introduce SBOM analysis using Trivy and CycloneDX, replacing the license analyzer. ([8fa1d24](https://github.com/trivoallan/regis-cli/commit/8fa1d24166324d4224287250b3456db7251924e2))
- introduce scorecard pages to group sections and add new size and versioning analyzers. ([2dd6b31](https://github.com/trivoallan/regis-cli/commit/2dd6b315c41cc440d57b349187acaa8e1a783b5b))
- Introduce section-based scorecards with a new schema and remove the dependency analyzer. ([e7adbea](https://github.com/trivoallan/regis-cli/commit/e7adbeab5a8404a2b983be5dad715b3f310f66fa))
- **playbooks:** Add support for loading playbooks from remote URLs and update cookiecutters to utilize this feature. ([69ef82f](https://github.com/trivoallan/regis-cli/commit/69ef82f57b4704135c0f3a4809a11be5294aa19b))
- refactor cookiecutter templates to support both GitHub and GitLab platforms with dedicated CI configurations and documentation. ([295db88](https://github.com/trivoallan/regis-cli/commit/295db881cd1b2eae17f595d567fe182fef087623))
- Refine scorecard reporting by updating schemas, engine logic, templates, and removing old report files. ([f3abf1f](https://github.com/trivoallan/regis-cli/commit/f3abf1f9a94faa638039bc959566315acf014b8f))
- render error cards for all unhandled analyzer errors in the report ([9bf27db](https://github.com/trivoallan/regis-cli/commit/9bf27db38e8bc9a542f286aa7638dc92e19be87e))
- replace single achieved level with a detailed summary by level in scorecard results, CLI output, and HTML report. ([c81c2ce](https://github.com/trivoallan/regis-cli/commit/c81c2ce854c25896765c2e9938361b02569c005e))
- **report:** Embed regis-cli version into analysis reports and schema ([ac3efb5](https://github.com/trivoallan/regis-cli/commit/ac3efb55d70263c5417c02df59522201e7ca501e))
- **reports:** Implement automatic versioning of analysis reports in GitLab CI and document its configuration. ([c985942](https://github.com/trivoallan/regis-cli/commit/c9859427c88ce06ae0cde3a64566fe6dc961a788))
- **review:** enhance GitLab CI report delivery by committing to `reports/`, posting direct links to MR comments, and updating documentation. ([d934913](https://github.com/trivoallan/regis-cli/commit/d934913c7451a9565ce3f8a2626ae3b54f24002a))
- **review:** enhance GitLab CI/CD to specify output filename, run site generation on the default branch, and dynamically configure Pages deployments for review apps and main branch, while updating the project backlog. ([342d0b8](https://github.com/trivoallan/regis-cli/commit/342d0b86d4b9111f5dc4d43a680c53ec4af7a335))
- **review:** Expose analysis reports as Merge Request artifacts instead of deploying to Review Apps and update documentation accordingly. ([c4850be](https://github.com/trivoallan/regis-cli/commit/c4850be3bbd6548d6d854529a59f2353bbc595b5))
- **review:** Implement and document a self-service analysis workflow in GitLab CI, including optional report commits to the branch and dynamic Review App links. ([016659d](https://github.com/trivoallan/regis-cli/commit/016659d34cf87e68b1af8e68e4806372c923979a))
- **review:** Introduce automated GitLab MR labeling and conditional playbook links based on analysis outcomes. ([86e5986](https://github.com/trivoallan/regis-cli/commit/86e59862895324ebb6276d31b94b99ec53f432bf))
- **review:** use GitLab API for merge request creation to enable setting reviewers and assignees, and add `curl` dependency. ([32f98f2](https://github.com/trivoallan/regis-cli/commit/32f98f226263ed577fd649743af69f0f7f2eff85))
- set default output directory template to include the tag. ([157f425](https://github.com/trivoallan/regis-cli/commit/157f425cca42a71afb089dd4fff6d1944abf9c95))
- Track and display involved data analyzers for scorecard rule evaluations in the schema, engine, and HTML report. ([42bcace](https://github.com/trivoallan/regis-cli/commit/42bcace830ae4aebb83b23c17486c79c867fc61d))
- **ui:** Implement a new report rendering engine with a sidebar layout and dedicated pages for various analysis results. ([e1faaf9](https://github.com/trivoallan/regis-cli/commit/e1faaf92dadc215bbcdfecf90d164b5a2658ad64))
- **ui:** Introduce new analyzer display templates and enhance the playbook engine to support section widgets. ([b998f63](https://github.com/trivoallan/regis-cli/commit/b998f63f50691a9a186ba83b1a3ebe42cb21751e))

### Bug Fixes

- **analyzers:** Expose analyzer results at the root of the scorecard evaluation context and update default Trivy rules. ([460871b](https://github.com/trivoallan/regis-cli/commit/460871ba19698bfff3b33f40183f742501d80045))
- **analyzers:** prevent Skopeo analyzer from failing on index image inspection and formalize commit message guidelines. ([c80f88c](https://github.com/trivoallan/regis-cli/commit/c80f88c0dc4dcefa2610c959812d8232649629a3))
- **build:** install git in Dockerfile ([dfffabd](https://github.com/trivoallan/regis-cli/commit/dfffabd778a1fbbe8d371f2d8713f95568427d04))
- **ci:** add workflow_dispatch trigger and refine tag matching for Docker publish workflow. ([21b7549](https://github.com/trivoallan/regis-cli/commit/21b754967ad212cea23c0a13d623ce06902c0058))
- **ci:** configure releaser-pleaser action with release token ([ed8a1f2](https://github.com/trivoallan/regis-cli/commit/ed8a1f2ff386d0f54b91b4b2cde3c07b770c73aa))
- **docker:** address permission denied errors in Docker by setting user UID/GID, ensuring directory writability, and adding a report output fallback. ([ddaba2c](https://github.com/trivoallan/regis-cli/commit/ddaba2ceb4c931fca1f68555e63e6408a32baec6))
- **docker:** Resolve Docker container permission issues by creating a home directory for the `regis` user and setting report directory permissions, and update the analysis workflow. ([9cf4087](https://github.com/trivoallan/regis-cli/commit/9cf408788e2923524da428b0eb19f2eb90f763bf))
- Prevent `AttributeError` in scorecard link processing by adding type checks and update `regis-cli` workflow flags to long form. ([a02caa3](https://github.com/trivoallan/regis-cli/commit/a02caa33bb8fc47fbed119bdd797ad84eeb7cdc0))

### Dependencies

- Populate Pipfile.lock with resolved dependency versions. ([e87ee2c](https://github.com/trivoallan/regis-cli/commit/e87ee2cd971b4d35c8cf4ccbf1ad5ee574701d58))

### Documentation

- Add a comprehensive architectural overview, update documentation structure, and refine the GitLab CI template. ([194d574](https://github.com/trivoallan/regis-cli/commit/194d5744a5bf45f316f757bcce05aa0e5cc4047e))
- add documentation for the default playbook, detailing its rules and report organization, and link it in the navigation. ([e67daab](https://github.com/trivoallan/regis-cli/commit/e67daabd9cb32faa2672a0deae48d0e7d95482d8))
- Add new example report assets and update documentation pages. ([a247d93](https://github.com/trivoallan/regis-cli/commit/a247d93417d32419e3cc89b1c944a4318a618b93))
- **commitmessages:** add Google Blockly commit style guide link ([8c61162](https://github.com/trivoallan/regis-cli/commit/8c611621d59b4600f0cfcea2d6970387b40ccb2c))
- Enhance GitHub Actions and GitLab CI integration guides with comprehensive examples, CI metadata, and deployment to respective pages services. ([3ae83e5](https://github.com/trivoallan/regis-cli/commit/3ae83e54fc89f8254602687afe4871cf379a4296))
- enhance Python, CI/CD, commit message, and documentation rules with new tools, scope definitions, and process clarifications. ([6f1d111](https://github.com/trivoallan/regis-cli/commit/6f1d11119d40d556b0a0bff7c963939b49f6421a))
- **gitlab-workflow:** add section on GitLab Review Apps for Premium/Ultimate tiers with CI/CD configuration example ([c919743](https://github.com/trivoallan/regis-cli/commit/c91974304d212da4f55139ba9124c3fa73336e25))
- **rules:** add commit message guidelines and refine CI/CD semantic versioning and conventional commit references. ([376c16e](https://github.com/trivoallan/regis-cli/commit/376c16eb2ac1cd1d9f5c47dfb51bf6c1eaabaeb5))
- **ui:** enable mermaid diagram rendering ([8edd450](https://github.com/trivoallan/regis-cli/commit/8edd4505f23d26cbb34441e8f5424ee481558c1b))
- **ui:** use correct mermaid extension package ([c622961](https://github.com/trivoallan/regis-cli/commit/c6229618d30d9629194ab74fe8a21b383f2e6cc1))
- **ui:** use correct mermaid extension package in playbook ([e7fed19](https://github.com/trivoallan/regis-cli/commit/e7fed19ea0f9dbc7c30d1dff9a05a2831fbbcb94))
- Update TIP block formatting in playbooks and add documentation versioning and CLI control to notes. ([544e51c](https://github.com/trivoallan/regis-cli/commit/544e51ca75c2dcb9430009d6b859921caeb30715))

## [v0.5.0](https://github.com/trivoallan/regis-cli/releases/tag/v0.5.0)

### Features

- embed regis-cli version in analysis reports and update cookiecutter image URLs.
- **report**: Embed regis-cli version into analysis reports and schema
- **playbooks**: Add support for loading playbooks from remote URLs and update cookiecutters to utilize this feature.
- **reports**: Implement automatic versioning of analysis reports in GitLab CI and document its configuration.
- **cli**: Implement `generate` command with `cookiecutter` for project scaffolding and update project templates.
- **ci**: introduce GitLab CI workflow for image analysis with MR-driven triggers and review app deployments.
- **cli**: Implement a CLI version command, refactor `importlib.metadata` imports, and update tests and GitLab CI artifact handling.

## [v0.4.0](https://github.com/trivoallan/regis-cli/releases/tag/v0.4.0)

### Features

- add time formatting and recursive metadata rendering to improve report request details display.
- refactor cookiecutter templates to support both GitHub and GitLab platforms with dedicated CI configurations and documentation.

## [v0.3.0](https://github.com/trivoallan/regis-cli/releases/tag/v0.3.0)

### Features

- **analyzers**: Enable private registry authentication for Trivy-based analyzers and update documentation.

### Bug Fixes

- **build**: install git in Dockerfile

## [v0.2.2](https://github.com/trivoallan/regis-cli/releases/tag/v0.2.2)

### Bug Fixes

- **ci**: configure releaser-pleaser action with release token

## [v0.2.1](https://github.com/trivoallan/regis-cli/releases/tag/v0.2.1)

### Bug Fixes

- **ci**: add workflow_dispatch trigger and refine tag matching for Docker publish workflow.

## [v0.2.0](https://github.com/trivoallan/regis-cli/releases/tag/v0.2.0)

### Features

- **cookiecutter**: introduce Cookiecutter template for bootstrapping new image analysis projects with documentation, workflows, and default scorecards.
- **cookiecutter**: Introduce Cookiecutter template for project bootstrapping and add its comprehensive usage guide, refining the template's analysis workflow input.
- **cookiecutter**: integrate GitHub Actions metadata into analysis reports for improved traceability and remove unused scorecard levels.
- enhance report output with per-scorecard HTML files, `slug` support, and improved file writing logic.
- Refine scorecard reporting by updating schemas, engine logic, templates, and removing old report files.
- **ui**: Introduce new analyzer display templates and enhance the playbook engine to support section widgets.
- **ui**: Implement a new report rendering engine with a sidebar layout and dedicated pages for various analysis results.
- Implement conditional widget rendering, add new widget styling options including alignment and subvalues, and introduce new CSS for recommendations and header elements.
- enhance default playbook overview with new recommendation and compliance widgets and update widget styling.

### Bug Fixes

- **docker**: Resolve Docker container permission issues by creating a home directory for the `regis` user and setting report directory permissions, and update the analysis workflow.
- **docker**: address permission denied errors in Docker by setting user UID/GID, ensuring directory writability, and adding a report output fallback.
- **analyzers**: Expose analyzer results at the root of the scorecard evaluation context and update default Trivy rules.
- Prevent `AttributeError` in scorecard link processing by adding type checks and update `regis-cli` workflow flags to long form.

## [v0.1.0](https://github.com/trivoallan/regis-cli/releases/tag/v0.1.0)

### Features

- **docs**: initialize Antora documentation
- add Dockerfile and GitHub Actions workflow for building and publishing regis-cli Docker images.
- add GitHub Actions workflows for Super-Linter and automated releases.
- add --cache option to the analyze command to load and use an existing report.json, skipping re-analysis.
- Add user and digest extraction and display to Skopeo image analysis.
- add Skopeo analyzer and refactor versioning analyzer to use Skopeo for tag listing.
- Add Hadolint analyzer to lint Dockerfiles and display results.
- introduce scorecard pages to group sections and add new size and versioning analyzers.
- enhance Trivy report display for multiple targets and refine report layout with dedicated sections for links and scorecards.
- add support for templated links in scorecards and reports
- introduce SBOM analysis using Trivy and CycloneDX, replacing the license analyzer.
- Introduce section-based scorecards with a new schema and remove the dependency analyzer.
- Introduce OpenSSF Scorecard, Freshness, and Popularity analyzer reports with supporting configuration and robustness improvements.
- render error cards for all unhandled analyzer errors in the report
- add `--theme` option for HTML report generation and ignore the `/reports` directory
- set default output directory template to include the tag.
- replace single achieved level with a detailed summary by level in scorecard results, CLI output, and HTML report.
- display structured analyzer errors in the UI and store them in reports.
- Track and display involved data analyzers for scorecard rule evaluations in the schema, engine, and HTML report.
- add support for multiple output formats and templated output paths for the `run` command.
- introduce new HTML report structure and styling with updated templates and CSS.
- Integrate scorecard evaluation directly into the `analyze` command, supporting multiple custom scorecards, and remove the dedicated `score` command.
- Enhance scorecard rule evaluation to track missing data, provide detailed condition stringification, and include rule tags in results and UI.
- enhance registry credential resolution by normalizing Docker Hub aliases and remove the `score.html` report file.
- implement flexible registry credential resolution via new `--auth` CLI option and dedicated module
- add support for passing metadata via CLI to reports and update report schema.
- Add initial HTML report for image health scores generated by regis-cli.
- add variant detection and reporting to the versioning analyzer
- add domain-trusted scorecard
- implement registry authentication using environment variables and add new tests.
- initialize regis-cli project with image analysis, scorecard engine, schema validation, and comprehensive project setup.

### Bug Fixes

- **analyzers**: prevent Skopeo analyzer from failing on index image inspection and formalize commit message guidelines.
