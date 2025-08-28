import json
import os
import time
from datetime import datetime
from typing import Any, Dict


class AuditLogger:
    """Simple JSONL audit logger. Each log line is a JSON object with ts, type and data."""

    def __init__(self, base_dir: str = "logs", session_id: str | None = None):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.session_id = session_id or datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        self.path = os.path.join(self.base_dir, f"audit-{self.session_id}.jsonl")

    def log(self, event_type: str, data: Dict[str, Any]):
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": event_type,
            "data": data,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def path_str(self) -> str:
        return self.path


def now_ms() -> int:
    return int(time.time() * 1000)