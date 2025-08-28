from __future__ import annotations
from .utils.logger import AuditLogger


def make_logger(session_id: str | None = None) -> AuditLogger:
    return AuditLogger(base_dir="logs", session_id=session_id)