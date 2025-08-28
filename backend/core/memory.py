from typing import Dict, List, Any
from datetime import datetime
import uuid

class ConversationMemory:
    def __init__(self):
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_session(self) -> str:
        """Create new conversation session"""
        session_id = str(uuid.uuid4())
        self.conversations[session_id] = []
        return session_id
    
    def add_interaction(self, session_id: str, query: str, response: Dict[str, Any]):
        """Add interaction to session memory"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response
        }
        self.conversations[session_id].append(interaction)
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for session"""
        return self.conversations.get(session_id, [])
    
    def get_context(self, session_id: str, context_window: int = 3) -> str:
        """Get recent conversation context"""
        history = self.get_session_history(session_id)
        recent = history[-context_window:] if len(history) > context_window else history
        
        context = ""
        for interaction in recent:
            context += f"Previous Query: {interaction['query']}\n"
            if 'explanation' in interaction['response']:
                context += f"Previous Response: {interaction['response']['explanation'][:200]}...\n"
        
        return context