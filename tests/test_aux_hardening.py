"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 5.1: Legacy Coverage Hardening.
    Targeted tests for auxiliary subsystems: SafeHarborLedger (intent log)
    and AgencyGuard (loop breaker). See ARCHITECTURE.md (Agency Guard).
"""
import pytest

from humanist_core.safe_harbor import IntentRecord, SafeHarborLedger


class TestIntentRecordSerialization:
    def test_to_dict_returns_all_fields(self):
        """Line 25: to_dict serializes the dataclass to a dict."""
        record = IntentRecord(
            record_id="abc123",
            timestamp="2026-08-10T00:00:00+00:00",
            prev_hash="0" * 64,
            intent="review quarterly report",
            context_hash="f" * 64,
            user_stance="Approved",
            consent_training=False,
        )
        result = record.to_dict()
        assert result["record_id"] == "abc123"
        assert result["intent"] == "review quarterly report"
        assert result["jurisdiction"] == "LOCAL_NODE"
        assert result["consent_training"] is False


class TestLedgerCorruptionRecovery:
    def test_corrupted_chain_falls_back_to_genesis(self, tmp_path):
        """Lines 50-51: unreadable/corrupted chain returns GENESIS_HASH."""
        chain_file = tmp_path / "corrupted_chain.jsonl"
        chain_file.write_text("this is not valid json\n", encoding="utf-8")

        ledger = SafeHarborLedger(path=str(chain_file))
        assert ledger.last_hash == SafeHarborLedger.GENESIS_HASH

import sys

import numpy as np
import pytest

from humanist_core.loop_breaker import AgencyGuardV2, DigitalBlockAnalyzer
from humanist_core.safe_harbor import IntentRecord, SafeHarborLedger





class TestDigitalBlockAnalyzerFallbacks:
    def test_import_error_falls_back_and_warns(self, monkeypatch):
        """Lines 83-89: missing sentence-transformers degrades to structural hashing."""
        analyzer = DigitalBlockAnalyzer()
        monkeypatch.setitem(sys.modules, "sentence_transformers", None)
        with pytest.warns(RuntimeWarning, match="sentence-transformers not installed"):
            model = analyzer._load_model()
        assert model is None
        assert analyzer._use_embeddings is False

    def test_check_similarity_falls_back_when_model_unavailable(self, monkeypatch):
        """Line 120: check_similarity uses structural fallback when model is None."""
        analyzer = DigitalBlockAnalyzer()
        monkeypatch.setitem(sys.modules, "sentence_transformers", None)
        with pytest.warns(RuntimeWarning):
            score = analyzer.check_similarity("hello world")
        assert score == 0.0

    def test_cosine_similarity_zero_norm(self):
        """Line 104: zero-norm vectors return 0.0 instead of dividing by zero."""
        score = DigitalBlockAnalyzer._cosine_similarity(
            np.array([0.0, 0.0]), np.array([1.0, 1.0])
        )
        assert score == 0.0


class TestAgencyGuardVectorAlert:
    def test_vector_alert_printed_on_repeated_blocks(self, capsys):
        """Line 177: high structural similarity triggers the vector alert."""
        guard = AgencyGuardV2()
        guard.vector_analyzer._use_embeddings = False  # deterministic structural mode

        guard.intercept_human_input("s1", "some input words here", "repeated block", 999.0)
        result = guard.intercept_human_input("s1", "some input words here", "repeated block", 999.0)

        assert result is True
        captured = capsys.readouterr()
        assert "[VECTOR ALERT]" in captured.out