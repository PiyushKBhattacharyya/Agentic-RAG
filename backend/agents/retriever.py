import json
import os
from typing import Dict, List, Any, Optional
from core.llm_client import LLMClient
from core.audit_logger import AuditLogger

class DocumentRetriever:
    def __init__(self, llm_client: LLMClient, audit_logger: AuditLogger):
        self.llm = llm_client
        self.audit_logger = audit_logger
        self.data_path = "data/"
        
    def retrieve_documents(self, query: str, session_id: str, 
                          doc_types: List[str] = None) -> Dict[str, Any]:
        """Retrieve relevant documents from local database"""
        
        if doc_types is None:
            doc_types = ["invoices", "purchase_orders", "goods_receipts"]
        
        results = {
            "documents": [],
            "sources": [],
            "retrieval_method": "keyword_and_semantic"
        }
        
        for doc_type in doc_types:
            file_path = os.path.join(self.data_path, f"{doc_type}.json")
            if os.path.exists(file_path):
                docs = self._search_documents(file_path, query, doc_type)
                results["documents"].extend(docs)
        
        # Log retrieval
        self.audit_logger.log_action(
            session_id=session_id,
            action_type="document_retrieval",
            agent="retriever",
            input_data={"query": query, "doc_types": doc_types},
            output_data=results
        )
        
        return results
    
    def _search_documents(self, file_path: str, query: str, doc_type: str) -> List[Dict[str, Any]]:
        """Search documents in a file"""
        try:
            with open(file_path, 'r') as f:
                documents = json.load(f)
            
            relevant_docs = []
            query_lower = query.lower()
            
            for doc in documents:
                # Simple keyword matching - in production would use embeddings
                doc_text = json.dumps(doc).lower()
                if any(term in doc_text for term in query_lower.split()):
                    doc["source_type"] = doc_type
                    doc["source_file"] = file_path
                    relevant_docs.append(doc)
            
            return relevant_docs[:5]  # Limit results
            
        except Exception as e:
            return []
    
    def get_specific_document(self, doc_id: str, doc_type: str) -> Optional[Dict[str, Any]]:
        """Get specific document by ID"""
        file_path = os.path.join(self.data_path, f"{doc_type}.json")
        try:
            with open(file_path, 'r') as f:
                documents = json.load(f)
            
            for doc in documents:
                if doc.get('id') == doc_id or doc.get('invoice_id') == doc_id or doc.get('po_id') == doc_id:
                    return doc
            return None
        except:
            return None