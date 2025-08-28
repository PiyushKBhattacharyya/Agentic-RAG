import json
from datetime import datetime
from typing import Dict, Any, List
import os

class AuditLogger:
    def __init__(self, log_file: str = "audit.jsonl"):
        self.log_file = log_file
        
    def log_action(self, session_id: str, action_type: str, agent: str, 
                   input_data: Dict[str, Any], output_data: Dict[str, Any], 
                   metadata: Dict[str, Any] = None):
        """Log agent action with full context"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "action_type": action_type,
            "agent": agent,
            "input": input_data,
            "output": output_data,
            "metadata": metadata or {}
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all logs for a session"""
        logs = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('session_id') == session_id:
                            logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        return logs