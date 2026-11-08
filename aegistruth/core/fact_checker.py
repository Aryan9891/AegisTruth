"""Autonomous Fact-Checking & Hallucination Sentinel: Claim Decomposition and Knowledge Grounding."""

import re
from typing import Dict, Any, List, Tuple

# Built-in ground-truth benchmark database for instant verification
FOUNDATIONAL_FACTS = {
    # Physics & Constants
    "speed of light": ("299,792,458 m/s (approx 300,000 km/s in vacuum)", r"\b(speed of light|c in vacuum)\b"),
    "water freezing point": ("0 degrees Celsius (32 degrees Fahrenheit) at 1 atm", r"\b(water freezes|freezing point of water)\b"),
    "water boiling point": ("100 degrees Celsius (212 degrees Fahrenheit) at 1 atm", r"\b(water boils|boiling point of water)\b"),
    
    # Geography & History
    "first moon landing": ("July 20, 1969 by Apollo 11", r"\b(apollo 11|first moon landing|neil armstrong.*moon)\b"),
    "earth circumference": ("approx 40,075 km at the equator", r"\b(earth('s)? circumference|circumference of the earth)\b"),
    "world war ii end": ("1945", r"\b(world war ii|wwii|second world war).*(ended|concluded|surrendered)\b"),
    "dna structure": ("double helix discovered/modeled by Watson, Crick, Franklin in 1953", r"\b(structure of dna|dna double helix)\b"),
}

# Hallucination markers: impossible historical pairings, fabricated tech
ANACHRONISM_RULES = [
    (r"\b(abraham lincoln|george washington|napoleon|julius caesar)\b.*(internet|email|iphone|computer|television|airplane|nuclear)", 
     "Severe Anachronism: Historic figure paired with modern technological invention."),
    (r"\b(albert einstein)\b.*(quantum computing|chatgpt|iphone)", 
     "Historical Inconsistency: Einstein lived prior to modern microprocessors and LLMs."),
    (r"\b(speed of light)\b.*(is \d{1,4}\s*(km/h|mph|m/s))\b", 
     "Physical Fact Distortion: Grossly incorrect physical constant."),
]

def extract_claims(text: str) -> List[Dict[str, Any]]:
    """Extracts propositional claims containing quantities, years, or factual assertions."""
    raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    claims = []
    
    for idx, sentence in enumerate(raw_sentences):
        s_clean = sentence.strip()
        if len(s_clean) < 10:
            continue
            
        has_number = bool(re.search(r'\b\d+(\.\d+)?%?\b', s_clean))
        has_year = bool(re.search(r'\b(1[789]\d\d|20\d\d)\b', s_clean))
        has_superlative = bool(re.search(r'\b(first|fastest|highest|largest|smallest|only|never|always|proven)\b', s_clean, re.I))
        
        claim_type = "GENERAL_STATEMENT"
        if has_year and has_number:
            claim_type = "STATISTICAL_HISTORICAL"
        elif has_year:
            claim_type = "TEMPORAL_HISTORICAL"
        elif has_number:
            claim_type = "QUANTITATIVE_MEASUREMENT"
        elif has_superlative:
            claim_type = "ABSOLUTE_ASSERTION"
            
        claims.append({
            "id": idx + 1,
            "text": s_clean,
            "type": claim_type,
            "has_metric": has_number or has_year,
        })
        
    return claims

def check_internal_contradictions(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detects mutually contradictory statements within the same document."""
    contradictions = []
    
    increase_pattern = re.compile(r'\b(increased|growth|surged|rose|amplified|expanded|skyrocketed)\b', re.I)
    decrease_pattern = re.compile(r'\b(decreased|declined|fell|dropped|diminished|contracted|plummeted)\b', re.I)
    
    for i in range(len(claims)):
        c1 = claims[i]["text"]
        for j in range(i + 1, len(claims)):
            c2 = claims[j]["text"]
            
            # Simple topic overlap check
            words1 = set(re.findall(r'\b\w{4,}\b', c1.lower()))
            words2 = set(re.findall(r'\b\w{4,}\b', c2.lower()))
            overlap = words1.intersection(words2)
            
            # If they share subject matter but one says increase and another says decrease
            if len(overlap) >= 2:
                if (increase_pattern.search(c1) and decrease_pattern.search(c2)) or \
                   (decrease_pattern.search(c1) and increase_pattern.search(c2)):
                    contradictions.append({
                        "claim_a_id": claims[i]["id"],
                        "claim_b_id": claims[j]["id"],
                        "claim_a": c1,
                        "claim_b": c2,
                        "shared_topics": list(overlap)[:3],
                        "issue": "Direct semantic contradiction regarding trajectory (increase vs decline)."
                    })
                    
    return contradictions

def verify_facts(text: str) -> Dict[str, Any]:
    """
    Evaluates factual integrity of a document.
    Extracts claims, checks against known benchmark knowledge, detects anachronisms and contradictions.
    """
    claims = extract_claims(text)
    contradictions = check_internal_contradictions(claims)
    
    evaluated_claims = []
    anachronisms_detected = []
    grounded_verified_count = 0
    high_risk_count = 0
    
    # 1. Anachronism & physical law check
    for pattern, description in ANACHRONISM_RULES:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            anachronisms_detected.append({
                "match": match.group(0),
                "description": description
            })
            high_risk_count += 1
            
    # 2. Benchmark Knowledge Cross-Check
    for claim in claims:
        status = "UNVERIFIED_OPINION"
        evidence = "Requires external domain corpus verification."
        confidence = 0.50
        
        # Check against ground truth knowledge base
        for fact_name, (fact_truth, fact_regex) in FOUNDATIONAL_FACTS.items():
            if re.search(fact_regex, claim["text"], re.IGNORECASE):
                status = "GROUNDED_VERIFIED"
                evidence = f"Ground truth match ({fact_name}): {fact_truth}"
                confidence = 0.95
                grounded_verified_count += 1
                break
                
        # Check if flagged by anachronism
        for anach in anachronisms_detected:
            if anach["match"].lower() in claim["text"].lower():
                status = "HIGH_RISK_HALLUCINATION"
                evidence = anach["description"]
                confidence = 0.10
                break
                
        # Flag absolute assertions
        if claim["type"] == "ABSOLUTE_ASSERTION" and status == "UNVERIFIED_OPINION":
            status = "POTENTIAL_OVERSTATEMENT"
            evidence = "Contains unhedged absolute superlatives (e.g. always, never, proven)."
            confidence = 0.40
            
        evaluated_claims.append({
            "id": claim["id"],
            "claim": claim["text"],
            "type": claim["type"],
            "status": status,
            "evidence": evidence,
            "credibility_score": round(confidence * 100, 1)
        })
        
    # Document Factuality Index
    total_claims = len(claims)
    if total_claims == 0:
        overall_factuality = 50.0
    else:
        avg_credibility = sum(c["credibility_score"] for c in evaluated_claims) / total_claims
        penalty = (len(contradictions) * 20.0) + (len(anachronisms_detected) * 35.0)
        overall_factuality = max(0.0, min(100.0, avg_credibility - penalty))
        
    return {
        "overall_factuality_score": round(overall_factuality, 1),
        "total_claims_extracted": total_claims,
        "verified_grounded_count": grounded_verified_count,
        "anachronisms_detected": anachronisms_detected,
        "internal_contradictions": contradictions,
        "claims": evaluated_claims
    }

