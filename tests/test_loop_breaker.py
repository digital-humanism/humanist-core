"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3
"""
import pytest

from humanist_core.loop_breaker import (
    AgencyGuardV2,
    CognitiveLoadAnalyzer,
    DigitalBlockAnalyzer,
    MasqueradeDetected,
)


class TestCognitiveLoadAnalyzer:
    def test_minimum_human_time_formula(self):
        # 100 words @100 WPM = 60s; 60 words @60 WPM = 60s; +10s penalty
        t = CognitiveLoadAnalyzer.calculate_minimum_human_time("w " * 100, "w " * 60)
        assert t == pytest.approx(130.0)

    def test_masquerade_detected_on_impossible_speed(self):
        guard = AgencyGuardV2()
        guard.vector_analyzer._use_embeddings = False  # keep test dependency-free
        with pytest.raises(MasqueradeDetected):
            guard.intercept_human_input(
                "s1", "word " * 3600, "word " * 500, elapsed_time_sec=15
            )

    def test_human_plausible_time_passes(self):
        guard = AgencyGuardV2()
        guard.vector_analyzer._use_embeddings = False
        # min = 30 + 20 + 10 = 60s; elapsed 120s is plausible
        assert guard.intercept_human_input("s2", "word " * 50, "word " * 20, 120)


class TestDigitalBlockAnalyzerFallback:
    def test_identical_blocks_flagged(self):
        a = DigitalBlockAnalyzer(window_size=5, similarity_threshold=0.5)
        a._use_embeddings = False
        score = 0.0
        for _ in range(6):
            score = a.check_similarity("the same message")
        assert score >= 0.5

    def test_diverse_blocks_not_flagged(self):
        a = DigitalBlockAnalyzer(window_size=5, similarity_threshold=0.5)
        a._use_embeddings = False
        score = 0.0
        for i in range(6):
            score = a.check_similarity(f"unique message number {i}")
        assert score < 0.5


class TestDigitalBlockAnalyzerEmbeddings:
    @pytest.fixture()
    def analyzer(self):
        pytest.importorskip("sentence_transformers")
        return DigitalBlockAnalyzer(window_size=10, similarity_threshold=0.5)

    def test_bot_farm_paraphrases_flagged(self, analyzer):
        messages = [
            "The new policy is harmful for our community and must be stopped.",
            "This new policy is dangerous for our community and should be stopped.",
            "The latest policy is harmful to our community and must end.",
            "Our community suffers from this harmful new policy; it must stop.",
            "The new policy harms our community and needs to be stopped now.",
        ]
        score = 0.0
        for m in messages:
            score = analyzer.check_similarity(m)
        assert score >= 0.5

    def test_human_diversity_not_flagged(self, analyzer):
        messages = [
            "Can you help me fix a bug in my Python script?",
            "The weather in Lisbon was amazing last spring.",
            "I need a recipe for sourdough bread without yeast.",
            "How do I configure nginx as a reverse proxy?",
            "My cat keeps knocking over the water glass at night.",
        ]
        score = 0.0
        for m in messages:
            score = analyzer.check_similarity(m)
        assert score < 0.5