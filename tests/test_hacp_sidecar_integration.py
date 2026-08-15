"""End-to-end interoperability tests: humanist-core <-> hacp-sidecar."""
from __future__ import annotations

import os
import uuid
import shlex
import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest

from humanist_core.hacp import (
    EnvelopeBuilder,
    TokenBuilder,
    SidecarClient,
    b64url_decode,
    load_private_key_pem,
)
from humanist_core.hacp.crypto import canonicalize_json, verify, hash_sha256


DEFAULT_URL = "http://127.0.0.1:18080"
E2E_ENVELOPE_ID = "22222222-2222-4222-8222-222222222222"
E2E_TOKEN_ID = "33333333-3333-4333-8333-333333333333"
POLICY_DIGEST = (
    "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
    "a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
)


def _sidecar_url() -> str:
    return os.environ.get("HACP_SIDECAR_URL", DEFAULT_URL).rstrip("/")


def _wait_for_tcp(url: str, timeout: float = 10.0) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    deadline = time.monotonic() + timeout
    last_error = None

    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.1)

    raise RuntimeError(f"sidecar not ready at {host}:{port}: {last_error}")


@pytest.fixture(scope="session")
def running_sidecar(sidecar_bin: Path):
    url = _sidecar_url()

    if os.environ.get("HACP_SIDECAR_EXTERNAL") == "1":
        _wait_for_tcp(url)
        yield url
        return

    raw_args = os.environ.get("HACP_SIDECAR_ARGS")
    if not raw_args:
        pytest.skip(
            "Set HACP_SIDECAR_ARGS, or HACP_SIDECAR_EXTERNAL=1 plus "
            "HACP_SIDECAR_URL."
        )

    proc = subprocess.Popen(
        [str(sidecar_bin), *shlex.split(raw_args, posix=False)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        _wait_for_tcp(url)
        yield url
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def _test_identity():
    key_path = os.environ.get("HACP_TEST_PRIVATE_KEY")
    key_id = os.environ.get("HACP_TEST_SIGNER_KEY_ID")
    if not key_path or not key_id:
        pytest.skip("Set HACP_TEST_PRIVATE_KEY and HACP_TEST_SIGNER_KEY_ID.")

    path = Path(key_path)
    if not path.is_file():
        pytest.fail(f"HACP_TEST_PRIVATE_KEY does not exist: {path}")

    return load_private_key_pem(path.read_bytes()), key_id


def _build_signed_pair():
    private_key, key_id = _test_identity()
    now = int(time.time())

    signed_env = (
        EnvelopeBuilder()
        .hacp_version("0.9")
        .principal("human_admin_01")
        .principal_kind("human")
        .intent_statement("Humanist Core sidecar interoperability test")
        .scope(
            verbs=["read"],
            resource_classes=["customer_record"],
            audiences=["internal"],
            reversibility=["reversible"],
            externality=["internal"],
            data_classes=["internal"],
        )
        .issued_at(now)
        .expires_at(now + 300)
        .signer_key_id(key_id)
        .envelope_id(E2E_ENVELOPE_ID)
        .sign(private_key)
    )

    # IMPORTANT: this mirrors hacp-sidecar HTTP synthesis:
    # GET -> read, resource_id=/api/test, scope dimensions from envelope,
    # payload_hash = SHA-256(empty body).
    signed_token = (
        TokenBuilder()
        .envelope(signed_env.envelope)
        .token_id(str(uuid.uuid4()))
        .issued_at(now)
        .expires_at(now + 300)
        .http_action("GET", "/api/test", body=b"")
        .constraints(method="GET", path="/api/test", max_uses=1)
        .decision("ALLOW")
        .policy_digest(POLICY_DIGEST)
        .sign(private_key)
    )

    return private_key, signed_env, signed_token


def test_real_sidecar_is_fail_closed_without_hacp_headers(running_sidecar):
    response = httpx.get(f"{running_sidecar}/api/test", timeout=5.0)
    assert response.headers.get("X-HACP-Decision") != "ALLOW"


def test_http_action_hash_matches_sidecar_shape():
    _, _, signed_token = _build_signed_pair()

    # Independent expected representation from hacp-sidecar's generator.
    expected_action = {
        "hacp_version": "0.9",
        "verb": "read",
        "resource_class": "customer_record",
        "resource_id": "/api/test",
        "audience": "internal",
        "reversibility": "reversible",
        "externality": "internal",
        "data_class": "internal",
        "payload_hash": hash_sha256(b""),
    }

    from humanist_core.hacp import hash_action
    assert signed_token.token.action_hash == hash_action(expected_action)


def test_python_envelope_and_token_signatures_are_self_consistent():
    private_key, signed_env, signed_token = _build_signed_pair()

    env = signed_env.to_dict()
    env_sig = b64url_decode(env.pop("signature"))
    assert verify(canonicalize_json(env), env_sig, private_key.public_key())

    tok = signed_token.to_dict()
    tok_sig = b64url_decode(tok.pop("signature"))
    assert verify(canonicalize_json(tok), tok_sig, private_key.public_key())


def test_real_sidecar_allows_python_signed_request(running_sidecar):
    _, signed_env, signed_token = _build_signed_pair()

    response = httpx.get(
        f"{running_sidecar}/api/test",
        headers={
            "X-HACP-Intent-Envelope": signed_env.to_b64url(),
            "X-HACP-Decision-Token": signed_token.to_b64url(),
        },
        timeout=5.0,
    )

    assert response.headers.get("X-HACP-Decision") == "ALLOW", (
        f"Expected ALLOW, got decision={response.headers.get('X-HACP-Decision')} "
        f"reason={response.headers.get('X-HACP-Reason')} body={response.text}"
    )
    assert response.status_code == 200


def test_sidecar_client_gets_allow(running_sidecar):
    _, signed_env, signed_token = _build_signed_pair()


    with SidecarClient(running_sidecar) as client:
        response = client.request(
            "GET",
            "/api/test",
            envelope=signed_env,
            token=signed_token,
        )

    assert response.headers.get("X-HACP-Decision") == "ALLOW"
    assert response.status_code == 200
