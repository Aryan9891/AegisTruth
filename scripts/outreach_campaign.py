"""AegisTruth B2B Sales Outreach Dispatcher & Campaign Engine.

Features:
- Multi-vertical targeting (Investigative Media, Fact Checkers, Digital Forensics, KYC/Fintech)
- Highly personalized executive pitch templates emphasizing C2PA, ELA, FFT, and Voice Forensics
- Dry-run preview mode & Self-test delivery to user's inbox
- Audit logging of all outbound emails
"""

import argparse
import json
import os
import smtplib
import ssl
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / ".env"
LOG_FILE = ROOT_DIR / "outreach_campaign_log.json"


def load_credentials():
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().replace(" ", "")
    return env_vars.get("SENDER_EMAIL", "aryansachinixd@gmail.com"), env_vars.get("GMAIL_APP_PASSWORD", "")


# Curated high-impact small & mid-sized organizations needing deepfake & forensic verification tech
TARGET_PROSPECTS = [
    {
        "id": "tbij",
        "organization": "The Bureau of Investigative Journalism",
        "contact_email": "info@thebureauinvestigates.com",
        "vertical": "Investigative Journalism",
        "focus_pain_point": "Verifying leaked video, audio, and whistleblower media before publishing",
        "primary_feature": "Temporal Video Sentinel, Voice Clone Acoustic Lab & C2PA Provenance Manifests",
        "subject": "Deepfake verification & source media authentication for The Bureau of Investigative Journalism",
        "custom_note": "Your investigative investigations frequently handle sensitive external leaks where verifying that video footage or audio recordings have not been altered or AI-generated is critical before reporting."
    },
    {
        "id": "factcheck_org",
        "organization": "FactCheck.org",
        "contact_email": "Editor@FactCheck.org",
        "vertical": "Independent Fact-Checking",
        "focus_pain_point": "Rapid debunking of viral generative AI hoaxes, synthetic political speeches, and face-swaps",
        "primary_feature": "Visual Error Level Analysis (ELA), 2D Fourier Spectrograms & Cognitive Contradiction Checker",
        "subject": "AI Deepfake & Synthetic Media Verification Tool for FactCheck.org Editorial Desk",
        "custom_note": "With generative video (Sora, Kling) and voice cloning escalating across election cycles, editorial verification needs sub-second multi-modal auditing tools."
    },
    {
        "id": "fullfact_uk",
        "organization": "Full Fact UK",
        "contact_email": "press@fullfact.org",
        "vertical": "Independent Fact-Checking",
        "focus_pain_point": "Automated detection of synthetic media claims, cloned voices, and fabricated photographic evidence",
        "primary_feature": "Acoustic Glottal Pulse Forensics & Multi-Modal Sentinel",
        "subject": "Automated Deepfake & Acoustic Forensics for Full Fact's Verification Team",
        "custom_note": "Full Fact leads the field in automated fact-checking; AegisTruth provides an integrated multi-modal engine that can integrate directly via API into claim-verification pipelines."
    },
    {
        "id": "primeau_forensics",
        "organization": "Primeau Forensics",
        "contact_email": "sales@primeaucompanies.com",
        "vertical": "Digital Multimedia Forensics",
        "focus_pain_point": "Demonstrating mathematical chain of custody and algorithmic tamper detection for court testimony",
        "primary_feature": "CMOS PRNU Sensor Noise, ELA Heatmaps & Exportable C2PA Court Certificates",
        "subject": "Multi-Modal AI Tamper Detection & C2PA Provenance for Digital Forensics Cases",
        "custom_note": "In digital legal evidence consulting, having verifiable SHA-256 cryptographic provenance seals alongside Fourier frequency harmonic breakdowns provides rigorous documentation for court filings."
    },
    {
        "id": "blackdog_forensics",
        "organization": "Black Dog Forensics",
        "contact_email": "retrievethetruth@bdforensics.com",
        "vertical": "Digital Multimedia Forensics",
        "focus_pain_point": "Detecting deepfake video face-swapping and acoustic audio tampering in investigative matters",
        "primary_feature": "Laplacian Boundary Edge Flicker, Pitch Jitter Analysis & Client-Side Offline Engine",
        "subject": "Forensic Video & Acoustic Deepfake Auditing Suite for Black Dog Forensics",
        "custom_note": "Our platform operates completely offline in-browser or on local hardware, ensuring client multimedia evidence never leaves your secure forensic enclave."
    },
    {
        "id": "ijf_canada",
        "organization": "The Investigative Journalism Foundation",
        "contact_email": "info@theijf.org",
        "vertical": "Investigative Journalism",
        "focus_pain_point": "Protecting investigative reporting against synthetic documents, voice fakes, and fabricated leaks",
        "primary_feature": "Multi-Modal Forensic Arsenal & Live Web Sentinel",
        "subject": "Deepfake Verification & Source Authenticity Tools for The Investigative Journalism Foundation",
        "custom_note": "Public interest investigative journalism requires airtight media verification before going to press. AegisTruth helps newsrooms detect synthetic anomalies before publication."
    }
]


