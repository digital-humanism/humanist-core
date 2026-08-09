"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3
"""
import json

from humanist_core.safe_harbor import SafeHarborLedger


class TestSafeHarborLedger:
    def test_chain_integrity(self, tmp_path):
        ledger = SafeHarborLedger(path=str(tmp_path / "chain.jsonl"))
        ledger.log_intent("RESEARCH", "prompt one", "approved")
        ledger.log_intent("RESEARCH", "prompt two", "approved")
        assert ledger.verify_integrity() is True

    def test_tamper_detected(self, tmp_path):
        path = tmp_path / "chain.jsonl"
        ledger = SafeHarborLedger(path=str(path))
        ledger.log_intent("RESEARCH", "prompt one", "approved")
        ledger.log_intent("RESEARCH", "prompt two", "approved")

        # Tamper with the first record
        lines = path.read_text().splitlines()
        record = json.loads(lines[0])
        record["user_stance"] = "TAMPERED"
        lines[0] = json.dumps(record)
        path.write_text("\n".join(lines) + "\n")

        reopened = SafeHarborLedger(path=str(path))
        assert reopened.verify_integrity() is False