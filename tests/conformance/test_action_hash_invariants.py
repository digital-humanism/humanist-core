"""JCS/action-hash security invariants."""
from __future__ import annotations

from copy import deepcopy

import pytest

from humanist_core.hacp.crypto import canonicalize_json

from .helpers import compute_action_hash, reordered_dict


BASE_ACTION = {
    "hacp_version": "0.9",
    "action_id": "11111111-1111-1111-1111-111111111111",
    "envelope_id": "22222222-2222-2222-2222-222222222222",
    "verb": "read",
    "resource_class": "customer_record",
    "resource_id": "crm://acct/4411",
    "audience": "internal",
    "reversibility": "reversible",
    "externality": "internal",
    "data_class": "internal",
    "proposed_at": 1786000100,
}


def test_action_hash_independent_of_object_field_order():
    reordered = reordered_dict(BASE_ACTION)
    assert canonicalize_json(BASE_ACTION) == canonicalize_json(reordered)
    assert compute_action_hash(BASE_ACTION) == compute_action_hash(reordered)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("audience", "external"),
        ("reversibility", "irreversible"),
        ("externality", "external"),
        ("data_class", "confidential"),
    ],
)
def test_action_hash_changes_with_security_semantics(field, replacement):
    changed = deepcopy(BASE_ACTION)
    changed[field] = replacement
    assert compute_action_hash(BASE_ACTION) != compute_action_hash(changed)
