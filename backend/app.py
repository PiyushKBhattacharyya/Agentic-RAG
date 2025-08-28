from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv

from core.llm_client import LLMClient
from core.memory import ConversationMemory
from core.audit_logger import AuditLogger
from agents.planner import QueryPlanner
from agents.retriever import DocumentRetriever
from agents.po_matcher import POMatchingAgent
from agents.web_search import WebSearchAgent
from agents.verifier import ResultVerifier

load_dotenv()

app = Flask(__name__, static_folder='../frontend/static/', static_url_path='')
CORS(app)

# Initialize components
llm_client = LLMClient()
memory = ConversationMemory()
audit_logger = AuditLogger()

# Initialize agents
retriever = DocumentRetriever(llm_client, audit_logger)
planner = QueryPlanner(llm_client, audit_logger)
po_matcher = POMatchingAgent(llm_client, audit_logger, retriever)
web_search = WebSearchAgent(llm_client, audit_logger)
verifier = ResultVerifier(llm_client, audit_logger)

@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory('../frontend/static/', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('../frontend/static/', filename)

@app.route('/api/query', methods=['POST'])
def handle_query():
    """Main query endpoint"""
    data = request.json
    query = data.get('query', '')
    session_id = data.get('session_id', '')
    
    if not session_id:
        session_id = memory.create_session()
    
    # Get conversation context
    context = memory.get_context(session_id)
    
    # Plan the query
    plan = planner.plan_query(query, session_id, context)
    
    # Execute plan
    agent_results = {}
    
    if "retriever" in plan.get("agents_to_call", []):
        agent_results["retrieval"] = retriever.retrieve_documents(query, session_id)
    
    if "po_matcher" in plan.get("agents_to_call", []):
        # Extract invoice ID from query
        invoice_id = extract_invoice_id(query)
        if invoice_id:
            agent_results["po_matching"] = po_matcher.match_invoice_to_po(invoice_id, session_id)
    
    if "web_search" in plan.get("agents_to_call", []):
        # Extract vendor from results or query
        vendor = extract_vendor_name(query, agent_results)
        if vendor:
            agent_results["web_search"] = web_search.search_vendor_info(vendor, session_id)
    
    # Verify results
    verification = verifier.verify_results(agent_results, session_id)
    
    # Synthesize final response
    final_response = synthesize_response(query, agent_results, verification, plan)
    final_response["session_id"] = session_id
    final_response["audit_trail"] = audit_logger.get_session_logs(session_id)
    
    # Store in memory
    memory.add_interaction(session_id, query, final_response)
    
    return jsonify(final_response)

@app.route('/api/approve', methods=['POST'])
def approve_invoice():
    """Approve invoice endpoint"""
    data = request.json
    invoice_id = data.get('invoice_id', '')
    session_id = data.get('session_id', '')
    
    # Log approval action
    audit_logger.log_action(
        session_id=session_id,
        action_type="invoice_approval",
        agent="system",
        input_data={"invoice_id": invoice_id},
        output_data={"status": "approved", "approved_by": "user"}
    )
    
    response = {
        "status": "success",
        "message": f"Invoice {invoice_id} has been approved",
        "invoice_id": invoice_id,
        "requires_confirmation": True
    }
    
    return jsonify(response)

def extract_invoice_id(query: str) -> str:
    """Extract invoice ID from query"""
    import re
    match = re.search(r'INV-\d+', query)
    return match.group(0) if match else ""

def extract_vendor_name(query: str, results: dict) -> str:
    """Extract vendor name from query or results"""
    if "po_matching" in results and results["po_matching"].get("invoice"):
        return results["po_matching"]["invoice"].get("vendor", "")
    return ""

def synthesize_response(query: str, agent_results: dict, verification: dict, plan: dict) -> dict:
    """Synthesize final response from all agent outputs"""
    
    explanation = "Query processed successfully."
    evidence = {}
    match_score = 0
    
    # Debug information
    debug_info = {
        "query": query,
        "plan_type": plan.get("query_type", "unknown"),
        "agents_called": plan.get("agents_to_call", []),
        "agent_results_keys": list(agent_results.keys())
    }
    
    # Handle PO matching results
    if "po_matching" in agent_results:
        po_result = agent_results["po_matching"]
        
        # Check if there's an error
        if "error" in po_result:
            explanation = f"Error: {po_result['error']}"
            match_score = 0
        else:
            match_score = po_result.get("match_score", 0)
            discrepancies = po_result.get("discrepancies", [])
            flag_reason = po_result.get("flag_reason", "No flag reason provided")
            
            if discrepancies:
                explanation = f"Invoice analysis complete. {flag_reason}. Found {len(discrepancies)} discrepancies: " + "; ".join(discrepancies[:3])
                if len(discrepancies) > 3:
                    explanation += f" and {len(discrepancies) - 3} more issues."
            else:
                explanation = f"Invoice analysis complete. {flag_reason}. No discrepancies found."
            
            evidence = po_result.get("evidence", {})
    else:
        # If no PO matching was done, explain why
        if "retriever" in agent_results:
            retrieval_result = agent_results["retrieval"]
            doc_count = len(retrieval_result.get("documents", []))
            explanation = f"Document retrieval completed. Found {doc_count} relevant documents."
        else:
            explanation = "No specific invoice analysis performed. Try asking about a specific invoice ID (e.g., 'Why was invoice INV-123 flagged?')"
    
    # Add web search context
    if "web_search" in agent_results:
        web_result = agent_results["web_search"]
        if web_result.get("found") and web_result.get("data"):
            vendor_data = web_result["data"]
            risk_level = vendor_data.get("risk_level", "unknown")
            compliance_score = vendor_data.get("compliance_score", "unknown")
            explanation += f" Vendor risk assessment: {risk_level} risk level with {compliance_score}% compliance score."
    
    return {
        "explanation": explanation,
        "evidence": evidence,
        "match_score": match_score,
        "verifier_confidence": verification.get("confidence", 0),
        "requires_human_review": verification.get("requires_human_review", False),
        "recommendations": verification.get("recommendations", []),
        "query_plan": plan,
        "agent_results": agent_results,
        "debug_info": debug_info  # Add debug information
    }

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    # Create frontend directory
    os.makedirs('../frontend', exist_ok=True)
    app.run(debug=True, port=5000)