"""Final branch-coverage tests for the HACP SDK.

This file intentionally targets the small set of remaining meaningful branches
after the main unit and security-hardening suites.
"""
from __future__ import annotations

import json
import runpy
import sys

import httpx
import pytest
import respx
from click.testing import CliRunner
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from humanist_core.hacp import (
    EnvelopeBuilder,
    TokenBuilder,
    SidecarClient,
    HACPError,
    b64url_decode,
)
from humanist_core.hacp.builders import _as_list
from humanist_core.hacp.cli import cli
from humanist_core.hacp.crypto import b64url_decode as decode_b64url


BASE = "http://sidecar.test"


def _allow_response(request_id: str = "req-final") -> httpx.Response:
    return httpx.Response(
        200,
        json={"ok": True},
        headers={
            "X-HACP-Decision": "ALLOW",
            "X-HACP-Request-Id": request_id,
        },
    )


def _signed_credentials():
    key = Ed25519PrivateKey.generate()

    signed_env = (
        EnvelopeBuilder()
        .principal("agent-final")
        .scope(
            verbs=["read"],
            resource_classes=["record"],
            audiences=["internal"],
            data_classes=["internal"],
        )
        .sign(key)
    )

    signed_token = (
        TokenBuilder()
        .envelope(signed_env.envelope)
        .http_action("GET", "/api/test")
        .constraints(method="GET", path="/api/test", max_uses=1)
        .policy_digest("policy-final")
        .sign(key)
    )

    return signed_env, signed_token


# ---------------------------------------------------------------------------
# builders.py
# ---------------------------------------------------------------------------

def test_as_list_none_uses_default():
    """Cover the explicit None/default normalization branch."""
    assert _as_list(None, "reversible") == ["reversible"]


def test_as_list_string_is_single_value_not_character_sequence():
    """A scalar scope value must remain one semantic value."""
    assert _as_list("external", "internal") == ["external"]


def test_signed_token_wrapper_to_dict_and_b64url_are_consistent():
    """Exercise the signed-token wrapper independently of client transport."""
    _, signed_token = _signed_credentials()

    wire = signed_token.to_dict()
    decoded = json.loads(decode_b64url(signed_token.to_b64url()))

    assert wire["signature"] == signed_token.signature
    assert decoded == wire


def test_envelope_builder_canonicalize_direct_path():
    """Exercise the public canonicalize() helper directly."""
    canonical = (
        EnvelopeBuilder()
        .principal("agent-canonical")
        .scope(
            verbs=["read"],
            resource_classes=["record"],
            audiences=["internal"],
            data_classes=["internal"],
        )
        .issued_at(1_800_000_000)
        .expires_at(1_800_000_100)
        .signer_key_id("key-canonical")
        .envelope_id("env-canonical")
        .canonicalize()
    )

    decoded = json.loads(canonical)
    assert decoded["principal"] == "agent-canonical"
    assert decoded["envelope_id"] == "env-canonical"


def test_constraints_can_be_explicitly_empty():
    """Optional constraints remain representable without inventing policy."""
    env = (
        EnvelopeBuilder()
        .principal("agent-constraints")
        .scope(
            verbs=["read"],
            resource_classes=["record"],
            audiences=["internal"],
            data_classes=["internal"],
        )
        .build_unsigned()
    )

    token = (
        TokenBuilder()
        .envelope(env)
        .http_action("GET", "/api/test")
        .constraints()
        .build_unsigned()
    )

    assert token.constraints is not None
    assert token.constraints.to_dict() == {}


# ---------------------------------------------------------------------------
# client.py
# ---------------------------------------------------------------------------

@respx.mock
def test_client_injects_signed_token_object():
    """Cover the non-string DecisionToken header branch."""
    signed_env, signed_token = _signed_credentials()

    route = respx.get(f"{BASE}/api/test").mock(return_value=_allow_response())

    with SidecarClient(BASE) as client:
        response = client.request(
            "GET",
            "/api/test",
            envelope=signed_env,
            token=signed_token,
        )

    assert response.status_code == 200
    request = route.calls.last.request
    assert request.headers["X-HACP-Decision-Token"] == signed_token.to_b64url()


@respx.mock
def test_client_injects_policy_context_and_tool_name():
    """Cover optional policy and deployment-hint HACP headers."""
    route = respx.get(f"{BASE}/api/test").mock(return_value=_allow_response())

    policy_context = {
        "tenant": "acme",
        "environment": "test",
    }

    with SidecarClient(BASE) as client:
        response = client.request(
            "GET",
            "/api/test",
            policy_context=policy_context,
            tool_name="customer_lookup",
        )

    assert response.status_code == 200

    request = route.calls.last.request
    assert request.headers["X-HACP-Tool-Name"] == "customer_lookup"

    encoded_policy = request.headers["X-HACP-Policy-Context"]
    decoded_policy = json.loads(b64url_decode(encoded_policy))
    assert decoded_policy == policy_context


def test_client_fails_closed_on_unknown_decision():
    """Unknown protocol decisions must never be treated as ALLOW."""
    response = httpx.Response(
        200,
        headers={
            "X-HACP-Decision": "MAGIC",
            "X-HACP-Request-Id": "req-unknown",
        },
    )

    with SidecarClient(BASE) as client:
        with pytest.raises(HACPError, match="Unknown HACP decision: MAGIC"):
            client._handle_hacp_response(response)


# ---------------------------------------------------------------------------
# cli.py
# ---------------------------------------------------------------------------

def test_cli_request_rejects_non_absolute_url():
    """Cover the explicit absolute-URL validation branch."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "request",
            "--url",
            "127.0.0.1:8080/api/test",
        ],
    )

    assert result.exit_code != 0
    assert "URL must be absolute" in result.output


@respx.mock
def test_cli_request_preserves_query_string():
    """A complete CLI URL must retain its query component."""
    runner = CliRunner()

    route = respx.get(
        "http://127.0.0.1:8080/api/test?limit=10&active=true"
    ).mock(return_value=_allow_response("req-query"))

    result = runner.invoke(
        cli,
        [
            "request",
            "--url",
            "http://127.0.0.1:8080/api/test?limit=10&active=true",
        ],
    )

    assert result.exit_code == 0
    assert route.called
    assert '"ok": true' in result.output.lower()


def test_cli_module_entrypoint_executes(monkeypatch):
    """Cover `if __name__ == "__main__": cli()` without runpy re-exec warnings."""
    monkeypatch.setattr(sys, "argv", ["humanist", "--help"])

    # `cli` is imported at module collection time above.  runpy warns when
    # asked to execute a module that is already present in sys.modules.
    # Temporarily remove only this submodule; monkeypatch restores it after
    # the test, so normal import state is preserved.
    monkeypatch.delitem(sys.modules, "humanist_core.hacp.cli", raising=False)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("humanist_core.hacp.cli", run_name="__main__")

    assert exc.value.code == 0
