"""HTTP client for HACP Sidecar integration.

Injects HACP headers and enforces fail-closed behavior on responses.
Supports both typed objects and raw base64url strings.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, Union

import httpx

from .builders import SignedIntentEnvelope, SignedDecisionToken
from .crypto import b64url_encode, canonicalize_json
from .exceptions import (
    HACPError,
    CheckpointRequiredError,
    TraceabilityFailureError,
    parse_reason_code,
)


class SidecarClient:
    """Synchronous HTTP client for communicating with hacp-sidecar."""

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=timeout)

    def request(
        self,
        method: str,
        path: str,
        envelope: Optional[Union[SignedIntentEnvelope, str]] = None,
        token: Optional[Union[SignedDecisionToken, str]] = None,
        policy_context: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request through the HACP sidecar.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., /api/customers/123)
            envelope: Signed intent envelope (object) or raw base64url string
            token: Signed decision token (object) or raw base64url string
            policy_context: Optional policy context dict
            tool_name: Optional deployment hint

        Returns:
            httpx.Response if decision is ALLOW

        Raises:
            HACPError or subclass if decision is DENY/CHECKPOINT
        """
        headers = kwargs.pop("headers", {})

        if envelope:
            if isinstance(envelope, str):
                headers["X-HACP-Intent-Envelope"] = envelope
            else:
                headers["X-HACP-Intent-Envelope"] = envelope.to_b64url()

        if token:
            if isinstance(token, str):
                headers["X-HACP-Decision-Token"] = token
            else:
                headers["X-HACP-Decision-Token"] = token.to_b64url()

        if policy_context:
            headers["X-HACP-Policy-Context"] = b64url_encode(
                canonicalize_json(policy_context)
            )

        if tool_name:
            headers["X-HACP-Tool-Name"] = tool_name

        try:
            response = self.client.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as e:
            # Fail closed on network/connection errors
            raise HACPError(f"Sidecar connection failed: {e}") from e

        self._handle_hacp_response(response)
        return response

    def _handle_hacp_response(self, response: httpx.Response) -> None:
        """Parse HACP decision headers and raise exceptions on failure."""
        decision = response.headers.get("X-HACP-Decision")
        reason = response.headers.get("X-HACP-Reason", "")
        request_id = response.headers.get("X-HACP-Request-Id", "unknown")

        if decision is None:
            raise TraceabilityFailureError(
                f"Missing X-HACP-Decision header. Request ID: {request_id}"
            )

        if decision == "ALLOW":
            return

        if decision == "CHECKPOINT":
            raise CheckpointRequiredError(
                f"Checkpoint required. Request ID: {request_id}"
            )

        if decision == "DENY":
            exc = parse_reason_code(
                reason, f"Request denied. Request ID: {request_id}"
            )
            raise exc

        raise HACPError(f"Unknown HACP decision: {decision}")

    def close(self) -> None:
        """Close underlying HTTP connection."""
        self.client.close()

    def __enter__(self) -> "SidecarClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()