"""The legacy registry RegistryError must be a core RegistryError subtype.

Lets the hexagonal core (which may not import regis.adapters.driven.registry) catch
legacy-branch registry failures by their core type during the P3 bridge.
"""

from regis.adapters.driven.registry.client import RegistryError as LegacyRegistryError
from regis.core.domain.errors import RegisError
from regis.core.domain.errors import RegistryError as CoreRegistryError


def test_legacy_registry_error_is_core_registry_error():
    assert issubclass(LegacyRegistryError, CoreRegistryError)


def test_legacy_registry_error_instance_caught_as_core():
    try:
        raise LegacyRegistryError("boom")
    except CoreRegistryError as exc:
        assert str(exc) == "boom"


def test_legacy_registry_error_still_an_exception():
    assert issubclass(LegacyRegistryError, RegisError)
    assert issubclass(LegacyRegistryError, Exception)
