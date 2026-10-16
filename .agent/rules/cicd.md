---
trigger: always_on
---

# CI / CD

- Use Github Actions and [Release Please](https://github.com/googleapis/release-please)
- Github project configuration as code in `.github/settings.json`, applied by `.github/apply-settings.sh` (`make settings`)
- [Semantic Versioning](https://semver.org/).
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
- CI only calls the common `make` targets (`lint`, `test`, `security`, `image`); always check their results in PRs
- Do not manually edit Release Please PRs unless necessary
