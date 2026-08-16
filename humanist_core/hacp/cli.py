"""CLI entry point for humanist-core HACP tools."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

import click

from .builders import EnvelopeBuilder, TokenBuilder
from .client import SidecarClient
from .models import IntentEnvelope, Scope, AutonomyBudget
from .crypto import load_private_key_pem


@click.group()
def cli():
    """Digital Humanism HACP CLI."""
    pass


@cli.group()
def envelope():
    """Manage HACP Intent Envelopes."""
    pass


@envelope.command("create")
@click.option("--principal", required=True, help="Principal identifier")
@click.option(
    "--principal-kind",
    default="system",
    type=click.Choice(["human", "system", "delegated"]),
)
@click.option("--scope-verbs", required=True, help="Comma-separated verbs")
@click.option("--audience", "audiences", multiple=True, default=["internal"])
@click.option("--data-class", "data_classes", multiple=True, default=["public"])
@click.option("--reversibility", default="reversible")
@click.option("--externality", default="internal")
@click.option("--max-actions", default=1, type=int)
@click.option("--expires-in", default=3600, type=int, help="Seconds until expiry")
@click.option("--sign", "key_path", required=True, type=click.Path(exists=True))
@click.option("--out", type=click.Path(), default="-")
def envelope_create(
    principal, principal_kind, scope_verbs, audiences, data_classes,
    reversibility, externality, max_actions, expires_in, key_path, out,
):
    """Create and sign an Intent Envelope."""
    private_key = load_private_key_pem(Path(key_path).read_bytes())
    verbs = [v.strip() for v in scope_verbs.split(",") if v.strip()]
    now = int(time.time())

    signed_env = (
        EnvelopeBuilder()
        .principal(principal)
        .principal_kind(principal_kind)
        .scope(
            verbs=verbs,
            resource_classes=[],
            audiences=list(audiences),
            reversibility=reversibility,
            externality=externality,
            data_classes=list(data_classes),
        )
        .autonomy_budget(max_actions=max_actions, expires_at=now + expires_in)
        .sign(private_key)
    )

    output = json.dumps(signed_env.to_dict(), indent=2)
    if out == "-":
        click.echo(output)
    else:
        Path(out).write_text(output)
        click.echo(f"Envelope written to {out}", err=True)


@cli.group()
def token():
    """Manage HACP Decision Tokens."""
    pass


@token.command("create")
@click.option("--envelope", "envelope_path", required=True, type=click.Path(exists=True))
@click.option("--action", "action_path", required=True, type=click.Path(exists=True))
@click.option("--sign", "key_path", required=True, type=click.Path(exists=True))
@click.option("--out", type=click.Path(), default="-")
def token_create(envelope_path, action_path, key_path, out):
    """Create and sign a Decision Token."""
    private_key = load_private_key_pem(Path(key_path).read_bytes())
    env_data = json.loads(Path(envelope_path).read_text())

    envelope = IntentEnvelope(
        principal=env_data["principal"],
        principal_kind=env_data["principal_kind"],
        scope=Scope(**env_data["scope"]),
        autonomy_budget=AutonomyBudget(**env_data["autonomy_budget"]),
        signer_key_id=env_data["signer_key_id"],
        issued_at=env_data["issued_at"],
        expires_at=env_data["expires_at"],
        envelope_id=env_data.get("envelope_id"),
    )

    action_data = json.loads(Path(action_path).read_text())
    constraints_data = action_data.pop("constraints", {})

    signed_tok = (
        TokenBuilder()
        .envelope(envelope)
        .proposed_action(**action_data)
        .constraints(**constraints_data)
        .sign(private_key)
    )

    output = json.dumps(signed_tok.to_dict(), indent=2)
    if out == "-":
        click.echo(output)
    else:
        Path(out).write_text(output)
        click.echo(f"Token written to {out}", err=True)


@cli.command()
@click.option("--url", required=True)
@click.option("--method", default="GET")
@click.option("--envelope", "envelope_b64_path", type=click.Path(exists=True))
@click.option("--token", "token_b64_path", type=click.Path(exists=True))
def request(url, method, envelope_b64_path, token_b64_path):
    """Make an HTTP request through the HACP sidecar."""
    envelope_b64 = None
    token_b64 = None

    if envelope_b64_path:
        envelope_b64 = Path(envelope_b64_path).read_text().strip()
    if token_b64_path:
        token_b64 = Path(token_b64_path).read_text().strip()

    parsed = urlsplit(url)
    if not parsed.scheme or not parsed.netloc:
        raise click.BadParameter(
            "URL must be absolute, e.g. http://127.0.0.1:8080/api/test",
            param_hint="--url",
        )

    base_url = f"{parsed.scheme}://{parsed.netloc}"
    request_path = parsed.path or "/"
    if parsed.query:
        request_path = f"{request_path}?{parsed.query}"

    try:
        with SidecarClient(base_url=base_url) as client:
            response = client.request(
                method=method,
                path=request_path,
                envelope=envelope_b64,
                token=token_b64,
            )
            click.echo(json.dumps(response.json(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.exceptions.Exit(1)


if __name__ == "__main__":
    cli()