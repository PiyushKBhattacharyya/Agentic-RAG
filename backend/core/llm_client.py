import openai
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        # Set the API key globally first
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Try the new client initialization
        try:
            self.client = openai.OpenAI()
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {e}")
            # Fallback to older initialization if needed
            self.client = None
            
        self.model = "gpt-3.5-turbo"
    
    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> str:
        """Get completion from OpenAI API"""
        try:
            if self.client:
                # Use new client
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            else:
                # Fallback to direct API call
                import requests
                api_key = os.getenv('OPENAI_API_KEY')
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': self.model,
                    'messages': messages,
                    'temperature': temperature,
                    'max_tokens': 1500
                }
                response = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data
                )
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"
    
    def extract_structured_data(self, prompt: str, data: str) -> Dict[str, Any]:
        """Extract structured data using LLM"""
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": data}
        ]
        return self.chat_completion(messages)