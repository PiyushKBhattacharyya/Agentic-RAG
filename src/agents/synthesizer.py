from __future__ import annotations
import os
from typing import Dict, Any
from openai import OpenAI
from ..types import Evidence, VerifierResult, FinalAnswer


def _openai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def synthesize_answer(query: str, evidence: Evidence, verdict: VerifierResult, audit_path: str) -> FinalAnswer:
    client = _openai_client()
    sources_str = (
        f"invoices.csv rows={evidence.source_offsets.get('invoices.csv', [])}; "
        f"pos.csv rows={evidence.source_offsets.get('pos.csv', [])}; "
        f"receipts.csv rows={evidence.source_offsets.get('receipts.csv', [])}"
    )

    evidence_summary: Dict[str, Any] = {
        "invoice_lines": [x.model_dump() for x in evidence.invoice_lines],
        "po_lines": [x.model_dump() for x in evidence.po_lines],
        "receipts": [x.model_dump() for x in evidence.receipts],
        "web": evidence.web_results,
        "sources": sources_str,
    }

    system = (
        "You are an accounts payable assistant. Answer briefly (120-200 words) "
        "and always include a 'Sources' section listing dataset names and row indices provided."
    )

    user = (
        f"Question: {query}\n\n"
        f"Verifier flagged: {verdict.flagged} | match_score={verdict.match_score:.2f} | "
        f"confidence={verdict.confidence:.2f}\n"
        f"Reasons: {verdict.reasons}\n\n"
        f"Evidence (summarized): {evidence_summary}"
    )

    if client:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
            )
            text = resp.choices[0].message.content.strip()
        except Exception:
            text = _fallback_text(verdict, sources_str)
    else:
        text = _fallback_text(verdict, sources_str)

    return FinalAnswer(
        explanation=text,
        evidence_summary=evidence_summary,
        match_score=verdict.match_score,
        verifier_confidence=verdict.confidence,
        audit_log_path=audit_path,
        memory_note=None,
    )


def _fallback_text(verdict: VerifierResult, sources: str) -> str:
    reasons = "; ".join(verdict.reasons) if verdict.reasons else "No variance detected."
    return (
        f"Invoice status: {'FLAGGED' if verdict.flagged else 'OK'}\n"
        f"Match score: {verdict.match_score:.2f}, Verifier confidence: {verdict.confidence:.2f}\n"
        f"Reasons: {reasons}\n\n"
        f"Sources: {sources}"
    )