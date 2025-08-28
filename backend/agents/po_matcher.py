from typing import Dict, List, Any, Tuple
from core.llm_client import LLMClient
from core.audit_logger import AuditLogger
from agents.retriever import DocumentRetriever

class POMatchingAgent:
    def __init__(self, llm_client: LLMClient, audit_logger: AuditLogger, retriever: DocumentRetriever):
        self.llm = llm_client
        self.audit_logger = audit_logger
        self.retriever = retriever
    
    def match_invoice_to_po(self, invoice_id: str, session_id: str) -> Dict[str, Any]:
        """Match invoice to purchase orders and analyze discrepancies"""
        
        # Get invoice details
        invoice = self.retriever.get_specific_document(invoice_id, "invoices")
        if not invoice:
            return {"error": f"Invoice {invoice_id} not found"}
        
        # Get related PO
        po_id = invoice.get('po_reference')
        purchase_order = None
        goods_receipt = None
        
        if po_id:
            purchase_order = self.retriever.get_specific_document(po_id, "purchase_orders")
            goods_receipt = self.retriever.get_specific_document(po_id, "goods_receipts")
        
        # Perform matching analysis
        match_result = self._analyze_three_way_match(invoice, purchase_order, goods_receipt)
        
        # Log the matching process
        self.audit_logger.log_action(
            session_id=session_id,
            action_type="po_matching",
            agent="po_matcher",
            input_data={"invoice_id": invoice_id},
            output_data=match_result
        )
        
        return match_result
    
    def _analyze_three_way_match(self, invoice: Dict, po: Dict = None, 
                                gr: Dict = None) -> Dict[str, Any]:
        """Perform three-way matching analysis"""
        
        discrepancies = []
        match_score = 1.0
        
        if not po:
            discrepancies.append("No matching purchase order found")
            match_score -= 0.4
        
        if not gr:
            discrepancies.append("No goods receipt found")
            match_score -= 0.2
        
        # Check amounts
        if po and invoice:
            invoice_total = float(invoice.get('total_amount', 0))
            po_total = float(po.get('total_amount', 0))
            
            if abs(invoice_total - po_total) > 0.01:
                diff = abs(invoice_total - po_total)
                discrepancies.append(f"Amount mismatch: Invoice ${invoice_total:.2f} vs PO ${po_total:.2f} (diff: ${diff:.2f})")
                match_score -= min(0.3, diff / po_total)
        
        # Check vendor
        if po and invoice:
            if invoice.get('vendor') != po.get('vendor'):
                discrepancies.append(f"Vendor mismatch: Invoice '{invoice.get('vendor')}' vs PO '{po.get('vendor')}'")
                match_score -= 0.2
        
        # Check line items
        if po and invoice:
            line_item_issues = self._check_line_items(invoice.get('line_items', []), 
                                                    po.get('line_items', []))
            discrepancies.extend(line_item_issues)
            match_score -= len(line_item_issues) * 0.1
        
        match_score = max(0, match_score)  # Ensure non-negative
        
        # Determine flag reason
        flag_reason = "No issues found" if match_score > 0.8 else "Failed validation checks"
        
        return {
            "invoice": invoice,
            "purchase_order": po,
            "goods_receipt": gr,
            "match_score": round(match_score, 2),
            "discrepancies": discrepancies,
            "flag_reason": flag_reason,
            "evidence": {
                "invoice_amount": invoice.get('total_amount') if invoice else None,
                "po_amount": po.get('total_amount') if po else None,
                "vendor": invoice.get('vendor') if invoice else None
            }
        }
    
    def _check_line_items(self, invoice_lines: List[Dict], po_lines: List[Dict]) -> List[str]:
        """Check line item matching"""
        issues = []
        
        if len(invoice_lines) != len(po_lines):
            issues.append(f"Line item count mismatch: Invoice has {len(invoice_lines)}, PO has {len(po_lines)}")
        
        # Simple line matching - in production would be more sophisticated
        for i, inv_line in enumerate(invoice_lines):
            if i < len(po_lines):
                po_line = po_lines[i]
                if inv_line.get('quantity') != po_line.get('quantity'):
                    issues.append(f"Quantity mismatch on line {i+1}")
                if inv_line.get('unit_price') != po_line.get('unit_price'):
                    issues.append(f"Unit price mismatch on line {i+1}")
        
        return issues