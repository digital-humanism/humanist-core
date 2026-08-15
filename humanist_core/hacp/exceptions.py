"""HACP Exception hierarchy.

Maps directly to X-HACP-Reason codes from hacp-spec.
Fail-closed by default: all exceptions result in DENY.
"""


class HACPError(Exception):
    """Base exception for all HACP protocol errors."""
    reason_code: str = "UNKNOWN_ERROR"

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(f"[{self.reason_code}] {message}")


class SchemaValidationError(HACPError):
    """JSON schema validation failed (Gate 1)."""
    reason_code = "INVALID_ENVELOPE"


class SignatureFailureError(HACPError):
    """Ed25519 signature verification failed."""
    reason_code = "SIGNATURE_FAILURE"


class KeyRevokedError(HACPError):
    """Signer key is present in revocation list."""
    reason_code = "KEY_REVOKED"


class EnvelopeRevokedError(HACPError):
    """Intent envelope ID is present in revocation list."""
    reason_code = "ENVELOPE_REVOKED"


class TokenRevokedError(HACPError):
    """Decision token ID is present in revocation list."""
    reason_code = "TOKEN_REVOKED"


class EnvelopeExpiredError(HACPError):
    """Envelope current time > expires_at."""
    reason_code = "ENVELOPE_EXPIRED"


class TokenExpiredError(HACPError):
    """Token current time > expires_at."""
    reason_code = "TOKEN_EXPIRED"


class ScopeExceededError(HACPError):
    """Action violates scope boundary matrix."""
    reason_code = "SCOPE_EXCEEDED"


class BoundaryCrossingError(HACPError):
    """Action crosses audience/reversibility/externality boundary."""
    reason_code = "BOUNDARY_CROSSING"


class BudgetExhaustedError(HACPError):
    """Autonomy budget limit reached."""
    reason_code = "BUDGET_EXHAUSTED"


class TraceabilityFailureError(HACPError):
    """Provenance chain broken or invalid."""
    reason_code = "TRACEABILITY_FAILURE"


class CheckpointRequiredError(HACPError):
    """Action requires human approval via CHECKPOINT flow."""
    reason_code = "CHECKPOINT_REQUIRED"


class ReauthorizeRequiredError(HACPError):
    """Boundary matrix requires re-authorization."""
    reason_code = "REAUTHORIZE_REQUIRED"


# Mapping for parsing sidecar X-HACP-Reason headers
REASON_CODE_MAP = {
    "INVALID_ENVELOPE": SchemaValidationError,
    "SIGNATURE_FAILURE": SignatureFailureError,
    "KEY_REVOKED": KeyRevokedError,
    "ENVELOPE_REVOKED": EnvelopeRevokedError,
    "TOKEN_REVOKED": TokenRevokedError,
    "ENVELOPE_EXPIRED": EnvelopeExpiredError,
    "TOKEN_EXPIRED": TokenExpiredError,
    "SCOPE_EXCEEDED": ScopeExceededError,
    "BOUNDARY_CROSSING": BoundaryCrossingError,
    "BUDGET_EXHAUSTED": BudgetExhaustedError,
    "TRACEABILITY_FAILURE": TraceabilityFailureError,
    "CHECKPOINT_REQUIRED": CheckpointRequiredError,
    "REAUTHORIZE_REQUIRED": ReauthorizeRequiredError,
}


def parse_reason_code(code: str, message: str = "") -> HACPError:
    """Instantiate the correct exception from a sidecar reason code."""
    exc_class = REASON_CODE_MAP.get(code, HACPError)
    return exc_class(message)