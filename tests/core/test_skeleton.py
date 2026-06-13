"""The hexagonal skeleton packages must be importable."""

import importlib

import pytest

PACKAGES = [
    "regis.core",
    "regis.core.domain",
    "regis.core.application",
    "regis.core.ports",
    "regis.adapters",
    "regis.adapters.driving",
    "regis.adapters.driven",
]


@pytest.mark.parametrize("name", PACKAGES)
def test_skeleton_package_importable(name: str) -> None:
    # import_module raises ModuleNotFoundError if the package is missing;
    # a clean return is the success condition.
    importlib.import_module(name)
