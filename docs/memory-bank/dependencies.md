# Dependencies

## Core Dependencies

| Package           | Version   | Purpose                        |
| ----------------- | --------- | ------------------------------ |
| click             | >=8.1     | CLI framework                  |
| requests          | >=2.32.2  | HTTP client                    |
| jsonschema        | >=4.20    | Schema validation              |
| semver            | >=3.0     | Version parsing and comparison |
| json-logic-qubit  | >=0.9     | Policy rule evaluation         |
| pyyaml            | >=6.0     | YAML parsing                   |
| jinja2            | >=3.1     | Template rendering             |
| cookiecutter      | >=2.5     | Scaffolding                    |
| referencing       | <0.37.0   | JSON schema references         |
| python-gitlab     | >=4.4.0   | GitLab integration             |
| fastapi           | >=0.115.0 | API/server support             |
| uvicorn[standard] | >=0.34    | ASGI server                    |

## Dev Dependencies

| Package            | Version | Purpose                                       |
| ------------------ | ------- | --------------------------------------------- |
| pytest             | >=7.4   | Test runner                                   |
| pytest-cov         | >=4.1   | Coverage reporting                            |
| responses          | >=0.24  | HTTP mocking                                  |
| genbadge[coverage] | >=1.1   | Coverage badge generation                     |
| httpx              | >=0.28  | HTTP client/testing                           |
| ruff               | \*      | Linting and formatting (dev dependency group) |
| jsonschema2md      | \*      | Docs generation helper                        |
| types-PyYAML       | \*      | Typing support                                |
| types-requests     | \*      | Typing support                                |
| types-jsonschema   | \*      | Typing support                                |

## Version Constraints

- Python project metadata targets `>=3.10`
- `.python-version` pins Python 3.13 for the local environment (uv)
- `referencing` is pinned below `0.37.0`
- PNPM overrides pin `serialize-javascript` and constrain `webpack`

## Upgrade Notes

- Keep `referencing` compatibility in mind when updating `jsonschema`
- Validate analyzer integrations after dependency changes
- Re-check CI workflow behavior after toolchain upgrades

## Internal Dependencies

- `regis` package is installed editable in the local environment by `uv sync`
- `regis.analyzers` entry points wire analyzer modules into the CLI
