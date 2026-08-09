"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3
"""
import hashlib
import warnings
from collections import deque


class AutonomousLoopDetected(Exception):
    """Raised when a blind machine-to-machine chain is detected."""
    pass


class MasqueradeDetected(Exception):
    """Raised when an AI attempts to masquerade as a human (cognitive limits exceeded)."""
    pass


class CognitiveFrictionRequired(Exception):
    """Requires human intervention to confirm meaning."""
    pass


class CognitiveLoadAnalyzer:
    """
    Calculates the minimum time required for a biological brain
    to process and analyze information.
    """
    READING_SPEED_WPM = 250
    DEEP_ANALYSIS_WPM = 100
    TYPING_SPEED_WPM = 60

    @classmethod
    def calculate_minimum_human_time(cls, input_text: str, output_text: str) -> float:
        """Returns the minimum time in seconds required for a human."""
        input_words = len(input_text.split())
        output_words = len(output_text.split())

        # Time for deep reading of the input
        reading_time = (input_words / cls.DEEP_ANALYSIS_WPM) * 60

        # Time for thinking and typing the output
        thinking_and_typing_time = (output_words / cls.TYPING_SPEED_WPM) * 60

        # Base penalty for context switching (cognitive friction)
        context_switch_penalty = 10.0

        return reading_time + thinking_and_typing_time + context_switch_penalty


class DigitalBlockAnalyzer:
    """
    Structural entropy detector for bot farm identification.

    Uses sentence-transformers embeddings with cosine similarity to detect
    low-entropy (structurally repetitive) text streams typical of LLM bot
    farms. Falls back to structural hashing if embeddings are unavailable.
    """

    def __init__(self, window_size: int = 10, similarity_threshold: float = 0.5,
                 model_name: str = "all-MiniLM-L6-v2"):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.model_name = model_name

        # Lazy loading: model is only loaded on first use
        self._model = None
        self._use_embeddings = True

        self.recent_blocks = deque(maxlen=window_size)
        self.recent_embeddings = deque(maxlen=window_size)

    def _load_model(self):
        """Lazy load the sentence-transformer model on first use."""
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        except ImportError:
            warnings.warn(
                "sentence-transformers not installed. Falling back to structural "
                "hashing. Install with: pip install sentence-transformers",
                RuntimeWarning,
            )
            self._use_embeddings = False
        return self._model

    def _get_structural_hash(self, text: str) -> str:
        """Fallback: structural hash for when embeddings are unavailable."""
        normalized = "".join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    @staticmethod
    def _cosine_similarity(vec1, vec2) -> float:
        """Cosine similarity between two vectors."""
        import numpy as np
        dot = np.dot(vec1, vec2)
        norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        if norm == 0:
            return 0.0
        return float(dot / norm)

    def check_similarity(self, text: str) -> float:
        """
        Returns a suspicion score (0.0 - 1.0).

        With embeddings: average cosine similarity between the current block
        and the recent window. Without embeddings: exact-match ratio of
        structural hashes.
        """
        if not self._use_embeddings:
            return self._fallback_check(text)

        model = self._load_model()
        if model is None:
            return self._fallback_check(text)

        current_embedding = model.encode(text)

        if len(self.recent_embeddings) == 0:
            self.recent_embeddings.append(current_embedding)
            return 0.0

        similarities = [
            self._cosine_similarity(current_embedding, past)
            for past in self.recent_embeddings
        ]
        avg_similarity = sum(similarities) / len(similarities)

        self.recent_embeddings.append(current_embedding)
        return avg_similarity

    def _fallback_check(self, text: str) -> float:
        """Fallback method using structural hashing (exact match only)."""
        current_block = self._get_structural_hash(text)
        matches = sum(1 for block in self.recent_blocks if block == current_block)
        similarity_score = (
            matches / len(self.recent_blocks) if self.recent_blocks else 0.0
        )
        self.recent_blocks.append(current_block)
        return similarity_score


class AgencyGuardV2:
    """
    Intercepts M2M loops and detects cognitive anomalies.
    """
    def __init__(self):
        self.cognitive_analyzer = CognitiveLoadAnalyzer()
        self.vector_analyzer = DigitalBlockAnalyzer(
            window_size=10, similarity_threshold=0.5
        )

    def intercept_human_input(self, session_id: str, input_text: str,
                              response_text: str, elapsed_time_sec: float):
        """
        Called when the system receives a response from an actor
        claiming to be HUMAN.
        """
        min_required_time = self.cognitive_analyzer.calculate_minimum_human_time(
            input_text, response_text
        )

        if elapsed_time_sec < min_required_time:
            raise MasqueradeDetected(
                f"Cognitive anomaly! Processed {len(input_text.split())} words "
                f"in {elapsed_time_sec:.2f}s. "
                f"Minimum biological requirement: {min_required_time:.2f}s."
            )

        similarity_score = self.vector_analyzer.check_similarity(response_text)
        if similarity_score >= self.vector_analyzer.similarity_threshold:
            print(
                f"[VECTOR ALERT] Structural block similarity: "
                f"{similarity_score*100:.1f}%. Possible AI generation."
            )

        return True
