"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3
"""
import time
import hashlib
from collections import deque
from typing import List, Optional

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
    Stub for vector analysis.
    Detects structural repetition (low entropy) typical of LLM bot farms.
    """
    def __init__(self, window_size: int = 10, similarity_threshold: float = 0.5):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.recent_blocks = deque(maxlen=window_size)

    def _get_structural_hash(self, text: str) -> str:
        # In production, this should use embeddings or AST structural hashing.
        normalized = "".join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def check_similarity(self, text: str) -> float:
        """Returns a suspicion score (0.0 - 1.0)."""
        current_block = self._get_structural_hash(text)
        
        # Vector Stub:
        # Should calculate cosine similarity between current block and history.
        matches = sum(1 for block in self.recent_blocks if block == current_block)
        similarity_score = matches / len(self.recent_blocks) if self.recent_blocks else 0.0
        
        self.recent_blocks.append(current_block)
        return similarity_score

class AgencyGuardV2:
    """
    Intercepts M2M loops and detects cognitive anomalies.
    """
    def __init__(self):
        self.cognitive_analyzer = CognitiveLoadAnalyzer()
        self.vector_analyzer = DigitalBlockAnalyzer(window_size=10, similarity_threshold=0.5)

    def intercept_human_input(self, session_id: str, input_text: str, response_text: str, elapsed_time_sec: float):
        """
        Called when the system receives a response from an actor claiming to be HUMAN.
        """
        min_required_time = self.cognitive_analyzer.calculate_minimum_human_time(input_text, response_text)
        
        if elapsed_time_sec < min_required_time:
            raise MasqueradeDetected(
                f"Cognitive anomaly! Processed {len(input_text.split())} words in {elapsed_time_sec:.2f}s. "
                f"Minimum biological requirement: {min_required_time:.2f}s."
            )

        similarity_score = self.vector_analyzer.check_similarity(response_text)
        if similarity_score >= self.vector_analyzer.similarity_threshold:
            print(f"[VECTOR ALERT] Structural block similarity: {similarity_score*100}%. Possible AI generation.")
            
        return True