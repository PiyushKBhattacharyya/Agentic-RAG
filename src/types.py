from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict, Any


class InvoiceLine(BaseModel):
    invoice_id: str
    po_number: str
    item: str
    quantity: float
    unit_price: float
    amount: float


class POLine(BaseModel):
    po_number: str
    item: str
    quantity: float
    unit_price: float
    amount: float


class ReceiptLine(BaseModel):
    receipt_id: str
    po_number: str
    item: str
    quantity_received: float


class Evidence(BaseModel):
    invoice_lines: List[InvoiceLine]
    po_lines: List[POLine]
    receipts: List[ReceiptLine]
    web_results: List[Dict[str, Any]]
    source_offsets: Dict[str, List[int]]  # dataset -> row indices


class VerifierResult(BaseModel):
    flagged: bool
    match_score: float
    confidence: float
    reasons: List[str]


class FinalAnswer(BaseModel):
    explanation: str
    evidence_summary: Dict[str, Any]
    match_score: float
    verifier_confidence: float
    audit_log_path: str
    memory_note: str | None = None