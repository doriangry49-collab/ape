from dataclasses import dataclass, field
from typing import Dict, List, Any
from ape.intelligence.models import BusinessEvidence, EvidenceProvenance, UNKNOWN

@dataclass(frozen=True)
class BridgeResult:
    evidence_flags: Dict[str, Any]
    provenance_chain: List[EvidenceProvenance] = field(default_factory=list)
    reference_urls: List[str] = field(default_factory=list)

def _aggregate_observation(vals: List[Any]) -> Any:
    """
    Deterministic observation aggregation:
    - TRUE + TRUE -> TRUE
    - TRUE + UNKNOWN -> TRUE
    - FALSE + FALSE -> FALSE
    - FALSE + UNKNOWN -> FALSE
    - TRUE + FALSE -> UNKNOWN (Conflict / Indeterminate)
    - UNKNOWN + UNKNOWN -> UNKNOWN
    - NO EVIDENCE -> UNKNOWN
    """
    if not vals:
        return UNKNOWN
    
    has_true = any(v is True for v in vals)
    has_false = any(v is False for v in vals)
    
    if has_true and has_false:
        return UNKNOWN  # Conflict / Indeterminate
    if has_true:
        return True
    if has_false:
        return False
    return UNKNOWN

class InferenceBridge:
    """
    Observation -> Inference Bridge (RFC-012 Option D)
    Aggregates raw observations from BusinessEvidence objects and maps them
    deterministically into high-level inference flags for ConstitutionValidator.
    """
    def aggregate_evidence(self, evidence_list: List[BusinessEvidence]) -> BridgeResult:
        if not evidence_list:
            return BridgeResult(
                evidence_flags={
                    "payment_signal": UNKNOWN,
                    "identifiable_customer": UNKNOWN,
                    "ai_solvability": UNKNOWN
                },
                provenance_chain=[],
                reference_urls=[]
            )

        # Collect provenance lineage
        provenance_chain = [ev.provenance for ev in evidence_list if ev.provenance]
        reference_urls = [
            ev.provenance.reference_url 
            for ev in evidence_list 
            if ev.provenance and ev.provenance.reference_url
        ]

        # Aggregate individual observations across evidence items
        search_intents = [ev.search_intent_observation for ev in evidence_list]
        manual_works = [ev.manual_work_observation for ev in evidence_list]
        pricings = [ev.pricing_observation for ev in evidence_list]
        competitions = [ev.competition_observation for ev in evidence_list]
        entities = [ev.entity_observation for ev in evidence_list]

        agg_search_intent = _aggregate_observation(search_intents)
        agg_manual_work = _aggregate_observation(manual_works)
        agg_pricing = _aggregate_observation(pricings)
        agg_competition = _aggregate_observation(competitions)
        agg_entity = _aggregate_observation(entities)

        # Map aggregate observations to inference flags
        # 1. payment_signal: pricing or competition
        if agg_pricing is True or agg_competition is True:
            payment_signal = True
        elif agg_pricing is False and agg_competition is False:
            payment_signal = False
        else:
            payment_signal = UNKNOWN

        # 2. identifiable_customer: search intent or entity
        if agg_search_intent is True or agg_entity is True:
            identifiable_customer = True
        elif agg_search_intent is False and agg_entity is False:
            identifiable_customer = False
        else:
            identifiable_customer = UNKNOWN

        # 3. ai_solvability: manual work observation
        if agg_manual_work is True:
            ai_solvability = True
        elif agg_manual_work is False:
            ai_solvability = False
        else:
            ai_solvability = UNKNOWN

        evidence_flags = {
            "payment_signal": payment_signal,
            "identifiable_customer": identifiable_customer,
            "ai_solvability": ai_solvability
        }

        return BridgeResult(
            evidence_flags=evidence_flags,
            provenance_chain=provenance_chain,
            reference_urls=reference_urls
        )