def generate_email_content(prospect, sender_email):
    org_name = prospect["organization"]
    custom_note = prospect["custom_note"]
    primary_feat = prospect["primary_feature"]

    text_body = f"""Dear {org_name} Team,

I hope this email finds you well.

With the rapid acceleration of hyper-realistic generative video (Sora, Kling, Runway), audio voice cloning (ElevenLabs), and synthetic image diffusion, organizations in {prospect['vertical']} face an escalating operational challenge: {prospect['focus_pain_point']}.

{custom_note}

I am reaching out to introduce AegisTruth Sentinel (https://aryan9891.github.io/AegisTruth/), an enterprise-grade multi-modal cognitive defense suite developed to automate synthetic media detection and digital provenance attestation:

1. Visual & Spatial Forensics Studio:
   • Multi-level Error Level Analysis (ELA) and 2D Fourier Transform (FFT) grid harmonic detection.
   • CMOS sensor PRNU noise correlation to verify physical camera hardware origins.

2. Temporal Video Deepfake Sentinel:
   • Frame-to-frame optical flow continuity and inter-frame facial boundary warp analysis.
   • Real-time motion acceleration variance and splicing discontinuity spike detection.

3. Acoustic Voice Clone Lab:
   • Mel-spectrogram frequency decomposition, acoustic pitch jitter, and shimmer analysis.
   • Glottal pulse consistency screening to expose synthetic speech synthesis.

4. C2PA Cryptographic Provenance Manifests:
   • Generates verifiable, tamper-evident SHA-256 cryptographic provenance certificates (C2PA v2.1 standard) that can be archived with verified media or published alongside reports.

5. Zero Third-Party Data Leakage:
   • AegisTruth runs completely on-premises or client-side in-browser via WebAssembly/HTML5 Canvas, ensuring sensitive investigative leads, client recordings, or proprietary assets never leave your secure perimeter.

You can explore and test the platform directly in your browser without registration:
https://aryan9891.github.io/AegisTruth/

We would be delighted to set up a brief 10-minute walkthrough or provide your technical team with API access and a dedicated pilot evaluation.

Are you available for a brief conversation this week?

Warm regards,

Aryan Sachin
Founder, AegisTruth Sentinel Engine
Email: {sender_email}
Website: https://aryan9891.github.io/AegisTruth/
GitHub: https://github.com/Aryan9891/AegisTruth
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 24px; margin: 0; line-height: 1.6;">
  <div style="max-width: 620px; margin: 0 auto; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; padding: 28px; box-shadow: 0 12px 30px rgba(0,0,0,0.45);">
    
    <!-- Header -->
    <div style="display: flex; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 22px;">
      <div style="font-size: 26px; margin-right: 12px;">🛡️</div>
      <div>
        <h2 style="margin: 0; color: #38bdf8; font-size: 19px; letter-spacing: 0.5px;">AEGIS-TRUTH SENTINEL</h2>
        <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px;">MULTI-MODAL FORENSICS &amp; C2PA PROVENANCE SUITE</div>
      </div>
    </div>

    <!-- Intro -->
    <p style="font-size: 15px; color: #e2e8f0; margin-top: 0;">
      Dear <strong>{org_name} Team</strong>,
    </p>
    <p style="font-size: 14px; color: #cbd5e1;">
      With the proliferation of hyper-realistic generative video (Sora, Kling), AI voice cloning, and synthetic diffusion imagery, organizations in <strong>{prospect['vertical']}</strong> face an escalating challenge: <em>{prospect['focus_pain_point']}</em>.
    </p>
    <p style="font-size: 14px; color: #cbd5e1; background: rgba(56, 189, 248, 0.05); padding: 12px 14px; border-left: 3px solid #0284c7; border-radius: 4px;">
      {custom_note}
    </p>

    <!-- Core Capabilities -->
    <div style="margin: 22px 0;">
      <h3 style="color: #06b6d4; font-size: 14px; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 12px;">Core Forensic Capabilities:</h3>
      
      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
        <strong style="color: #38bdf8; font-size: 13px;">👁️ Visual &amp; Spatial Forensics</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Multi-level Error Level Analysis (ELA), 2D Fourier Transform (FFT) grid lattice detection, and CMOS sensor PRNU noise correlation.</p>
      </div>

      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
        <strong style="color: #a855f7; font-size: 13px;">🎬 Temporal Video Deepfake Sentinel</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Inter-frame optical flow continuity, boundary edge flickering analysis, and generative warping detection with sub-second processing.</p>
      </div>

      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
        <strong style="color: #ec4899; font-size: 13px;">🎙️ Acoustic Voice Clone Lab</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Mel-spectrogram analysis, pitch jitter, shimmer acoustics, and glottal pulse consistency to screen out ElevenLabs/TTS voice clones.</p>
      </div>

      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px;">
        <strong style="color: #10b981; font-size: 13px;">🔒 C2PA Cryptographic Provenance Seals</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Attaches immutable SHA-256 cryptographic provenance manifests and exportable HTML proof certificates for publication or legal discovery.</p>
      </div>
    </div>

    <!-- Security & Deployment Highlight -->
    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 14px 16px; margin-bottom: 22px;">
      <strong style="color: #34d399; font-size: 13px;">🛡️ 100% Privacy &amp; Zero Data Leakage</strong>
      <p style="margin: 4px 0 0 0; font-size: 12px; color: #cbd5e1;">AegisTruth can operate completely offline on local hardware or client-side in the browser. Confidential investigative media and evidence never leave your internal network.</p>
    </div>

    <!-- Call to Action Button -->
    <div style="text-align: center; margin: 26px 0;">
      <a href="https://aryan9891.github.io/AegisTruth/" style="display: inline-block; background: linear-gradient(135deg, #0284c7, #9333ea); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4);">
        Test Interactive Web Sentinel &rarr;
      </a>
    </div>

    <p style="font-size: 13px; color: #94a3b8; margin-bottom: 24px;">
      We would be delighted to provide a 10-minute technical demonstration tailored to your workflow, or grant access to our API integration SDK for pilot benchmarking.<br><br>
      Would you be open to a brief conversation this week?
    </p>

    <!-- Sign-off -->
    <div style="border-top: 1px solid #1e293b; padding-top: 16px; font-size: 12px; color: #94a3b8;">
      <strong style="color: #f1f5f9; font-size: 13px;">Aryan Sachin</strong><br>
      Founder, AegisTruth Sentinel Engine<br>
      Email: <a href="mailto:{sender_email}" style="color: #38bdf8; text-decoration: none;">{sender_email}</a><br>
      Live Platform: <a href="https://aryan9891.github.io/AegisTruth/" style="color: #38bdf8; text-decoration: none;">aryan9891.github.io/AegisTruth</a><br>
      Repository: <a href="https://github.com/Aryan9891/AegisTruth" style="color: #38bdf8; text-decoration: none;">github.com/Aryan9891/AegisTruth</a>
    </div>

  </div>
</body>
</html>"""

    return text_body, html_body


