"""Presentation-template rendering must stay local (no remote clone).

Regression coverage for the CI slowdown where the default playbook referenced
the regis repo by git URL, so every ``regis analyze`` cloned the whole repo
(~25s per test on CI). Templates are now resolved from the installed package.
"""

from importlib import resources
from pathlib import Path

import cookiecutter.main as _cc_main
import cookiecutter.repository as _cc_repo
import pytest
import yaml

from regis.utils.report import render_presentation_templates


def test_packaged_template_resolved_to_local_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``package`` template is passed to Cookiecutter as a local path, never cloned."""
    seen: list[str] = []
    monkeypatch.setattr(
        _cc_main, "cookiecutter", lambda template, **kw: seen.append(str(template))
    )

    report = {
        "request": {
            "registry": "registry-1.docker.io",
            "repository": "library/nginx",
            "tag": "latest",
            "digest": "latest",
        },
        "playbooks": [
            {
                "templates": [
                    {"package": "regis", "directory": "cookiecutters/mr-evidence"}
                ]
            }
        ],
    }

    render_presentation_templates(report, str(tmp_path))

    assert len(seen) == 1, "expected exactly one template render"
    template_arg = seen[0]
    assert not _cc_repo.is_repo_url(
        template_arg
    ), f"packaged template must resolve to a local path, got a repo URL: {template_arg!r}"
    assert template_arg.endswith("cookiecutters/mr-evidence")
    assert Path(template_arg).is_dir()


def test_default_playbook_templates_are_packaged() -> None:
    """The shipped default playbook must not clone a remote template."""
    pb_path = resources.files("regis") / "playbooks" / "default" / "playbook.yaml"
    playbook = yaml.safe_load(pb_path.read_text(encoding="utf-8"))
    templates = playbook["spec"]["presentation"].get("templates", [])
    assert templates, "default playbook should surface at least one template"
    for tmpl in templates:
        assert "url" not in tmpl, (
            f"default playbook template uses a remote url ({tmpl.get('url')!r}); "
            "use a packaged template to avoid a git clone on every analyze"
        )
        assert tmpl.get("package"), "expected a packaged template reference"
