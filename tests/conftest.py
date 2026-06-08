"""Shared pytest fixtures.

Network guard for Cookiecutter:

``regis analyze`` renders the playbook's presentation templates via
Cookiecutter. The default playbook surfaces a *packaged* (local) template, so
no test should ever clone a remote one. If a repository URL slips back into a
playbook, Cookiecutter would ``git clone`` it — which hangs for ~25s per test
on CI runners (cold cache, slow/blocked egress) and silently inflated the
``pytest`` job to ~10 minutes. Fail fast and loudly instead.
"""

import cookiecutter.main as _cc_main
import cookiecutter.repository as _cc_repo
import pytest

from tests import _per_file_coverage


@pytest.fixture(autouse=True)
def block_remote_cookiecutter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject remote Cookiecutter templates; allow packaged/local ones."""
    real = _cc_main.cookiecutter

    def _guard(template, *args, **kwargs):  # type: ignore[no-untyped-def]
        if _cc_repo.is_repo_url(str(template)):
            raise RuntimeError(
                "Test attempted to clone a remote Cookiecutter template "
                f"({template!r}). Use a packaged/local template instead "
                "(see tests/conftest.py)."
            )
        return real(template, *args, **kwargs)

    monkeypatch.setattr(_cc_main, "cookiecutter", _guard)


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session: pytest.Session):
    """Run the per-file coverage gate after pytest-cov writes its data."""
    yield
    _per_file_coverage.enforce(session)
