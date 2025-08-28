from __future__ import annotations
import re
from typing import Dict, Any


def extract_invoice_id(query: str) -> str | None:
    m = re.search(r"(INV[- ]?\d+)", query, re.IGNORECASE)
    return m.group(1).replace(" ", "-").upper() if m else None


def plan(query: str) -> Dict[str, Any]:
    invoice_id = extract_invoice_id(query)
    steps = []
    if invoice_id:
        steps.append({"action": "retrieve_local", "args": {"invoice_id": invoice_id}})
        steps.append({"action": "web_search", "args": {"query": f"invoice {invoice_id} matching policy price variance tolerance"}})
        steps.append({"action": "verify"})
        steps.append({"action": "synthesize"})
    else:
        steps.append({"action": "web_search", "args": {"query": query}})
        steps.append({"action": "synthesize"})
    return {"invoice_id": invoice_id, "steps": steps}