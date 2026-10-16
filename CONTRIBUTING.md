# Contributing

Contributions are welcome. By submitting one, you agree that it is licensed under the
Apache License 2.0, as section 5 of the [LICENSE](LICENSE) states. No CLA or sign-off is required.

## Before you open a pull request

- Run `make lint test security` locally. The CI runs the same targets.
- Title the pull request with [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat: …`, `fix(cli): …`). The title becomes the squashed commit, and it drives the
  version and the changelog.
- Report vulnerabilities privately: see [SECURITY.md](SECURITY.md).

Conventions and architecture notes for this repository are in [CLAUDE.md](CLAUDE.md).
