# Suggested Commands for regis

## Development

- `uv sync` — Install all dependencies (incl. dev group)
- `uv run pytest` — Run tests with coverage (fails if < 90%)
- `uv run pytest --no-cov` — Run tests without coverage check
- `uv run ruff check .` — Lint
- `uv run ruff format .` — Format
- `uv run regis --help` — Run CLI locally

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
