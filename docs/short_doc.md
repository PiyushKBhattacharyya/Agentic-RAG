# Short Doc

- **Use-case**: Explain why an invoice was flagged and show evidence (invoice, PO, receipts), plus a match score, verifier confidence, and an audit log of steps.
- **Implemented**: end-to-end minimal pipeline with planner → retrieval (local + web) → verifier → synthesizer → memory and audit log. Follow-up command "Approve it" returns a mock response requiring human confirmation.
- **Omitted**: multi-agent expansion, embeddings/vector DB, complex planner, long-term memory, cloud integrations.
- **Limitations**: heuristic verifier; shallow web fusion; ephemeral memory; CSV-only storage; manual thresholds.
- **Next Steps**: add embeddings & reranking, richer planner and toolset, structured approvals with policy thresholds, unit tests and CI, privacy and redaction filters.
- **Process**: started from minimal retriever and verifier to ensure reliability, added provenance, and layered a simple planner and audit logging; kept follow-up interactions safe by enforcing human confirmation.