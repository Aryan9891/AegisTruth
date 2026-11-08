"""Unit tests for Provenance and C2PA Manifest generation."""

import pytest
from aegistruth.core.provenance import compute_content_hashes, generate_provenance_manifest, generate_html_certificate

def test_compute_content_hashes():
    data = b"Authentic forensic digital asset bytes"
    hashes = compute_content_hashes(data)
    assert "sha256" in hashes
    assert "sha512" in hashes
    assert len(hashes["sha256"]) == 64

def test_generate_provenance_manifest():
    data = b"Sample image data for attestation"
    forensics = {
        "verdict": "AUTHENTIC",
        "synthetic_probability": 12.5,
        "forensic_reasons": ["Natural sensor PRNU"]
    }
    manifest = generate_provenance_manifest("image", data, forensics)
    assert manifest["seal_verified"] is True
    assert "manifest_signature" in manifest
    assert manifest["body"]["asset_type"] == "image"
    assert manifest["body"]["verdict"] == "AUTHENTIC"

def test_generate_html_certificate():
    manifest = {
        "manifest_signature": "abcdef1234567890abcdef1234567890",
        "body": {
            "schema_version": "1.0.0-c2pa.draft",
            "issuer": "AegisTruth Sentinel Engine",
            "timestamp_utc": "2026-11-08T12:00:00Z",
            "epoch": 1731067200,
            "asset_type": "image",
            "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "verdict": "AUTHENTIC",
            "synthetic_probability": 5.0,
            "forensic_markers": ["Consistent camera PRNU"]
        },
        "hash_fingerprints": {
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
    }
    html = generate_html_certificate(manifest)
    assert "<!DOCTYPE html>" in html
    assert "AEGIS-TRUTH FORENSIC ATTESTATION" in html
    assert "AUTHENTIC" in html

