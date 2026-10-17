"""RegistryClient.get_referrers: Referrers API first, sha256-<hex> fallback tag next."""

from __future__ import annotations

from typing import Any

import pytest

from regis.adapters.driven.registry.client import RegistryClient, RegistryError

_DIGEST = "sha256:abc"
_API = "https://ghcr.io/v2/o/r/referrers/sha256:abc"
_TAG = "https://ghcr.io/v2/o/r/manifests/sha256-abc"


class _Resp:
    def __init__(self, status: int, body: dict[str, Any] | None = None) -> None:
        self.status_code = status
        self._body = body or {}
        self.text = str(self._body)
        self.headers: dict[str, str] = {}

    def json(self) -> dict[str, Any]:
        return self._body


def _client(monkeypatch, answers: dict[str, _Resp]) -> tuple[RegistryClient, list[str]]:
    client = RegistryClient("ghcr.io", "o/r")
    seen: list[str] = []

    def fake_request(url, headers, method="GET"):
        seen.append(url)
        return answers[url]

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "_authenticate", lambda resp: None)
    return client, seen


def test_api_answer_wins(monkeypatch) -> None:
    client, seen = _client(
        monkeypatch, {_API: _Resp(200, {"manifests": [{"digest": "d"}]})}
    )
    assert client.get_referrers(_DIGEST) == [{"digest": "d"}]
    assert seen == [_API]


def test_api_404_falls_back_to_tag(monkeypatch) -> None:
    client, _ = _client(
        monkeypatch,
        {_API: _Resp(404), _TAG: _Resp(200, {"manifests": [{"digest": "d"}]})},
    )
    assert client.get_referrers(_DIGEST) == [{"digest": "d"}]


def test_both_absent_is_empty(monkeypatch) -> None:
    client, _ = _client(monkeypatch, {_API: _Resp(404), _TAG: _Resp(404)})
    assert client.get_referrers(_DIGEST) == []


def test_null_manifests_is_empty(monkeypatch) -> None:
    client, _ = _client(monkeypatch, {_API: _Resp(200, {"manifests": None})})
    assert client.get_referrers(_DIGEST) == []


def test_fallback_500_raises(monkeypatch) -> None:
    client, _ = _client(monkeypatch, {_API: _Resp(404), _TAG: _Resp(500)})
    with pytest.raises(RegistryError):
        client.get_referrers(_DIGEST)


def test_401_reauthenticates_then_retries(monkeypatch) -> None:
    client = RegistryClient("ghcr.io", "o/r")
    answers = iter([_Resp(401), _Resp(200, {"manifests": []})])
    monkeypatch.setattr(
        client, "_request", lambda url, headers, method="GET": next(answers)
    )
    monkeypatch.setattr(client, "_authenticate", lambda resp: None)
    assert client.get_referrers(_DIGEST) == []
