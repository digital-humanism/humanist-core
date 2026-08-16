"""Fixtures for HACP v0.9.2 conformance tests."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


SEED_INPUT = b"hacp-conformance-v0.9-key-001"
SIGNER_KEY_ID = "key-ed25519-test-001"
EXPECTED_PUBLIC_KEY_HEX = (
    "9d17f1bbcc0845865e670f526413fb7a"
    "510380798fe300b6c98e28f3a3b0fdb3"
)


def resolve_spec_repo() -> Path:
    env_path = os.environ.get("HACP_SPEC_REPO")
    if env_path:
        return Path(env_path).resolve()

    repo_root = Path(__file__).resolve().parents[2]
    return (repo_root.parent / "hacp-spec").resolve()


def _load_json_preserving_duplicate_info(text: str) -> tuple[dict, list[str]]:
    """Parse a conformance vector without aborting on duplicate JSON keys.

    Duplicate keys are intentionally possible in malformed/negative vectors.
    Python's json parser keeps the last value, while we separately record
    duplicate-key diagnostics so the evaluator can fail closed.
    """
    duplicate_keys: list[str] = []

    def object_pairs_hook(pairs):
        result = {}

        for key, value in pairs:
            if key in result:
                duplicate_keys.append(key)

            result[key] = value

        return result

    data = json.loads(
        text,
        object_pairs_hook=object_pairs_hook,
    )

    return data, duplicate_keys


def load_vectors(vectors_dir: Path) -> list[dict]:
    vectors: list[dict] = []

    for path in sorted(vectors_dir.glob("*.json")):
        try:
            data, duplicate_keys = _load_json_preserving_duplicate_info(
                path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            continue

        if "test_id" not in data:
            continue

        data["_source_file"] = str(path)

        # Test-only metadata. It is never included in canonical HACP payloads.
        if duplicate_keys:
            data["_duplicate_json_keys"] = duplicate_keys

        vectors.append(data)

    return vectors


@pytest.fixture(scope="session")
def spec_repo() -> Path:
    candidate = resolve_spec_repo()
    if not candidate.exists():
        pytest.skip(
            "hacp-spec repository not found. Set HACP_SPEC_REPO or clone "
            "hacp-spec beside humanist-core."
        )
    return candidate


@pytest.fixture(scope="session")
def vectors_dir(spec_repo: Path) -> Path:
    path = spec_repo / "vectors"
    if not path.exists():
        pytest.skip(f"HACP vectors directory not found: {path}")
    return path


@pytest.fixture(scope="session")
def conformance_vectors(vectors_dir: Path) -> list[dict]:
    vectors = load_vectors(vectors_dir)
    assert len(vectors) == 38, (
        "HACP v0.9.2 baseline drift: expected exactly 38 vectors, "
        f"found {len(vectors)} in {vectors_dir}"
    )
    test_ids = [v["test_id"] for v in vectors]
    assert len(test_ids) == len(set(test_ids)), "duplicate HACP test_id detected"
    return vectors


@pytest.fixture(scope="session")
def test_private_key() -> Ed25519PrivateKey:
    seed = hashlib.sha256(SEED_INPUT).digest()
    return Ed25519PrivateKey.from_private_bytes(seed)


@pytest.fixture(scope="session")
def test_public_key(test_private_key):
    public_key = test_private_key.public_key()
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    assert raw.hex() == EXPECTED_PUBLIC_KEY_HEX
    return public_key


def pytest_generate_tests(metafunc):
    if "conformance_vector" not in metafunc.fixturenames:
        return

    spec_repo = resolve_spec_repo()
    vectors_dir = spec_repo / "vectors"

    if not vectors_dir.exists():
        metafunc.parametrize(
            "conformance_vector",
            [
                pytest.param(
                    None,
                    marks=pytest.mark.skip(
                        reason="hacp-spec vectors unavailable; set HACP_SPEC_REPO"
                    ),
                )
            ],
        )
        return

    vectors = load_vectors(vectors_dir)

    metafunc.parametrize(
        "conformance_vector",
        vectors,
        ids=[v["test_id"] for v in vectors],
    )
