"""Unit tests for Textual Forensics and AI Linguistic Detection."""

import pytest
from aegistruth.core.text_forensics import (
    analyze_text,
    tokenize_sentences,
    tokenize_words,
    compute_shannon_entropy,
    compute_burstiness,
    compute_perplexity_proxy,
)

def test_tokenize_sentences():
    text = "Hello world! This is a test. Is this sentence valid? Yes."
    sentences = tokenize_sentences(text)
    assert len(sentences) >= 3

def test_compute_shannon_entropy():
    tokens = ["the", "cat", "sat", "on", "the", "mat"]
    entropy = compute_shannon_entropy(tokens)
    assert entropy > 0.0

def test_compute_burstiness():
    lengths = [5, 25, 4, 30, 6]  # Varied human-like lengths
    burstiness, mean_l, std_l = compute_burstiness(lengths)
    assert burstiness > 0.4
    assert mean_l > 0.0

def test_analyze_text_human_vs_ai():
    human_text = (
        "We ran out of coffee at midnight. Then, unexpectedly, the deployment script crashed! "
        "I spent an hour digging through log files before realizing someone deleted the config map. "
        "Fixed it, finally."
    )
    res_human = analyze_text(human_text)
    assert res_human["verdict"] in ["LIKELY_HUMAN", "MIXED_OR_EDITED"]
    assert res_human["synthetic_probability"] < 50.0

    ai_text = (
        "In today's fast-paced digital world, it is crucial to remember that technology serves as a beacon of progress. "
        "Furthermore, it is worth noting that modern artificial intelligence plays a pivotal role across industries. "
        "By navigating the complexities of computational innovation, we can seamlessly integrate these multifaceted solutions. "
        "In summary, this groundbreaking paradigm stands as a testament to human ingenuity and continuous evolution."
    )
    res_ai = analyze_text(ai_text)
    assert res_ai["verdict"] == "LIKELY_AI_GENERATED"
    assert res_ai["synthetic_probability"] >= 60.0
    assert len(res_ai["sentence_breakdown"]) >= 3
