"""Advanced Text Forensics: Burstiness, Perplexity Estimation, Shannon Entropy, and AI Heuristics."""

import re
import math
from typing import Dict, Any, List, Tuple
from collections import Counter
import numpy as np

# Prominent generative AI linguistic markers and transition clichés
AI_CLICHE_PATTERNS = [
    r"\bdelve\b",
    r"\btapestry\b",
    r"\btestament to\b",
    r"\bpivotal role\b",
    r"\bbeacon of\b",
    r"\bin summary\b",
    r"\bit is crucial to (remember|note|understand)\b",
    r"\bin today's (fast-paced|rapidly evolving|digital) world\b",
    r"\bfurthermore,\s+it is worth\b",
    r"\bnavigat(e|ing) the complexities\b",
    r"\ba multifaceted (approach|problem|issue)\b",
    r"\brest assured\b",
    r"\bharness(ing)? the power of\b",
    r"\bleverag(e|ing)\b",
    r"\bseamlessly integrat(ed|ing)?\b",
]

def tokenize_sentences(text: str) -> List[str]:
    """Splits text into clean sentence units."""
    # Split on period, exclamation, or question mark followed by whitespace
    raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 3]
    return sentences if sentences else [text.strip()]

def tokenize_words(text: str) -> List[str]:
    """Extracts lowercase words, stripping punctuation."""
    words = re.findall(r'\b[a-zA-Z0-9_\'-]+\b', text.lower())
    return words

def compute_shannon_entropy(tokens: List[str]) -> float:
    """Computes Shannon Entropy of token distribution."""
    if not tokens:
        return 0.0
    total = len(tokens)
    counts = Counter(tokens)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return float(entropy)

def compute_burstiness(sentence_lengths: List[int]) -> Tuple[float, float, float]:
    """
    Computes Sentence Burstiness.
    Humans write with high variance in sentence lengths (mix of short and long clauses).
    AI text is characterized by regular, uniform sentence cadence.
    """
    if not sentence_lengths:
        return 0.0, 0.0, 0.0
    arr = np.array(sentence_lengths, dtype=np.float32)
    mean_len = float(np.mean(arr))
    std_len = float(np.std(arr))
    # Burstiness coefficient
    burstiness = float(std_len / (mean_len + 1e-9))
    return burstiness, mean_len, std_len

def compute_perplexity_proxy(words: List[str]) -> float:
    """
    Estimates a proxy perplexity score based on n-gram distribution repetition.
    Lower score indicates repetitive, predictable machine-like sequencing.
    """
    if len(words) < 5:
        return 50.0
        
    bigrams = list(zip(words[:-1], words[1:]))
    unique_bigrams = len(set(bigrams))
    ttr = unique_bigrams / float(len(bigrams))
    
    # Scale into a normalized 0-100 score
    return float(ttr * 100.0)

def evaluate_sentence(sentence: str, avg_len: float) -> Dict[str, Any]:
    """Scores an individual sentence for synthetic indicators."""
    words = tokenize_words(sentence)
    word_count = len(words)
    
    # Check for AI cliches
    cliche_matches = []
    for pattern in AI_CLICHE_PATTERNS:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            cliche_matches.append(match.group(0))
            
    # Uniformity penalty (very close to mean without punctuation variance)
    length_diff = abs(word_count - avg_len)
    
    suspicion_score = 0.0
    if cliche_matches:
        suspicion_score += len(cliche_matches) * 35.0
    if 14 <= word_count <= 22:  # Classic LLM sweet-spot sentence length
        suspicion_score += 15.0
    if length_diff < 3.0:
        suspicion_score += 10.0
        
    suspicion_score = min(100.0, suspicion_score)
    
    if suspicion_score >= 60.0:
        tag = "LIKELY_AI"
    elif suspicion_score >= 30.0:
        tag = "SUSPICIOUS"
    else:
        tag = "ORGANIC"
        
    return {
        "text": sentence,
        "word_count": word_count,
        "tag": tag,
        "suspicion_score": round(suspicion_score, 1),
        "cliches_found": cliche_matches
    }

