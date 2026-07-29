import hashlib
import json
import os
from datetime import datetime
from typing import List

import requests

from ape.intelligence.models import UNKNOWN, BusinessEvidence, EvidenceProvenance


class BudgetExhaustedError(Exception):
    pass

class AdapterError(Exception):
    pass

class WebSearchAdapter:
    def __init__(self, max_requests: int = 0, limit_queries: int = 0):
        self.max_requests = max_requests
        self.limit_queries = limit_queries
        self._request_count = 0
        self._query_count = 0
        self.cache_dir = os.path.join(os.getcwd(), ".cache")

    def _get_cache_path(self, query: str) -> str:
        # Normalized query cache key using MD5
        query_hash = hashlib.md5(query.strip().lower().encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"serpapi_{query_hash}.json")

    def _read_cache(self, query: str) -> str:
        cache_path = self._get_cache_path(query)
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def _write_cache(self, query: str, data: str) -> None:
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
        cache_path = self._get_cache_path(query)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(data)

    def _external_request(self, query: str) -> str:
        # 1. Check cache first to avoid consuming budget/quota
        cached_data = self._read_cache(query)
        if cached_data is not None:
            return cached_data

        # 2. Check budget BEFORE calling requests.get
        if self.max_requests > 0 and self._request_count >= self.max_requests:
            raise BudgetExhaustedError(f"Request budget of {self.max_requests} exhausted.")
        
        api_key = os.environ.get("SERPAPI_API_KEY")
        if not api_key:
            # Fallback to Windows User Registry if os.environ subshell hasn't inherited it
            try:
                import winreg
                reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
                api_key, _ = winreg.QueryValueEx(reg_key, "SERPAPI_API_KEY")
            except Exception:
                pass

        if not api_key:
            raise AdapterError("SERPAPI_API_KEY environment variable is not configured.")

        self._request_count += 1
        
        # Enforce budget before requests.get invocation
        try:
            response = requests.get(
                "https://serpapi.com/search",
                params={"q": query, "engine": "google", "api_key": api_key},
                timeout=10
            )
            # Raise exception on HTTP client failure (4xx, 5xx) - failure semantic preservation
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Propagate error cleanly without converting to UNKNOWN
            raise AdapterError(f"Network request failed: {e}") from e

        raw_text = response.text
        
        # Save to cache
        self._write_cache(query, raw_text)
        return raw_text

    def scan_segment(self, segment: str) -> List[BusinessEvidence]:
        # Define live search queries for segment
        queries_to_run = [f"{segment} jobs", f"{segment} pricing"]
        if self.limit_queries > 0:
            queries_to_run = queries_to_run[:self.limit_queries]
            
        results = []
        for q in queries_to_run:
            try:
                raw_text = self._external_request(q)
                results.append(self.process_live_result(q, raw_text))
            except BudgetExhaustedError:
                raise
            except AdapterError:
                # Do NOT fabricate evidence on adapter/network failures
                raise
        return results

    def process_live_result(self, query: str, raw_text: str) -> BusinessEvidence:
        # Extract observations from SerpAPI payload safely
        try:
            data = json.loads(raw_text)
        except Exception as e:
            raise AdapterError(f"Failed to parse SerpAPI response JSON: {e}") from e

        organic_results = data.get("organic_results", [])
        
        # Extract primary reference link if available
        first_link = None
        if organic_results and isinstance(organic_results, list):
            first_item = organic_results[0]
            if isinstance(first_item, dict) and first_item.get("link"):
                first_link = str(first_item.get("link"))

        structured_observations = []
        combined_text = ""
        for result in organic_results:
            if isinstance(result, dict):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                structured_observations.append(f"Title: {title} | Snippet: {snippet} | Link: {link}")
                combined_text += f" {title} {snippet}"
            
        raw_obs = "\n".join(structured_observations) if structured_observations else combined_text
        combined_text_lower = combined_text.lower()

        # Evidence-first: raw observations mapping
        manual_work = True if "aranıyor" in combined_text_lower or "asistan" in combined_text_lower or "eleman" in combined_text_lower else UNKNOWN
        pricing = True if "fiyat" in combined_text_lower or "teklif" in combined_text_lower or "ücret" in combined_text_lower else UNKNOWN
        competition = True if data.get("ads") else UNKNOWN
        search_intent = True if len(organic_results) > 0 else UNKNOWN

        prov = EvidenceProvenance(
            source_adapter="serpapi_web_search",
            raw_observation=raw_obs[:1000],  # Limit size for provenance safety
            reference_url=first_link,
            request_context=query,
            retrieval_timestamp=datetime.now()
        )
        
        return BusinessEvidence(
            search_intent_observation=search_intent,
            pain_observation=UNKNOWN,
            manual_work_observation=manual_work,
            pricing_observation=pricing,
            entity_observation=UNKNOWN,
            competition_observation=competition,
            ai_solvability=UNKNOWN,
            provenance=prov
        )

    def process_mock_result(self, raw_text: str) -> BusinessEvidence:
        manual_work = True if "aranıyor" in raw_text.lower() or "asistan" in raw_text.lower() else UNKNOWN
        pricing = True if "fiyat" in raw_text.lower() or "teklif" in raw_text.lower() else UNKNOWN
        
        prov = EvidenceProvenance(
            source_adapter="web_search", 
            raw_observation=raw_text,
            request_context="mock_query",
            retrieval_timestamp=datetime.now()
        )
        return BusinessEvidence(
            search_intent_observation=UNKNOWN,
            pain_observation=UNKNOWN,
            manual_work_observation=manual_work,
            pricing_observation=pricing,
            entity_observation=UNKNOWN,
            competition_observation=UNKNOWN,
            ai_solvability=UNKNOWN,
            provenance=prov
        )