def send_single_email(sender, password, recipient, subject, text, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Aryan Sachin - AegisTruth <{sender}>"
    msg["To"] = recipient
    msg["Reply-To"] = sender

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())


def log_dispatch(record):
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(record)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="AegisTruth B2B Outreach Dispatcher")
    parser.add_argument("--mode", choices=["preview", "self-test", "send-one", "send-all"], default="preview",
                        help="Action mode: preview, self-test (sends sample to user inbox), send-one, or send-all")
    parser.add_argument("--target", type=str, default="tbij", help="Prospect ID for send-one mode")
    args = parser.parse_args()

    sender, password = load_credentials()
    if not sender or not password:
        print("[ERROR] Credentials not found in .env")
        return

    print("=" * 65)
    print("  AEGIS-TRUTH B2B COLD OUTREACH CAMPAIGN ENGINE")
    print(f"  Sender: {sender}")
    print(f"  Active Prospects in Pipeline: {len(TARGET_PROSPECTS)}")
    print("=" * 65)

    if args.mode == "preview":
        print("\n[*] PREVIEW MODE (No emails sent):\n")
        for i, p in enumerate(TARGET_PROSPECTS, 1):
            print(f"[{i}/{len(TARGET_PROSPECTS)}] ID: {p['id']}")
            print(f"  Organization : {p['organization']}")
            print(f"  Recipient    : {p['contact_email']}")
            print(f"  Vertical     : {p['vertical']}")
            print(f"  Subject      : {p['subject']}")
            print(f"  Core Feature : {p['primary_feature']}")
            print("-" * 65)
        print("\nTo send a test copy of these pitches to your own email, run:")
        print("  python scripts/outreach_campaign.py --mode self-test")
        print("\nTo dispatch outreach to a specific organization, run:")
        print("  python scripts/outreach_campaign.py --mode send-one --target tbij")
        print("\nTo dispatch outreach to all target prospects, run:")
        print("  python scripts/outreach_campaign.py --mode send-all")

    elif args.mode == "self-test":
        print(f"\n[*] SELF-TEST MODE: Sending sample pitch to {sender}...")
        sample = TARGET_PROSPECTS[0]  # TBIJ template
        text, html = generate_email_content(sample, sender)
        subject = f"[Sample Pitch Preview] {sample['subject']}"
        try:
            send_single_email(sender, password, sender, subject, text, html)
            print(f"  ✔ Sample pitch successfully delivered to {sender}!")
            print("  Check your Gmail inbox to review the exact design, formatting, and messaging.")
        except Exception as e:
            print(f"  ✖ Failed to send: {e}")

    elif args.mode == "send-one":
        match = next((p for p in TARGET_PROSPECTS if p["id"] == args.target), None)
        if not match:
            print(f"[ERROR] Target '{args.target}' not found in prospects list.")
            return

        print(f"\n[*] DISPATCHING OUTREACH to {match['organization']} ({match['contact_email']})...")
        text, html = generate_email_content(match, sender)
        try:
            send_single_email(sender, password, match["contact_email"], match["subject"], text, html)
            print(f"  ✔ Email successfully dispatched to {match['contact_email']}!")
            log_dispatch({
                "prospect_id": match["id"],
                "organization": match["organization"],
                "recipient": match["contact_email"],
                "subject": match["subject"],
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "status": "SENT"
            })
        except Exception as e:
            print(f"  ✖ Dispatch failed: {e}")

    elif args.mode == "send-all":
        print(f"\n[*] BATCH DISPATCHING OUTREACH to {len(TARGET_PROSPECTS)} organizations...")
        for i, match in enumerate(TARGET_PROSPECTS, 1):
            print(f"  [{i}/{len(TARGET_PROSPECTS)}] Sending to {match['organization']} ({match['contact_email']})...")
            text, html = generate_email_content(match, sender)
            try:
                send_single_email(sender, password, match["contact_email"], match["subject"], text, html)
                print(f"    ✔ Sent!")
                log_dispatch({
                    "prospect_id": match["id"],
                    "organization": match["organization"],
                    "recipient": match["contact_email"],
                    "subject": match["subject"],
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "status": "SENT"
                })
                # Throttle slightly to comply with Google SMTP rate limits and avoid spam classification
                if i < len(TARGET_PROSPECTS):
                    time.sleep(3)
            except Exception as e:
                print(f"    ✖ Failed: {e}")


if __name__ == "__main__":
    main()
