"""Unit tests for HACP CLI commands."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import httpx
import pytest
import respx
from click.testing import CliRunner
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from humanist_core.hacp.cli import cli
from humanist_core.hacp.crypto import export_private_key_pem


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def temp_key_file():
    """Create a temporary Ed25519 private key PEM file."""
    key = Ed25519PrivateKey.generate()
    pem = export_private_key_pem(key)
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pem") as f:
        f.write(pem)
        path = Path(f.name)
    yield path
    path.unlink()


@pytest.fixture()
def temp_envelope_file():
    """Create a temporary envelope JSON file."""
    envelope_data = {
        "principal": "agent_001",
        "principal_kind": "system",
        "scope": {
            "verbs": ["read"],
            "resource_classes": [],
            "audiences": ["internal"],
            "reversibility": ["reversible"],
            "externality": ["internal"],
            "data_classes": ["public"],
        },
        "autonomy_budget": {
            "max_actions": 10,
            "expires_at": 9999999999,
            "used_actions": 0,
        },
        "signer_key_id": "key-001",
        "issued_at": 1700000000,
        "expires_at": 1800000000,
        "envelope_id": "env-001",
        "signature": "dummy_sig",
    }
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(envelope_data, f)
        path = Path(f.name)
    yield path
    path.unlink()


@pytest.fixture()
def temp_action_file():
    """Create a temporary action JSON file."""
    action_data = {
        "verb": "read",
        "resource_class": "record",
        "resource_id": "/api/test/1",
        "audience": "internal",
        "data_class": "public",
        "constraints": {
            "method": "GET",
            "path": "/api/test/1",
            "max_uses": 1,
        },
    }
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(action_data, f)
        path = Path(f.name)
    yield path
    path.unlink()


class TestEnvelopeCreate:
    """Tests for `humanist envelope create`."""

    def test_envelope_create_stdout(self, runner, temp_key_file):
        result = runner.invoke(
            cli,
            [
                "envelope",
                "create",
                "--principal",
                "test_agent",
                "--scope-verbs",
                "read,write",
                "--sign",
                str(temp_key_file),
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["principal"] == "test_agent"
        assert "read" in output["scope"]["verbs"]
        assert "write" in output["scope"]["verbs"]
        assert "signature" in output

    def test_envelope_create_to_file(self, runner, temp_key_file, tmp_path):
        out_file = tmp_path / "envelope.json"
        result = runner.invoke(
            cli,
            [
                "envelope",
                "create",
                "--principal",
                "test_agent",
                "--scope-verbs",
                "read",
                "--sign",
                str(temp_key_file),
                "--out",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        assert out_file.exists()
        output = json.loads(out_file.read_text())
        assert output["principal"] == "test_agent"
        assert "signature" in output

    def test_envelope_create_bad_key_path(self, runner):
        result = runner.invoke(
            cli,
            [
                "envelope",
                "create",
                "--principal",
                "test",
                "--scope-verbs",
                "read",
                "--sign",
                "/nonexistent/key.pem",
            ],
        )
        assert result.exit_code != 0

    def test_envelope_create_with_options(self, runner, temp_key_file):
        result = runner.invoke(
            cli,
            [
                "envelope",
                "create",
                "--principal",
                "test_agent",
                "--principal-kind",
                "human",
                "--scope-verbs",
                "read",
                "--audience",
                "external",
                "--data-class",
                "confidential",
                "--reversibility",
                "irreversible",
                "--externality",
                "external",
                "--max-actions",
                "5",
                "--expires-in",
                "7200",
                "--sign",
                str(temp_key_file),
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["principal_kind"] == "human"
        assert "external" in output["scope"]["audiences"]
        assert "confidential" in output["scope"]["data_classes"]
        assert output["autonomy_budget"]["max_actions"] == 5


class TestTokenCreate:
    """Tests for `humanist token create`."""

    def test_token_create_stdout(
        self, runner, temp_key_file, temp_envelope_file, temp_action_file
    ):
        result = runner.invoke(
            cli,
            [
                "token",
                "create",
                "--envelope",
                str(temp_envelope_file),
                "--action",
                str(temp_action_file),
                "--sign",
                str(temp_key_file),
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert "action_hash" in output
        assert "signature" in output
        assert output["envelope_id"] == "env-001"

    def test_token_create_to_file(
        self, runner, temp_key_file, temp_envelope_file, temp_action_file, tmp_path
    ):
        out_file = tmp_path / "token.json"
        result = runner.invoke(
            cli,
            [
                "token",
                "create",
                "--envelope",
                str(temp_envelope_file),
                "--action",
                str(temp_action_file),
                "--sign",
                str(temp_key_file),
                "--out",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        assert out_file.exists()
        output = json.loads(out_file.read_text())
        assert "signature" in output

    def test_token_create_bad_envelope(
        self, runner, temp_key_file, temp_action_file
    ):
        result = runner.invoke(
            cli,
            [
                "token",
                "create",
                "--envelope",
                "/nonexistent/envelope.json",
                "--action",
                str(temp_action_file),
                "--sign",
                str(temp_key_file),
            ],
        )
        assert result.exit_code != 0

    def test_token_create_bad_action(
        self, runner, temp_key_file, temp_envelope_file
    ):
        result = runner.invoke(
            cli,
            [
                "token",
                "create",
                "--envelope",
                str(temp_envelope_file),
                "--action",
                "/nonexistent/action.json",
                "--sign",
                str(temp_key_file),
            ],
        )
        assert result.exit_code != 0


class TestRequest:
    """Tests for `humanist request`."""

    def test_request_success(self, runner, tmp_path):
        env_file = tmp_path / "env.b64"
        tok_file = tmp_path / "tok.b64"
        env_file.write_text("dummy_envelope_b64")
        tok_file.write_text("dummy_token_b64")

        with respx.mock:
            respx.get("http://127.0.0.1:8080/api/test").mock(
                return_value=httpx.Response(
                    200,
                    json={"ok": True},
                    headers={
                        "X-HACP-Decision": "ALLOW",
                        "X-HACP-Request-Id": "req-1",
                    },
                )
            )
            result = runner.invoke(
                cli,
                [
                    "request",
                    "--url",
                    "http://127.0.0.1:8080/api/test",
                    "--envelope",
                    str(env_file),
                    "--token",
                    str(tok_file),
                ],
            )
        assert result.exit_code == 0
        assert "ok" in result.output

    def test_request_deny(self, runner, tmp_path):
        env_file = tmp_path / "env.b64"
        tok_file = tmp_path / "tok.b64"
        env_file.write_text("dummy_envelope_b64")
        tok_file.write_text("dummy_token_b64")

        with respx.mock:
            respx.get("http://127.0.0.1:8080/api/test").mock(
                return_value=httpx.Response(
                    403,
                    headers={
                        "X-HACP-Decision": "DENY",
                        "X-HACP-Reason": "SCOPE_EXCEEDED",
                        "X-HACP-Request-Id": "req-2",
                    },
                )
            )
            result = runner.invoke(
                cli,
                [
                    "request",
                    "--url",
                    "http://127.0.0.1:8080/api/test",
                    "--envelope",
                    str(env_file),
                    "--token",
                    str(tok_file),
                ],
            )
        assert result.exit_code != 0
        assert "Error" in result.output or "SCOPE_EXCEEDED" in result.output

    def test_request_connection_error(self, runner, tmp_path):
        env_file = tmp_path / "env.b64"
        tok_file = tmp_path / "tok.b64"
        env_file.write_text("dummy_envelope_b64")
        tok_file.write_text("dummy_token_b64")

        with respx.mock:
            respx.get("http://127.0.0.1:8080/api/test").mock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            result = runner.invoke(
                cli,
                [
                    "request",
                    "--url",
                    "http://127.0.0.1:8080/api/test",
                    "--envelope",
                    str(env_file),
                    "--token",
                    str(tok_file),
                ],
            )
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_request_no_headers(self, runner, tmp_path):
        env_file = tmp_path / "env.b64"
        tok_file = tmp_path / "tok.b64"
        env_file.write_text("dummy_envelope_b64")
        tok_file.write_text("dummy_token_b64")

        with respx.mock:
            respx.get("http://127.0.0.1:8080/api/test").mock(
                return_value=httpx.Response(200, json={})
            )
            result = runner.invoke(
                cli,
                [
                    "request",
                    "--url",
                    "http://127.0.0.1:8080/api/test",
                    "--envelope",
                    str(env_file),
                    "--token",
                    str(tok_file),
                ],
            )
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_request_with_method(self, runner, tmp_path):
        env_file = tmp_path / "env.b64"
        tok_file = tmp_path / "tok.b64"
        env_file.write_text("dummy_envelope_b64")
        tok_file.write_text("dummy_token_b64")

        with respx.mock:
            respx.post("http://127.0.0.1:8080/api/test").mock(
                return_value=httpx.Response(
                    200,
                    json={"ok": True},
                    headers={
                        "X-HACP-Decision": "ALLOW",
                        "X-HACP-Request-Id": "req-3",
                    },
                )
            )
            result = runner.invoke(
                cli,
                [
                    "request",
                    "--url",
                    "http://127.0.0.1:8080/api/test",
                    "--method",
                    "POST",
                    "--envelope",
                    str(env_file),
                    "--token",
                    str(tok_file),
                ],
            )
        assert result.exit_code == 0