"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class IntentRecord:
    record_id: str
    timestamp: str
    prev_hash: str
    intent: str
    context_hash: str
    user_stance: str
    consent_training: bool
    jurisdiction: str = "LOCAL_NODE"

    def to_dict(self) -> Dict:
        return asdict(self)

class SafeHarborLedger:
    """
    Local, append-only ledger for logging human intent.
    Uses a hash-chain structure to ensure cryptographic integrity.
    """
    GENESIS_HASH = "0" * 64

    def __init__(self, path: str = "safe_harbor_chain.jsonl"):
        self.path = path
        self.last_hash = self._get_last_hash()

    def _sha256(self, data: str) -> str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _get_last_hash(self) -> str:
        if not os.path.exists(self.path):
            return self.GENESIS_HASH
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    return self.GENESIS_HASH
                last_entry = json.loads(lines[-1])
                return last_entry.get('record_hash', self.GENESIS_HASH)
        except:
            return self.GENESIS_HASH

    def _calculate_hash(self, record_data: Dict, prev_hash: str) -> str:
        raw_data = json.dumps(record_data, sort_keys=True) + prev_hash
        return self._sha256(raw_data)

    def log_intent(self, intent: str, prompt: str, stance: str, allow_training: bool = False) -> str:
        """
        Logs the user's intent. Stores only the SHA-256 hash of the prompt
        to maintain privacy (Zero-Knowledge Privacy).
        """
        record_id = self._sha256(f"{datetime.now().timestamp()}_{prompt}")[:16]
        timestamp = datetime.now(timezone.utc).isoformat()
        context_hash = self._sha256(prompt)

        record_data = {
            "record_id": record_id,
            "timestamp": timestamp,
            "prev_hash": self.last_hash,
            "intent": intent,
            "context_hash": context_hash,
            "user_stance": stance,
            "consent_training": allow_training
        }

        record_hash = self._calculate_hash(record_data, self.last_hash)
        full_entry = {**record_data, "record_hash": record_hash}

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(full_entry) + "\n")
            
        self.last_hash = record_hash
        return record_id

    def verify_integrity(self) -> bool:
        """Verifies that the hash-chain has not been tampered with."""
        prev_hash = self.GENESIS_HASH
        if not os.path.exists(self.path): return True
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                current_hash = entry.pop("record_hash")
                if self._calculate_hash(entry, prev_hash) != current_hash:
                    return False
                prev_hash = current_hash
        return True