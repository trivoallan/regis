"""RegistryImageInspector delegates to RegistryClient and translates errors."""

from unittest.mock import create_autospec

import pytest

from regis.adapters.driven.registry.image_inspector import RegistryImageInspector
from regis.core.domain.errors import RegistryError
from regis.core.ports.image_inspector import ImageInspector
from regis.registry.client import RegistryClient
from regis.registry.client import RegistryError as ClientRegistryError


def _inspector() -> tuple[RegistryImageInspector, RegistryClient]:
    client = create_autospec(RegistryClient, instance=True)
    return RegistryImageInspector(client), client


def test_is_an_image_inspector() -> None:
    inspector, _ = _inspector()
    assert isinstance(inspector, ImageInspector)


def test_delegates_each_method() -> None:
    inspector, client = _inspector()
    client.list_tags.return_value = ["1.27"]
    client.get_manifest.return_value = {"schemaVersion": 2}
    client.get_blob.return_value = {"config": {}}
    client.get_digest.return_value = "sha256:abc"

    assert inspector.list_tags() == ["1.27"]
    assert inspector.get_manifest("1.27") == {"schemaVersion": 2}
    assert inspector.get_blob("sha256:abc") == {"config": {}}
    assert inspector.get_digest("1.27") == "sha256:abc"
    client.get_manifest.assert_called_once_with("1.27")
    client.get_blob.assert_called_once_with("sha256:abc")
    client.get_digest.assert_called_once_with("1.27")


def test_translates_legacy_registry_error() -> None:
    # One method suffices — all four share the same contextmanager.
    inspector, client = _inspector()
    client.list_tags.side_effect = ClientRegistryError("boom")
    with pytest.raises(RegistryError) as exc_info:
        inspector.list_tags()
    assert "boom" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, ClientRegistryError)
