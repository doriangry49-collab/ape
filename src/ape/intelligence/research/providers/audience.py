from __future__ import annotations

from typing import Any

from ape.intelligence.research.providers.base import BaseResearchProvider


class HeuristicAudienceProvider(BaseResearchProvider):
    """Calculates target audience, competitors, risks, and MVP suggestions using heuristics."""

    def fetch_signals(self, topic: str) -> dict[str, Any]:
        topic_lower = topic.lower()
        
        # Default fallback values
        target_audience = ["Solo Founders", "Indie Hackers", "Software Developers"]
        competitors = [f"Generic {topic} API Providers", "Manual custom implementations"]
        risks = ["High time-to-market if building from scratch", "Platform dependency risks"]
        suggested_mvp = [
            "Local CLI interface for rapid prototype testing",
            "Simple single-page web ui showing raw results",
            "Export raw data format in JSON / CSV"
        ]
        confidence = 0.80

        # Heuristic rules matching topic keywords
        if any(kw in topic_lower for kw in ["ai", "llm", "gpt", "agent", "model"]):
            target_audience = ["AI Engineers", "Solo Founders", "Product Managers"]
            competitors = [
                "OpenAI Assistants Platform",
                "LangChain Framework Ecosystem",
                "Coze/Dify platforms",
            ]
            risks = [
                "API rate-limiting overhead",
                "Token cost scaling issues",
                "Rapid tech landscape evolution",
            ]
            suggested_mvp = [
                "Prompt template playground with version logs",
                "Lightweight API wrapper caching tokens locally",
                "Single-file configuration interface"
            ]
            confidence = 0.85
            
        elif any(kw in topic_lower for kw in ["saas", "dashboard", "tool"]):
            target_audience = ["SaaS Developers", "Indie Hackers", "Digital Marketers"]
            competitors = [
                "Vercel templates",
                "Stripe billing integrations",
                "Supabase authentication services",
            ]
            risks = ["Low user retention barriers", "High marketing/acquisition costs"]
            suggested_mvp = [
                "Clean database migrations builder",
                "Basic OAuth configuration template",
                "Pricing table mockup utility"
            ]
            confidence = 0.78

        return {
            "target_audience": target_audience,
            "competitors": competitors,
            "risks": risks,
            "suggested_mvp": suggested_mvp,
            "confidence": confidence,
            "sources": ["AudienceHeuristics"]
        }
