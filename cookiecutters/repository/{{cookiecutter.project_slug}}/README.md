# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Getting Started

To run the analysis locally using the `regis-cli` Docker image:

```bash
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/playbooks:/app/playbooks \
  {{ cookiecutter.regis_cli_image_url }} \
  analyze {{ cookiecutter.regis_cli_image_url }} \
  -p playbooks/default.yaml \
  --site
```

{% if cookiecutter.platform == "github" -%}
## GitHub Actions

The analysis is automatically performed on `workflow_dispatch`. Reports are published to GitHub Pages.
{%- endif %}

{% if cookiecutter.platform == "gitlab" -%}
## GitLab CI

The analysis is automatically performed on web triggers. Reports are published to GitLab Pages.
{%- endif %}
