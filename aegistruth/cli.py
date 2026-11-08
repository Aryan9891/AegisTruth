"""AegisTruth Command Line Interface (CLI)."""

import sys
import json
import argparse
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from aegistruth.core.image_forensics import analyze_image
from aegistruth.core.audio_forensics import analyze_audio
from aegistruth.core.text_forensics import analyze_text
from aegistruth.core.fact_checker import verify_facts
from aegistruth.core.agent_guard import inspect_prompt, inspect_tool_call
from aegistruth.core.video_forensics import analyze_video
from aegistruth.core.provenance import generate_provenance_manifest

def print_banner():
    banner = r"""
========================================================================
   ___    ___  ____ ___ ____   _____ ____  _   _ _____ _   _ 
  / _ \  | __|/ ___|_ _/ ___| |_   _|  _ \| | | |_   _| | | |
 / /_\ \ | _|| |  _ | |\___ \   | | | |_) | | | | | | | |_| |
/_/   \_\|___|\____|___|____/   |_| |_| \_\___/  |_|  |___|_|
   Autonomous Multi-Modal AI Forensics & Cognitive Sentinel
========================================================================
    """
    print(banner)

def main():
    parser = argparse.ArgumentParser(
        description="AegisTruth: Autonomous Multi-Modal AI Forensics & Cognitive Defense CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Launch the Web Studio & API server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")

    # Image command
    img_parser = subparsers.add_parser("image", help="Analyze image for synthetic/deepfake artifacts")
    img_parser.add_argument("path", help="Path to image file (JPEG, PNG, WebP)")
    img_parser.add_argument("--json", action="store_true", help="Output full JSON results")

    # Audio command
    audio_parser = subparsers.add_parser("audio", help="Analyze audio for synthetic voice clone artifacts")
    audio_parser.add_argument("path", help="Path to audio file (WAV)")
    audio_parser.add_argument("--json", action="store_true", help="Output full JSON results")

    # Text command
    text_parser = subparsers.add_parser("text", help="Analyze text for AI generation markers")
    text_parser.add_argument("input", help="Text string or path to text file")
    text_parser.add_argument("--json", action="store_true", help="Output full JSON results")

    # Fact check command
    fact_parser = subparsers.add_parser("factcheck", help="Verify claims and detect contradictions")
    fact_parser.add_argument("input", help="Text string or path to text file")
    fact_parser.add_argument("--json", action="store_true", help="Output full JSON results")

    # Video command
    video_parser = subparsers.add_parser("video", help="Analyze video for temporal deepfake flickers & warping")
    video_parser.add_argument("path", help="Path to video file (GIF, MP4, WebM)")
    video_parser.add_argument("--json", action="store_true", help="Output full JSON results")

    # Guard command
    guard_parser = subparsers.add_parser("guard", help="Scan prompt for jailbreaks and prompt injection")
    guard_parser.add_argument("prompt", help="Prompt string to scan")
    guard_parser.add_argument("--json", action="store_true", help="Output full JSON results")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.command == "serve":
        print_banner()
        print(f"[*] Starting AegisTruth Web Studio on http://{args.host}:{args.port}")
        uvicorn.run("aegistruth.api.app:app", host=args.host, port=args.port, reload=False)

    elif args.command == "image":
        file_path = Path(args.path)
        if not file_path.exists():
            print(f"Error: File not found: {args.path}")
            sys.exit(1)
        data = file_path.read_bytes()
        res = analyze_image(data)
        manifest = generate_provenance_manifest("image", data, res)
        res["provenance_manifest"] = manifest
        if args.json:
            # Omit huge base64 images in cli json output
            res_clean = {k: v for k, v in res.items() if k != "visualizations"}
            print(json.dumps(res_clean, indent=2))
        else:
            print_banner()
            print(f"File: {args.path}")
            print(f"Verdict: {res['verdict']}")
            print(f"Synthetic Probability: {res['synthetic_probability']}%")
            print(f"Description: {res['confidence_description']}")
            print("Forensic Findings:")
            for r in res["forensic_reasons"]:
                print(f"  - {r}")
            print(f"Manifest Signature: {manifest['manifest_signature'][:16]}...")

    elif args.command == "video":
        file_path = Path(args.path)
        if not file_path.exists():
            print(f"Error: File not found: {args.path}")
            sys.exit(1)
        data = file_path.read_bytes()
        res = analyze_video(data)
        manifest = generate_provenance_manifest("video", data, res)
        if args.json:
            res_clean = {k: v for k, v in res.items() if k != "visualizations"}
            print(json.dumps(res_clean, indent=2))
        else:
            print_banner()
            print(f"File: {args.path}")
            print(f"Verdict: {res['verdict']}")
            print(f"Deepfake Probability: {res['synthetic_probability']}%")
            print("Forensic Findings:")
            for r in res["forensic_reasons"]:
                print(f"  - {r}")
            print(f"Frames: {res['metrics']['frames_analyzed']} | Temporal Flicker: {res['metrics']['temporal_flicker_score']}")

    elif args.command == "audio":
        file_path = Path(args.path)
        if not file_path.exists():
            print(f"Error: File not found: {args.path}")
            sys.exit(1)
        data = file_path.read_bytes()
        res = analyze_audio(data)
        manifest = generate_provenance_manifest("audio", data, res)
        if args.json:
            res_clean = {k: v for k, v in res.items() if k != "visualizations"}
            print(json.dumps(res_clean, indent=2))
        else:
            print_banner()
            print(f"File: {args.path}")
            print(f"Verdict: {res['verdict']}")
            print(f"Voice Clone Probability: {res['synthetic_probability']}%")
            print("Forensic Findings:")
            for r in res["forensic_reasons"]:
                print(f"  - {r}")
            print(f"Duration: {res['metrics']['duration_seconds']}s | Jitter: {res['metrics']['pitch_jitter']*100:.2f}%")

    elif args.command == "text":
        input_val = args.input
        if Path(input_val).exists():
            input_val = Path(input_val).read_text(encoding="utf-8")
        res = analyze_text(input_val)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print_banner()
            print(f"Verdict: {res['verdict']}")
            print(f"AI Likelihood: {res['synthetic_probability']}%")
            print(f"Burstiness Index: {res['metrics']['burstiness_index']}")
            print(f"Shannon Entropy: {res['metrics']['shannon_entropy']} bits/token")
            print("Forensic Findings:")
            for r in res["forensic_reasons"]:
                print(f"  - {r}")

    elif args.command == "factcheck":
        input_val = args.input
        if Path(input_val).exists():
            input_val = Path(input_val).read_text(encoding="utf-8")
        res = verify_facts(input_val)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print_banner()
            print(f"Factuality Score: {res['overall_factuality_score']}/100")
            print(f"Total Claims Analyzed: {res['total_claims_extracted']}")
            print(f"Verified Claims: {res['verified_grounded_count']}")
            if res['internal_contradictions']:
                print("\n[!] Contradictions Found:")
                for c in res['internal_contradictions']:
                    print(f"  - Claim {c['claim_a_id']} vs {c['claim_b_id']}: {c['issue']}")
            if res['anachronisms_detected']:
                print("\n[!] Anachronisms / Physical Violations:")
                for a in res['anachronisms_detected']:
                    print(f"  - {a['description']}")

    elif args.command == "guard":
        res = inspect_prompt(args.prompt)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print_banner()
            print(f"Verdict: {res['verdict']}")
            print(f"Action: {res['action']}")
            print(f"Threat Score: {res['threat_score']}/100")
            if res["threats"]:
                print("Detected Threats:")
                for t in res["threats"]:
                    print(f"  - [{t['type']}] (Severity: {t['severity_score']}): {t['recommendation']}")

if __name__ == "__main__":
    main()