def analyze_text(text: str) -> Dict[str, Any]:
    """
    Complete textual forensics pipeline.
    Returns synthetic AI likelihood, burstiness score, entropy, cliche density, and sentence heatmap.
    """
    cleaned = text.strip()
    if len(cleaned) < 20:
        raise ValueError("Text too short for statistical forensic evaluation (min 20 characters required)")
        
    sentences = tokenize_sentences(cleaned)
    words = tokenize_words(cleaned)
    
    if len(words) < 5:
        raise ValueError("Text must contain at least 5 words for analysis")
        
    sentence_lengths = [len(tokenize_words(s)) for s in sentences]
    burstiness, mean_len, std_len = compute_burstiness(sentence_lengths)
    entropy = compute_shannon_entropy(words)
    perplexity_proxy = compute_perplexity_proxy(words)
    
    # Type-Token Ratio (lexical diversity)
    unique_words = len(set(words))
    ttr = float(unique_words / len(words))
    
    # Scan for AI cliches across document
    cliches_found = []
    for pattern in AI_CLICHE_PATTERNS:
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        if matches:
            cliches_found.extend(matches)
            
    cliche_density = len(cliches_found) / (len(words) / 100.0) if len(words) >= 50 else len(cliches_found)
    
    # Per-sentence inspection
    sentence_analysis = [evaluate_sentence(s, mean_len) for s in sentences]
    
    # Composite AI Text Probability Score
    ai_score = 0.0
    forensic_reasons = []
    
    # 1. Burstiness (Human texts typically have burstiness > 0.50, AI often < 0.35)
    if burstiness < 0.30 and len(sentences) >= 3:
        ai_score += 30.0
        forensic_reasons.append(f"Unnaturally low sentence burstiness ({burstiness:.2f}), indicating uniform machine-generated sentence cadence.")
    elif burstiness < 0.45 and len(sentences) >= 3:
        ai_score += 15.0
        forensic_reasons.append("Low sentence length variance.")
        
    # 2. Clichés and transition hallmarks
    if len(cliches_found) >= 3:
        ai_score += 35.0
        forensic_reasons.append(f"High density of canonical LLM transition clichés ({len(cliches_found)} detected: {', '.join(cliches_found[:4])}).")
    elif len(cliches_found) >= 1:
        ai_score += 15.0
        forensic_reasons.append(f"Detected characteristic generative AI phrases ({', '.join(cliches_found)}).")
        
    # 3. Lexical repetition vs perplexity
    if perplexity_proxy < 45.0 and len(words) > 30:
        ai_score += 20.0
        forensic_reasons.append("Highly predictable n-gram token transitions and low vocabulary perplexity.")
        
    # 4. Token entropy
    if entropy < 3.8 and len(words) > 40:
        ai_score += 15.0
        forensic_reasons.append(f"Constrained Shannon entropy ({entropy:.2f} bits/token), showing synthetic lexical constraint.")
        
    ai_score = float(np.clip(ai_score, 0.0, 100.0))
    
    if ai_score >= 65.0:
        verdict = "LIKELY_AI_GENERATED"
        desc = "High probability of Large Language Model generation (GPT-4 / Claude / Gemini / LLaMA style)"
    elif ai_score >= 35.0:
        verdict = "MIXED_OR_EDITED"
        desc = "Contains mixed signatures; potentially AI-assisted drafting or human text with heavy editing"
    else:
        verdict = "LIKELY_HUMAN"
        desc = "Rich lexical diversity, natural sentence burstiness, and organic phrasing dynamics"
        
    return {
        "verdict": verdict,
        "synthetic_probability": round(ai_score, 1),
        "confidence_description": desc,
        "forensic_reasons": forensic_reasons,
        "sentence_breakdown": sentence_analysis,
        "metrics": {
            "sentence_count": len(sentences),
            "word_count": len(words),
            "burstiness_index": round(burstiness, 3),
            "mean_sentence_length": round(mean_len, 1),
            "sentence_len_std": round(std_len, 2),
            "shannon_entropy": round(entropy, 3),
            "lexical_ttr": round(ttr, 3),
            "perplexity_proxy": round(perplexity_proxy, 1),
            "cliche_count": len(cliches_found),
        }
    }

