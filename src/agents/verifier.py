from __future__ import annotations
from typing import List
from ..types import Evidence, VerifierResult


def _safe_div(a: float, b: float) -> float:
    return 0.0 if b == 0 else a / b


def verify_invoice(evidence: Evidence) -> VerifierResult:
    if not evidence.invoice_lines:
        return VerifierResult(flagged=True, match_score=0.0, confidence=0.9, reasons=["Invoice not found in local data"]) 

    # Aggregate by item for simplicity
    inv_total = sum(x.amount for x in evidence.invoice_lines)
    po_map = {(p.item, p.po_number): p for p in evidence.po_lines}
    reasons: List[str] = []

    expected_total = 0.0
    price_variances = []
    qty_shortfalls = []

    for inv in evidence.invoice_lines:
        key = (inv.item, inv.po_number)
        po = po_map.get(key)
        if not po:
            reasons.append(f"No PO line for item '{inv.item}' on {inv.po_number}")
            continue
        expected_total += po.quantity * po.unit_price
        price_variances.append((inv.unit_price - po.unit_price) / max(po.unit_price, 1e-9))

        # Receipt coverage for this item
        received_qty = sum(r.quantity_received for r in evidence.receipts if r.item == inv.item and r.po_number == inv.po_number)
        qty_shortfalls.append((inv.quantity - received_qty) / max(inv.quantity, 1e-9))

    # Scores
    avg_price_var = sum(abs(v) for v in price_variances) / max(len(price_variances), 1)
    avg_qty_short = sum(max(0.0, q) for q in qty_shortfalls) / max(len(qty_shortfalls), 1)

    total_var = abs(inv_total - expected_total) / max(expected_total, 1e-9)

    # Heuristic match score: 1.0 is perfect, penalize deviations
    match_score = max(0.0, 1.0 - (0.5 * total_var + 0.3 * avg_price_var + 0.2 * avg_qty_short))

    flagged = (total_var > 0.05) or (avg_price_var > 0.05) or (avg_qty_short > 0.05) or (len(reasons) > 0)

    # Confidence increases with magnitude of discrepancy
    discrepancy = max(total_var, avg_price_var, avg_qty_short)
    confidence = min(0.95, 0.5 + 0.4 * min(1.0, discrepancy * 5))

    if avg_price_var > 0.05:
        reasons.append(f"Unit price variance avg={avg_price_var:.1%} exceeds tolerance")
    if avg_qty_short > 0.05:
        reasons.append(f"Goods receipt shortfall avg={avg_qty_short:.1%} vs invoiced quantity")
    if total_var > 0.05:
        reasons.append(f"Total amount variance={total_var:.1%} (invoice vs PO)")

    return VerifierResult(flagged=flagged, match_score=match_score, confidence=confidence, reasons=reasons)