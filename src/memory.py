from __future__ import annotations
from typing import Any, Dict


class ShortMemory:
    """Ephemeral short-term memory for demo follow-ups."""

    def __init__(self):
        self.state: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self.state[key] = value

    def get(self, key: str, default=None):
        return self.state.get(key, default)