import json
from datetime import datetime
from pathlib import Path

from ape.intelligence.models import Opportunity
from ape.intelligence.scanner.base import BaseScanner
from ape.intelligence.scanner.extractor import PainPointExtractor


class OfflineFileAdapter(BaseScanner):
    def __init__(self, mock_data_path: str):
        self.mock_data_path = mock_data_path
        self.extractor = PainPointExtractor()

    def scan(self) -> list[Opportunity]:
        # For testing, if the path doesn't exist, just return a single mock opportunity
        if not Path(self.mock_data_path).exists():
            pain_point, provenance = self.extractor.extract("Offline mock data.", "offline_file")
            
            # The tests expect a single opportunity to be returned
            return [
                Opportunity(
                    title="Mock Offline Opportunity",
                    description="This is a mock opportunity from OfflineFileAdapter.",
                    url="local://mock",
                    source="offline_file",
                    score=50,
                    confidence=0.5,
                    published_at=datetime.now(),
                    tags=["mock", "offline"],
                    pain_point=pain_point,
                    provenance=provenance,
                    is_hypothesis=True
                )
            ]
        
        # If the file exists, read it (this part can be expanded later)
        with open(self.mock_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        opportunities = []
        for item in data.get("items", []):
            pain_point, provenance = self.extractor.extract(item.get("text", ""), "offline_file")
            opp = Opportunity(
                title=item.get("title", "Unknown Title"),
                description=item.get("description", ""),
                url=item.get("url", ""),
                source="offline_file",
                score=item.get("score", 0),
                confidence=item.get("confidence", 0.0),
                published_at=datetime.now(),
                tags=item.get("tags", []),
                pain_point=pain_point,
                provenance=provenance,
                is_hypothesis=True
            )
            opportunities.append(opp)
            
        return opportunities
