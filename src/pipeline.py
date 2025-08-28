from __future__ import annotations
from typing import Dict, Any
from .audit import make_logger
from .memory import ShortMemory
from .retrieval.local_loader import load_data
from .retrieval.web_search import web_search
from .agents.planner import plan, extract_invoice_id
from .agents.retriever import retrieve_local, attach_web_results
from .agents.verifier import verify_invoice
from .agents.synthesizer import synthesize_answer


class Pipeline:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.memory = ShortMemory()

    def handle(self, query: str) -> Dict[str, Any]:
        logger = make_logger()
        logger.log("query", {"query": query})

        # Simple follow-up: "approve it"
        if query.strip().lower().startswith("approve"):
            last = self.memory.get("last_result")
            invoice_id = self.memory.get("last_invoice")
            if not last:
                msg = "No prior invoice context to approve. Ask 'Why was invoice INV-123 flagged?' first."
                logger.log("followup_error", {"message": msg})
                return {"message": msg, "audit_log_path": logger.path_str()}
            # Always require human confirmation in demo
            reply = {
                "message": f"Request to approve {invoice_id} recorded. Human confirmation required per policy.",
                "policy": "Human-in-the-loop required for financial actions.",
                "prior_verifier_confidence": last["verifier_confidence"],
                "audit_log_path": logger.path_str(),
            }
            logger.log("followup", reply)
            return reply

        pl = plan(query)
        logger.log("plan", pl)

        dfs = load_data(self.data_dir)
        evidence = retrieve_local(pl.get("invoice_id"), dfs) if pl.get("invoice_id") else None
        if evidence:
            logger.log("retrieve_local", {"invoice_id": pl.get("invoice_id"), "counts": {
                "invoice_lines": len(evidence.invoice_lines),
                "po_lines": len(evidence.po_lines),
                "receipts": len(evidence.receipts),
            }})

        web = web_search(pl.get("invoice_id") or query)
        if evidence:
            evidence = attach_web_results(evidence, web)
        logger.log("web_search", {"results": web})

        verdict = verify_invoice(evidence) if evidence else None
        logger.log("verify", verdict.model_dump() if verdict else {"skipped": True})

        answer = synthesize_answer(query, evidence, verdict, logger.path_str())
        logger.log("synthesize", {"len": len(answer.explanation)})

        # memory for follow-up
        invoice_id = pl.get("invoice_id") or extract_invoice_id(query)
        if invoice_id:
            self.memory.set("last_invoice", invoice_id)
        self.memory.set("last_result", answer.model_dump())

        return answer.model_dump()