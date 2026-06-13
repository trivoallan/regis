"""Core value objects."""

import dataclasses

import pytest

from regis.core.model.image_reference import ImageReference
from regis.core.model.report import Report


def test_image_reference_is_frozen_and_equal() -> None:
    a = ImageReference(registry="docker.io", repository="library/nginx", tag="1.27")
    b = ImageReference(registry="docker.io", repository="library/nginx", tag="1.27")
    assert a == b
    assert a.platform is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.tag = "1.28"  # type: ignore[misc]


def test_report_exposes_schema_version() -> None:
    assert Report(payload={"schemaVersion": 2, "results": {}}).schema_version == 2
    assert Report(payload={"schemaVersion": 0}).schema_version == 0
    assert Report(payload={}).schema_version is None
    # Non-integer values are rejected by the int-guard.
    assert Report(payload={"schemaVersion": "2"}).schema_version is None
    assert Report(payload={"schemaVersion": 2.0}).schema_version is None
