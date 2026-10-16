# Suggested Commands for regis

## Development

- `uv sync` — Install all dependencies (incl. dev group)
- `make lint` — ruff, mypy, import-linter, docs/reference up to date
- `make test` — Run tests with coverage (fails if total or any file < 90%)
- `make security` — pip-audit, blocking from HIGH
- `make image` — Build and smoke-test both image variants
- `make reference` — Regenerate docs/reference (commit the result)
- `uv run python -m pytest --no-cov` — Fast test loop without coverage gates
- `uv run ruff format .` — Format
- `uv run regis --help` — Run CLI locally

## Git

- `git status`, `git diff`, `git log --oneline` — Standard git utils
- PRs are mandatory for main (feature/\* branches)
- Conventional Commits with mandatory scopes

## System (Darwin/macOS)

- Standard unix: `ls`, `grep`, `find`, `cat`, `sed`, etc.
