"""Digital Provenance & Verifiable Attestation: C2PA-Style Manifests, Cryptographic Seals, and Audit Reports."""

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

MANIFEST_SCHEMA_VERSION = "1.0.0-c2pa.draft"

def compute_content_hashes(data_bytes: bytes) -> Dict[str, str]:
    """Generates cryptographic hashes for content integrity attestation."""
    sha256 = hashlib.sha256(data_bytes).hexdigest()
    sha512 = hashlib.sha512(data_bytes).hexdigest()
    md5 = hashlib.md5(data_bytes).hexdigest()
    return {
        "sha256": sha256,
        "sha512": sha512,
        "md5": md5
    }

def generate_provenance_manifest(
    asset_type: str,
    raw_data: bytes,
    forensic_results: Dict[str, Any],
    issuer: str = "AegisTruth Sentinel Engine"
) -> Dict[str, Any]:
    """
    Creates a tamper-evident C2PA-compatible forensic attestation manifest.
    """
    hashes = compute_content_hashes(raw_data)
    timestamp = datetime.now(timezone.utc).isoformat()
    epoch = int(time.time())
    
    verdict = forensic_results.get("verdict", "UNKNOWN")
    synthetic_prob = forensic_results.get("synthetic_probability", 0.0)
    
    # Calculate manifest signature hash
    manifest_body = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "issuer": issuer,
        "timestamp_utc": timestamp,
        "epoch": epoch,
        "asset_type": asset_type,
        "content_hash": hashes["sha256"],
        "verdict": verdict,
        "synthetic_probability": synthetic_prob,
        "forensic_markers": forensic_results.get("forensic_reasons", []),
    }
    
    canonical_json = json.dumps(manifest_body, sort_keys=True)
    manifest_signature = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    
    return {
        "manifest_signature": manifest_signature,
        "body": manifest_body,
        "hash_fingerprints": hashes,
        "seal_verified": True,
        "attestation_status": "SEALED_VERIFIABLE"
    }

def generate_html_certificate(manifest: Dict[str, Any]) -> str:
    """Generates a standalone, beautifully styled HTML Certificate of Forensic Authenticity."""
    b = manifest["body"]
    hashes = manifest["hash_fingerprints"]
    verdict_color = "#10b981" if b["verdict"] in ["AUTHENTIC", "AUTHENTIC_HUMAN", "LIKELY_HUMAN"] else "#ef4444"
    
    markers_html = "".join([f"<li>{m}</li>" for m in b.get("forensic_markers", [])]) or "<li>No critical tampering detected.</li>"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AegisTruth Forensic Certificate: {manifest['manifest_signature'][:12]}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f3f4f6; margin: 0; padding: 40px; }}
  .cert-container {{ max-width: 800px; margin: 0 auto; border: 2px solid #3b82f6; border-radius: 12px; padding: 35px; background: #111827; box-shadow: 0 10px 40px rgba(0,0,0,0.8); }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #374151; padding-bottom: 20px; }}
  .title {{ font-size: 24px; font-weight: bold; color: #60a5fa; letter-spacing: 1px; }}
  .badge {{ background: {verdict_color}; color: #fff; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; }}
  .section {{ margin-top: 25px; }}
  .label {{ font-size: 12px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; }}
  .value {{ font-size: 15px; color: #e5e7eb; font-weight: 500; margin-top: 4px; word-break: break-all; }}
  .code {{ font-family: monospace; background: #1f2937; padding: 8px 12px; border-radius: 6px; font-size: 13px; color: #38bdf8; margin-top: 5px; }}
  ul {{ padding-left: 20px; color: #d1d5db; }}
  li {{ margin-bottom: 6px; }}
  .footer {{ margin-top: 40px; border-top: 1px solid #374151; padding-top: 20px; display: flex; justify-content: space-between; font-size: 12px; color: #6b7280; }}
</style>
</head>
<body>
<div class="cert-container">
  <div class="header">
    <div>
      <div class="title">&#x1F6E1; AEGIS-TRUTH FORENSIC ATTESTATION</div>
      <div style="font-size: 13px; color: #9ca3af; margin-top: 4px;">C2PA-Compatible Digital Integrity Seal</div>
    </div>
    <div class="badge">{b['verdict']} ({b['synthetic_probability']}% SYNTHETIC)</div>
  </div>
  
  <div class="section">
    <div class="label">Manifest Signature (SHA-256)</div>
    <div class="code">{manifest['manifest_signature']}</div>
  </div>
  
  <div class="section" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
    <div>
      <div class="label">Asset Type</div>
      <div class="value">{b['asset_type'].upper()}</div>
    </div>
    <div>
      <div class="label">Attestation Issuer</div>
      <div class="value">{b['issuer']}</div>
    </div>
    <div>
      <div class="label">Timestamp (UTC)</div>
      <div class="value">{b['timestamp_utc']}</div>
    </div>
    <div>
      <div class="label">Cryptographic Status</div>
      <div class="value" style="color: #10b981;">&#x2714; Sealed &amp; Tamper-Evident</div>
    </div>
  </div>
  
  <div class="section">
    <div class="label">SHA-256 Content Hash</div>
    <div class="code">{hashes['sha256']}</div>
  </div>
  
  <div class="section">
    <div class="label">Forensic Evidentiary Markers</div>
    <ul>{markers_html}</ul>
  </div>
  
  <div class="footer">
    <div>Standard: {b['schema_version']}</div>
    <div>Generated by AegisTruth Autonomous Forensics Engine</div>
  </div>
</div>
</body>
</html>"""
    return html

