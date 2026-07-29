from typing import List

from ape.intelligence.models import UNKNOWN, BusinessEvidence, EvidenceProvenance


class MapsReviewAdapter:
    def scan_segment(self, segment: str) -> List[BusinessEvidence]:
        # Implementation for P1 actual network would go here later
        return []

    def process_mock_result(self, raw_text: str) -> BusinessEvidence:
        pain = True if "yıldız" in raw_text.lower() or "berbat" in raw_text.lower() else UNKNOWN
        
        prov = EvidenceProvenance(source_adapter="maps_review", raw_observation=raw_text)
        return BusinessEvidence(
            search_intent_observation=UNKNOWN,
            pain_observation=pain,
            manual_work_observation=UNKNOWN,
            pricing_observation=UNKNOWN,
            entity_observation=UNKNOWN,
            competition_observation=UNKNOWN,
            ai_solvability=UNKNOWN,
            provenance=prov
        )
