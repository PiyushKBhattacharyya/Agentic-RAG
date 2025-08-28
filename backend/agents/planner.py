from typing import Dict, List, Any
from core.llm_client import LLMClient
from core.audit_logger import AuditLogger
import re

class QueryPlanner:
    def __init__(self, llm_client: LLMClient, audit_logger: AuditLogger):
        self.llm = llm_client
        self.audit_logger = audit_logger
    
    def plan_query(self, query: str, session_id: str, context: str = "") -> Dict[str, Any]:
        """Plan the execution strategy for a query"""
        
        planning_prompt = """
        You are a query planner for an invoice-PO matching system. Analyze the query and determine:
        1. What type of query this is (invoice_analysis, approval_request, general_inquiry)
        2. Which agents to call and in what order
        3. What information needs to be retrieved
        
        Available agents:
        - retriever: Get documents from local database
        - po_matcher: Match invoices to purchase orders
        - web_search: Search external sources for vendor/compliance info
        - verifier: Verify results and assess confidence
        
        Query: {query}
        Context: {context}
        
        Respond in JSON format:
        {{
            "query_type": "string",
            "agents_to_call": ["agent1", "agent2"],
            "reasoning": "why this plan",
            "parameters": {{"key": "value"}}
        }}
        """
        
        messages = [
            {"role": "system", "content": planning_prompt.format(query=query, context=context)}
        ]
        
        response = self.llm.chat_completion(messages)
        
        try:
            # Extract JSON from response
            import json
            plan = json.loads(response)
        except:
            # Fallback to rule-based planning
            plan = self._rule_based_plan(query)
        
        # Log the planning decision
        self.audit_logger.log_action(
            session_id=session_id,
            action_type="query_planning",
            agent="planner",
            input_data={"query": query, "context": context},
            output_data=plan
        )
        
        return plan
    
    def _rule_based_plan(self, query: str) -> Dict[str, Any]:
        """Fallback rule-based planning"""
        query_lower = query.lower()
        
        if "approve" in query_lower:
            return {
                "query_type": "approval_request",
                "agents_to_call": ["retriever", "verifier"],
                "reasoning": "User requesting approval action",
                "parameters": {"action": "approve"}
            }
        elif "invoice" in query_lower and ("flag" in query_lower or "why" in query_lower):
            return {
                "query_type": "invoice_analysis",
                "agents_to_call": ["retriever", "po_matcher", "verifier"],
                "reasoning": "Analyzing flagged invoice",
                "parameters": {"analysis_type": "flagged_invoice"}
            }
        else:
            return {
                "query_type": "general_inquiry",
                "agents_to_call": ["retriever", "web_search", "verifier"],
                "reasoning": "General inquiry requiring comprehensive search",
                "parameters": {}
            }