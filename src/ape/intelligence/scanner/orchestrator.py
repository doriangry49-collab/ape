from datetime import datetime
from typing import List

from ape.intelligence.models import Opportunity
from ape.intelligence.scanner.adapters.complaint_adapter import ComplaintAdapter
from ape.intelligence.scanner.adapters.maps_review_adapter import MapsReviewAdapter
from ape.intelligence.scanner.adapters.web_search_adapter import WebSearchAdapter


class DiscoveryOrchestrator:
    SEGMENTS = [
        "real_estate", 
        "automotive", 
        "health_beauty", 
        "home_local_services", 
        "professional_services"
    ]
    
    def __init__(
        self, 
        offline: bool = False, 
        limit_segments: int = 0,
        live_mode: bool = False,
        max_requests: int = 0,
        limit_queries: int = 0
    ):
        self.offline = offline
        self.limit_segments = limit_segments
        self.live_mode = live_mode
        self.max_requests = max_requests
        self.limit_queries = limit_queries
        
        # Pass the budget and query limits to the web adapter
        self.web_adapter = WebSearchAdapter(
            max_requests=self.max_requests,
            limit_queries=self.limit_queries
        )
        self.complaint_adapter = ComplaintAdapter()
        self.maps_adapter = MapsReviewAdapter()

    def run_segment_discovery(self) -> List[Opportunity]:
        if self.offline:
            # P0 offline mode fallback
            from ape.intelligence.scanner.business import OfflineFileAdapter
            return OfflineFileAdapter("mock_business_data.json").scan()
            
        segments_to_scan = self.SEGMENTS
        if self.limit_segments > 0:
            segments_to_scan = self.SEGMENTS[:self.limit_segments]

        opportunities = []
        for segment in segments_to_scan:
            # 1. Gather evidence from all adapters
            web_evidence = self.web_adapter.scan_segment(segment)
            
            if self.live_mode:
                # In live verification mode, strictly ONLY run the WebSearchAdapter
                complaint_evidence = []
                maps_evidence = []
            else:
                complaint_evidence = self.complaint_adapter.scan_segment(segment)
                maps_evidence = self.maps_adapter.scan_segment(segment)
            
            # 2. Combine into a single Opportunity per segment
            opp = Opportunity(
                title=f"Discovery in {segment}",
                description=f"Automated discovery scan for {segment}",
                url=f"ape://discovery/{segment}",
                source="orchestrator",
                score=0,
                confidence=0.5,
                published_at=datetime.now(),
                tags=[segment],
                business_evidence=web_evidence + complaint_evidence + maps_evidence,
                is_hypothesis=True
            )
            opportunities.append(opp)
            
        return opportunities
