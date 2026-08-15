"""Unit tests for SidecarClient header injection and decision handling."""
import httpx
import pytest
import respx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from humanist_core.hacp import (
    EnvelopeBuilder,
    SidecarClient,
    ScopeExceededError,
    CheckpointRequiredError,
    TraceabilityFailureError,
)

BASE = "http://sidecar.test"


@pytest.fixture()
def key():
    return Ed25519PrivateKey.generate()


@pytest.fixture()
def signed_env(key):
    return (
        EnvelopeBuilder()
        .principal("agent_001")
        .scope(
            verbs=["read"],
            resource_classes=[],
            audiences=["internal"],
            data_classes=["public"],
        )
        .autonomy_budget(max_actions=1, expires_at=2000000000)
        .sign(key)
    )


def allow_response():
    return httpx.Response(
        200,
        json={"ok": True},
        headers={"X-HACP-Decision": "ALLOW", "X-HACP-Request-Id": "req-1"},
    )


@respx.mock
def test_allow_and_header_injection(signed_env):
    route = respx.get(f"{BASE}/api/test").mock(return_value=allow_response())
    with SidecarClient(BASE) as client:
        resp = client.request("GET", "/api/test", envelope=signed_env)
    assert resp.status_code == 200
    assert route.called
    req = route.calls.last.request
    assert req.headers["X-HACP-Intent-Envelope"] == signed_env.to_b64url()


@respx.mock
def test_deny_maps_to_scope_exceeded(signed_env):
    respx.get(f"{BASE}/api/test").mock(
        return_value=httpx.Response(
            403,
            headers={
                "X-HACP-Decision": "DENY",
                "X-HACP-Reason": "SCOPE_EXCEEDED",
                "X-HACP-Request-Id": "req-2",
            },
        )
    )
    with SidecarClient(BASE) as client:
        with pytest.raises(ScopeExceededError):
            client.request("GET", "/api/test", envelope=signed_env)


@respx.mock
def test_checkpoint_raises(signed_env):
    respx.get(f"{BASE}/api/test").mock(
        return_value=httpx.Response(
            200,
            headers={"X-HACP-Decision": "CHECKPOINT", "X-HACP-Request-Id": "req-3"},
        )
    )
    with SidecarClient(BASE) as client:
        with pytest.raises(CheckpointRequiredError):
            client.request("GET", "/api/test", envelope=signed_env)


@respx.mock
def test_missing_decision_header_fail_closed(signed_env):
    respx.get(f"{BASE}/api/test").mock(return_value=httpx.Response(200, json={}))
    with SidecarClient(BASE) as client:
        with pytest.raises(TraceabilityFailureError):
            client.request("GET", "/api/test", envelope=signed_env)