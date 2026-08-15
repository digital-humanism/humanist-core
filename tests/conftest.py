"""Shared fixtures for humanist-core tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SIDECAR_REPO = Path(
    os.environ.get("HACP_SIDECAR_REPO", str(REPO_ROOT.parent / "hacp-sidecar"))
)


def find_sidecar_binary() -> "Path | None":
    """Resolve hacp-sidecar binary via env var or sibling repo layout."""
    env_bin = os.environ.get("HACP_SIDECAR_BIN")
    if env_bin:
        p = Path(env_bin)
        return p if p.exists() else None

    candidates = [
        SIDECAR_REPO / "hacp-sidecar.exe",
        SIDECAR_REPO / "bin" / "hacp-sidecar.exe",
        SIDECAR_REPO / "build" / "hacp-sidecar.exe",
        SIDECAR_REPO / "hacp-sidecar",
        SIDECAR_REPO / "bin" / "hacp-sidecar",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


@pytest.fixture(scope="session")
def sidecar_bin() -> Path:
    bin_path = find_sidecar_binary()
    if bin_path is None:
        pytest.skip(
            "hacp-sidecar binary not found. "
            "Set HACP_SIDECAR_BIN or HACP_SIDECAR_REPO."
        )
    return bin_path