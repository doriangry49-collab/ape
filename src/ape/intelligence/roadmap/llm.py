"""
LLM Provider Abstractions for the Intelligent Planning Boundary.
(RFC-015)
"""
import json
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class PlannerModel(ABC):
    """Abstract interface for LLM providers used in planning."""
    
    @abstractmethod
    def generate(self, prompt: str, system_message: str, schema: dict) -> Dict[str, Any]:
        """Generate a structured JSON response conforming to the schema."""


class OpenAICompatibleProvider(PlannerModel):
    """
    Generic provider that works with any OpenAI API compatible endpoint.
    This includes OpenAI, NVIDIA NIMs, Ollama, etc.
    """
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        
    def generate(self, prompt: str, system_message: str, schema: dict) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # We enforce JSON mode via response_format if supported,
        # but also provide the JSON schema in the system prompt for models that need it.
        schema_str = json.dumps(schema, indent=2)
        system_with_schema = (
            f"{system_message}\n\n"
            "You MUST return your response as a valid JSON object matching the following JSON Schema:\n"
            f"{schema_str}\n\n"
            "Do NOT return markdown blocks (like ```json), just the raw JSON object."
        )

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_with_schema},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode("utf-8"), 
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                
                # Cleanup potential markdown ticks if the model ignores the instruction
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                    
                return json.loads(content.strip())
        except Exception as e:
            # We raise this to be caught by the RoadmapGenerator fallback logic
            raise RuntimeError(f"Planner LLM API Error: {str(e)}") from e
