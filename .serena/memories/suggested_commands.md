# Suggested Commands for regis

## Development

- `pipenv install --dev` — Install all dependencies
- `pipenv run pytest` — Run tests with coverage (fails if < 90%)
- `pipenv run pytest --no-cov` — Run tests without coverage check
- `pipenv run ruff check .` — Lint
- `pipenv run ruff format .` — Format
- `pipenv run regis --help` — Run CLI locally

## Linting / Formatting

- `trunk check` — Run trunk check
- `trunk check --fix` — Fix issues
- `trunk check --fix --all` — Fix issues in all files

## Git

- `git status`, `git diff`, `git log --oneline` — Standard git utils
- PRs are mandatory for main (feature/\* branches)
- Conventional Commits with mandatory scopes

## System (Darwin/macOS)

- Standard unix: `ls`, `grep`, `find`, `cat`, `sed`, etc.
