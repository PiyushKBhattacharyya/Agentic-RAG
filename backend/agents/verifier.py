from typing import Dict, List, Any
from core.llm_client import LLMClient
from core.audit_logger import AuditLogger

class ResultVerifier:
    def __init__(self, llm_client: LLMClient, audit_logger: AuditLogger):
        self.llm = llm_client
        self.audit_logger = audit_logger
        self.confidence_threshold = 0.7
    
    def verify_results(self, agent_results: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Verify and synthesize results from multiple agents"""
        
        verification_prompt = """
        You are a result verifier for an invoice-PO matching system. 
        Analyze the following agent results and provide:
        1. Overall confidence score (0-1)
        2. Key findings summary
        3. Risk assessment
        4. Recommended actions
        5. Any conflicts between agent outputs
        
        Agent Results: {results}
        
        Respond in JSON format with fields: confidence, summary, risks, recommendations, conflicts
        """
        
        messages = [
            {"role": "system", "content": verification_prompt.format(results=str(agent_results))}
        ]
        
        verification_text = self.llm.chat_completion(messages)
        
        # Parse verification results
        try:
            import json
            verification = json.loads(verification_text)
        except:
            # Fallback verification
            verification = self._fallback_verification(agent_results)
        
        # Add confidence-based routing
        verification["requires_human_review"] = verification.get("confidence", 0) < self.confidence_threshold
        
        # Log verification
        self.audit_logger.log_action(
            session_id=session_id,
            action_type="result_verification",
            agent="verifier",
            input_data=agent_results,
            output_data=verification
        )
        
        return verification
    
    def _fallback_verification(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback verification logic"""
        
        confidence = 0.8  # Default confidence
        risks = []
        recommendations = []
        
        # Check match score if available
        if "match_score" in results:
            match_score = results["match_score"]
            confidence = match_score
            
            if match_score < 0.5:
                risks.append("Low match score indicates significant discrepancies")
                recommendations.append("Manual review required before approval")
            elif match_score < 0.8:
                risks.append("Moderate discrepancies found")
                recommendations.append("Supervisor approval recommended")
        
        # Check discrepancies
        discrepancies = results.get("discrepancies", [])
        if len(discrepancies) > 2:
            confidence *= 0.8
            risks.append("Multiple discrepancies detected")
        
        return {
            "confidence": round(confidence, 2),
            "summary": f"Analysis complete with {len(discrepancies)} discrepancies found",
            "risks": risks,
            "recommendations": recommendations,
            "conflicts": []
        }