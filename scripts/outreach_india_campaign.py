"""AegisTruth India B2B Sales Outreach Dispatcher & Campaign Engine.

Targeting small-scale & boutique organizations operating in India:
- Independent Fact-Checking Desks (Boom Live, Alt News, Quint WebQoof, Factly, Vishvas News)
- Indian Digital Multimedia Forensics Consultancies (Cyint Technologies, IFS India, Brilliant Forensic)

Includes:
- Full 1080p MP4 Demo Video with Voiceover & Subtitles (embedded & attached)
- Direct interactive live demo links
- Self-test mode & audit logging
"""

import argparse
import json
import os
import smtplib
import ssl
import time
from datetime import datetime, timezone
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / ".env"
LOG_FILE = ROOT_DIR / "outreach_india_campaign_log.json"
DEMO_VIDEO_PATH = ROOT_DIR / "aegistruth_demo_walkthrough.mp4"


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


# Curated high-impact Indian organizations dealing with synthetic media & digital forensics
INDIAN_TARGET_PROSPECTS = [
    {
        "id": "boomlive",
        "organization": "BOOM Live",
        "contact_email": "assist@boomlive.in",
        "vertical": "Independent Fact-Checking & Media Verification (India)",
        "focus_pain_point": "Debunking viral WhatsApp deepfakes, synthetic political voice notes, and altered videos at scale",
        "primary_feature": "Temporal Video Deepfake Sentinel, Voice Clone Acoustic Lab & Live In-Browser Web Sentinel",
        "subject": "AI Deepfake & Voice Clone Verification Engine for BOOM Live Editorial Desk",
        "custom_context": "BOOM Live is at the forefront of debunking viral misinformation across Indian social media. With the surge of generative AI video (Sora/Kling) and cloned voice notes circulating on messaging apps, your editorial team requires sub-second multi-modal forensic verification tools."
    },
    {
        "id": "altnews",
        "organization": "Alt News",
        "contact_email": "contact@altnews.in",
        "vertical": "Independent Fact-Checking Non-Profit (India)",
        "focus_pain_point": "Exposing hyper-realistic synthetic media, lip-sync deepfakes, and forged photographic evidence",
        "primary_feature": "Visual Error Level Analysis (ELA), 2D Fourier Spectrograms & Video Boundary Warp Detection",
        "subject": "Deepfake Video & Audio Forensic Verification Suite for Alt News Fact-Checking Desk",
        "custom_context": "Alt News's investigative fact-checking regularly uncovers deceptive video splices and manipulated media. AegisTruth provides mathematical, reproducible forensic proofs (spatial FFT harmonics, frame-to-frame optical flow continuity) to rigorously document altered media."
    },
    {
        "id": "thequint_webqoof",
        "organization": "The Quint (WebQoof)",
        "contact_email": "webqoof@thequint.com",
        "vertical": "Digital Fact-Checking Unit (India)",
        "focus_pain_point": "Verifying reader-submitted suspicious media claims and audio voice notes during breaking news",
        "primary_feature": "Acoustic Glottal Pulse Analysis, Perplexity Burstiness & C2PA Provenance Manifests",
        "subject": "Automated AI Deepfake & Audio Clone Detection Toolkit for The Quint WebQoof",
        "custom_context": "WebQoof handles a vast stream of reader queries concerning viral images, clone audio clips, and synthetic videos. AegisTruth delivers a unified multi-modal sentinel that verifies images, video, audio, and claims in a single dashboard."
    },
    {
        "id": "factly_india",
        "organization": "Factly India",
        "contact_email": "factcheck@factly.in",
        "vertical": "Data-Driven Fact-Checking & Public Information (India)",
        "focus_pain_point": "Automated verification of synthetic media claims and digital evidence validation",
        "primary_feature": "REST API Integration, Python SDK & Cognitive Fact-Checking Sentinel",
        "subject": "Multi-Modal AI Deepfake & Cognitive Fact Sentinel for Factly's Verification Team",
        "custom_context": "Factly's data-driven methodology aligns perfectly with AegisTruth's algorithmic approach, providing automated cross-sentence contradiction checking and verifiable cryptographic provenance."
    },
    {
        "id": "vishvasnews",
        "organization": "Vishvas News",
        "contact_email": "contact@vishvasnews.com",
        "vertical": "Multi-Lingual Fact-Checking Network (India)",
        "focus_pain_point": "Rapid multi-lingual debunking of generative AI imagery, cloned politician voices, and deepfake video clips",
        "primary_feature": "Visual ELA, Mel-Spectrogram Acoustic Lab & Chrome Browser Extension",
        "subject": "Deepfake & Synthetic Voice Auditing Sentinel for Vishvas News Editorial Network",
        "custom_context": "Serving audiences across multiple Indian languages, Vishvas News requires rapid, lightweight verification tools that journalists can operate directly in their browser without uploading sensitive files to third-party servers."
    },
    {
        "id": "cyint_technologies",
        "organization": "Cyint Technologies",
        "contact_email": "Info@cyint.in",
        "vertical": "Digital Multimedia Forensics & Cyber Intelligence (India)",
        "focus_pain_point": "Establishing chain of custody, camera sensor PRNU attribution, and court-admissible forensic documentation",
        "primary_feature": "CMOS PRNU Sensor Noise, ELA Variance & Exportable C2PA Court Certificates",
        "subject": "Multi-Modal AI Forensic Tamper Detection & C2PA Provenance Suite for Cyint Technologies",
        "custom_context": "In specialized digital and video forensics investigations, proving whether a video or audio exhibit has been altered by generative AI or tampered with requires rigorous mathematical proof. AegisTruth provides court-ready C2PA manifests with SHA-256 digital seals."
    },
    {
        "id": "ifs_india",
        "organization": "International Forensic Sciences (IFS India)",
        "contact_email": "contact@forensic.co.in",
        "vertical": "Forensic Laboratory & Court Expert Witness Consulting (India)",
        "focus_pain_point": "Providing expert opinions on video and audio evidence authenticity in Indian courts",
        "primary_feature": "Court-Admissible C2PA Provenance Certificates, ELA Heatmaps & Acoustic Pitch Jitter",
        "subject": "AI Deepfake Video & Voice Clone Forensic Analysis Toolkit for IFS Laboratory",
        "custom_context": "As an established forensic laboratory providing scientific evidence for legal proceedings, IFS can leverage AegisTruth's standardized multi-modal pipeline to analyze disputed digital recordings and generate verifiable proof certificates."
    },
    {
        "id": "brilliant_forensic",
        "organization": "Brilliant Forensic Investigation (BFI)",
        "contact_email": "ceo.bfi@gmail.com",
        "vertical": "Audio-Video Forensic Examination & Cyber Crimes (India)",
        "focus_pain_point": "Detecting audio voice manipulation, deepfake video tampering, and forged digital exhibits",
        "primary_feature": "Mel-Spectrogram Acoustics, Temporal Edge Flicker & Offline Enclave Security",
        "subject": "Forensic Audio-Video AI Deepfake Auditing Suite for Brilliant Forensic Investigation",
        "custom_context": "BFI's specialized focus on audio-video authenticity makes AegisTruth an ideal addition to your forensic workbench, enabling rapid detection of synthetic speech models (ElevenLabs) and deepfake frame interpolation."
    }
]


def generate_email_content(prospect, sender_email):
    org_name = prospect["organization"]
    custom_context = prospect["custom_context"]
    focus_pain = prospect["focus_pain_point"]

    text_body = f"""Dear {org_name} Team,

I hope this email finds you well.

As synthetic media and generative AI rapidly proliferate across the Indian digital ecosystem, organizations in {prospect['vertical']} face an escalating challenge: {focus_pain}.

{custom_context}

I am reaching out to introduce AegisTruth Sentinel (https://aryan9891.github.io/AegisTruth/), an enterprise-grade multi-modal cognitive defense suite developed to automate synthetic media detection and digital provenance attestation.

To help you evaluate our capabilities, I have attached a complete 1080p video demonstration (with synchronized voice narration and burnt-in subtitles) walking through each forensic module in action.

CORE FORENSIC CAPABILITIES:

1. Visual & Spatial Forensics Studio:
   • Multi-level Error Level Analysis (ELA) and 2D Fourier Transform (FFT) grid harmonic detection.
   • CMOS sensor PRNU noise correlation to verify physical camera hardware origins vs. diffusion models (Midjourney, Stable Diffusion).

2. Temporal Video Deepfake Sentinel:
   • Frame-to-frame optical flow continuity and inter-frame facial boundary warp analysis.
   • Detects Laplacian edge flickering and splicing discontinuity spikes from Sora, Kling, Runway, and FaceSwap.

3. Acoustic Voice Clone Lab:
   • Mel-spectrogram frequency decomposition, acoustic pitch micro-jitter, and shimmer analysis.
   • Glottal pulse consistency screening to expose ElevenLabs and synthetic speech cloning.

4. Cognitive Text Forensics & Fact Sentinel:
   • Shannon entropy, sentence burstiness, and automated cross-sentence contradiction detection to flag hallucinations and fabricated claims.

5. AI Agent Zero-Trust Guard & Tool Firewall:
   • Real-time jailbreak quarantine (DAN, zero-width Unicode injection) and tool execution sandboxing (blocking unauthorized SQL or system wipes).

6. C2PA Cryptographic Provenance Manifests:
   • Generates verifiable, tamper-evident SHA-256 cryptographic provenance certificates (C2PA v2.1 standard) that can be linked to published reports or submitted in legal discovery.

100% PRIVACY & ZERO DATA LEAKAGE:
AegisTruth runs completely client-side in the browser or on local on-premise hardware. Sensitive investigative leaks, confidential recordings, and legal evidence never leave your internal network.

EXPLORE & TEST LIVE:
• Interactive Web Platform: https://aryan9891.github.io/AegisTruth/
• Complete Demo Video (with Voice & Subtitles): Attached to this email (also downloadable at https://aryan9891.github.io/AegisTruth/downloads/aegistruth_demo_walkthrough.mp4)
• Open-Source GitHub Repository: https://github.com/Aryan9891/AegisTruth

We would be delighted to provide your editorial or forensic team with a dedicated 10-minute technical demonstration or grant access to our API SDK for pilot evaluation.

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
  <div style="max-width: 640px; margin: 0 auto; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; padding: 28px; box-shadow: 0 12px 30px rgba(0,0,0,0.5);">
    
    <!-- Header -->
    <div style="display: flex; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 22px;">
      <div style="font-size: 28px; margin-right: 12px;">🛡️</div>
      <div>
        <h2 style="margin: 0; color: #38bdf8; font-size: 20px; letter-spacing: 0.5px;">AEGIS-TRUTH SENTINEL</h2>
        <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px;">MULTI-MODAL AI FORENSICS &amp; C2PA PROVENANCE SUITE</div>
      </div>
    </div>

    <!-- Intro -->
    <p style="font-size: 15px; color: #e2e8f0; margin-top: 0;">
      Dear <strong>{org_name} Team</strong>,
    </p>
    <p style="font-size: 14px; color: #cbd5e1;">
      As synthetic media and generative AI rapidly proliferate across the Indian digital landscape, organizations in <strong>{prospect['vertical']}</strong> face an escalating operational challenge: <em>{focus_pain}</em>.
    </p>
    <p style="font-size: 14px; color: #cbd5e1; background: rgba(56, 189, 248, 0.06); padding: 14px 16px; border-left: 4px solid #0284c7; border-radius: 4px;">
      {custom_context}
    </p>

    <!-- Attached Demo Video Banner -->
    <div style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(168, 85, 247, 0.15)); border: 1px solid #06b6d4; border-radius: 8px; padding: 16px; margin: 22px 0;">
      <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 22px;">🎬</span>
        <div>
          <strong style="color: #38bdf8; font-size: 14px;">Full Product Demo Video Included (Attached)</strong>
          <p style="margin: 4px 0 0 0; font-size: 12px; color: #cbd5e1;">
            We have attached the complete 1080p demo walkthrough (<strong><code>aegistruth_demo_walkthrough.mp4</code></strong>) with <strong>voice explanation and synchronized burned-in subtitles</strong> covering each forensic lab in action.
          </p>
        </div>
      </div>
    </div>

    <!-- Core Forensic Capabilities -->
    <div style="margin: 22px 0;">
      <h3 style="color: #06b6d4; font-size: 14px; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 12px;">Core Forensic Arsenal:</h3>
      
      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
        <strong style="color: #38bdf8; font-size: 13px;">👁️ Visual &amp; Spatial Forensics Studio</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Multi-level Error Level Analysis (ELA), 2D Fourier Transform (FFT) grid harmonic lattice detection, and CMOS sensor PRNU noise correlation.</p>
      </div>

      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
        <strong style="color: #a855f7; font-size: 13px;">🎬 Temporal Video Deepfake Sentinel</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Inter-frame optical flow continuity, boundary edge flickering analysis, and generative warping detection (Sora, Kling, Runway, FaceSwap).</p>
      </div>

      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
        <strong style="color: #ec4899; font-size: 13px;">🎙️ Acoustic Voice Clone Lab</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Mel-spectrogram analysis, pitch micro-jitter, and glottal pulse consistency to screen out ElevenLabs and synthetic WhatsApp voice notes.</p>
      </div>

      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
        <strong style="color: #f59e0b; font-size: 13px;">📝 Cognitive Text &amp; Fact Sentinel</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Sentence burstiness, Shannon entropy, and automated cross-sentence contradiction checking to expose hallucinatory AI claims.</p>
      </div>

      <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px;">
        <strong style="color: #10b981; font-size: 13px;">🔒 C2PA Cryptographic Provenance Manifests</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Attaches immutable SHA-256 cryptographic provenance manifests and exportable HTML proof certificates for publication or legal discovery.</p>
      </div>
    </div>

    <!-- Security & Privacy Highlight -->
    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 14px 16px; margin-bottom: 22px;">
      <strong style="color: #34d399; font-size: 13px;">🛡️ 100% Privacy &amp; Zero Data Leakage</strong>
      <p style="margin: 4px 0 0 0; font-size: 12px; color: #cbd5e1;">AegisTruth can operate completely offline on local hardware or client-side in the browser. Confidential whistleblower leads, legal exhibits, and recordings never leave your internal enclave.</p>
    </div>

    <!-- Call to Action Buttons -->
    <div style="text-align: center; margin: 26px 0;">
      <a href="https://aryan9891.github.io/AegisTruth/" style="display: inline-block; background: linear-gradient(135deg, #0284c7, #9333ea); color: #ffffff; text-decoration: none; padding: 12px 26px; border-radius: 6px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4); margin-right: 8px;">
        Launch Live Sentinel &rarr;
      </a>
      <a href="https://aryan9891.github.io/AegisTruth/downloads/aegistruth_demo_walkthrough.mp4" style="display: inline-block; background: #1e293b; color: #38bdf8; border: 1px solid #38bdf8; text-decoration: none; padding: 11px 20px; border-radius: 6px; font-weight: bold; font-size: 13px;">
        Download Walkthrough Video (.MP4)
      </a>
    </div>

    <p style="font-size: 13px; color: #94a3b8; margin-bottom: 24px;">
      We would be delighted to provide a 10-minute technical demonstration for your editorial or forensic team, or grant access to our API SDK for pilot evaluation.<br><br>
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


def send_single_email_with_video(sender, password, recipient, subject, text, html, attach_video=True):
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f"Aryan Sachin - AegisTruth <{sender}>"
    msg["To"] = recipient
    msg["Reply-To"] = sender

    # Body container
    body_part = MIMEMultipart("alternative")
    body_part.attach(MIMEText(text, "plain"))
    body_part.attach(MIMEText(html, "html"))
    msg.attach(body_part)

    # Attach MP4 Demo Video if requested and file exists
    if attach_video and DEMO_VIDEO_PATH.exists():
        with open(DEMO_VIDEO_PATH, "rb") as vf:
            part = MIMEBase("video", "mp4")
            part.set_payload(vf.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="aegistruth_demo_walkthrough.mp4"'
            )
            msg.attach(part)

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
    parser = argparse.ArgumentParser(description="AegisTruth India B2B Sales Outreach Dispatcher")
    parser.add_argument("--mode", choices=["preview", "self-test", "send-one", "send-all"], default="preview",
                        help="Action mode: preview, self-test (sends with video to user inbox), send-one, or send-all")
    parser.add_argument("--target", type=str, default="boomlive", help="Prospect ID for send-one mode")
    parser.add_argument("--no-attach", action="store_true", help="Do not attach video file to reduce email size")
    args = parser.parse_args()

    sender, password = load_credentials()
    if not sender or not password:
        print("[ERROR] Credentials not found in .env")
        return

    print("=" * 70)
    print("  AEGIS-TRUTH INDIA B2B OUTREACH CAMPAIGN ENGINE")
    print(f"  Sender: {sender}")
    print(f"  Active Indian Prospects in Pipeline: {len(INDIAN_TARGET_PROSPECTS)}")
    print(f"  Demo Video Available: {DEMO_VIDEO_PATH.exists()} ({os.path.getsize(DEMO_VIDEO_PATH)/(1024*1024):.2f} MB)")
    print("=" * 70)

    attach_video = not args.no_attach

    if args.mode == "preview":
        print("\n[*] PREVIEW MODE (No emails sent):\n")
        for i, p in enumerate(INDIAN_TARGET_PROSPECTS, 1):
            print(f"[{i}/{len(INDIAN_TARGET_PROSPECTS)}] ID: {p['id']}")
            print(f"  Organization : {p['organization']}")
            print(f"  Recipient    : {p['contact_email']}")
            print(f"  Vertical     : {p['vertical']}")
            print(f"  Subject      : {p['subject']}")
            print(f"  Pain Point   : {p['focus_pain_point']}")
            print("-" * 70)
        print("\nTo send a complete test email with video attachment to your inbox, run:")
        print("  python scripts/outreach_india_campaign.py --mode self-test")
        print("\nTo dispatch outreach to all 8 Indian organizations with video, run:")
        print("  python scripts/outreach_india_campaign.py --mode send-all")

    elif args.mode == "self-test":
        print(f"\n[*] SELF-TEST MODE: Sending sample pitch + video attachment to {sender}...")
        sample = INDIAN_TARGET_PROSPECTS[0]  # BOOM Live template
        text, html = generate_email_content(sample, sender)
        subject = f"[Sample India Pitch + Demo Video] {sample['subject']}"
        try:
            send_single_email_with_video(sender, password, sender, subject, text, html, attach_video=attach_video)
            print(f"  ✔ Sample pitch with demo video successfully delivered to {sender}!")
            print("  Check your Gmail inbox to review the attached MP4 video and styling.")
        except Exception as e:
            print(f"  ✖ Failed to send: {e}")

    elif args.mode == "send-one":
        match = next((p for p in INDIAN_TARGET_PROSPECTS if p["id"] == args.target), None)
        if not match:
            print(f"[ERROR] Target '{args.target}' not found in prospects list.")
            return

        print(f"\n[*] DISPATCHING OUTREACH to {match['organization']} ({match['contact_email']})...")
        text, html = generate_email_content(match, sender)
        try:
            send_single_email_with_video(sender, password, match["contact_email"], match["subject"], text, html, attach_video=attach_video)
            print(f"  ✔ Email + Demo Video dispatched to {match['contact_email']}!")
            log_dispatch({
                "prospect_id": match["id"],
                "organization": match["organization"],
                "recipient": match["contact_email"],
                "subject": match["subject"],
                "video_attached": attach_video,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "status": "SENT"
            })
        except Exception as e:
            print(f"  ✖ Dispatch failed: {e}")

    elif args.mode == "send-all":
        print(f"\n[*] BATCH DISPATCHING OUTREACH to {len(INDIAN_TARGET_PROSPECTS)} Indian organizations...")
        for i, match in enumerate(INDIAN_TARGET_PROSPECTS, 1):
            print(f"  [{i}/{len(INDIAN_TARGET_PROSPECTS)}] Sending to {match['organization']} ({match['contact_email']})...")
            text, html = generate_email_content(match, sender)
            try:
                send_single_email_with_video(sender, password, match["contact_email"], match["subject"], text, html, attach_video=attach_video)
                print(f"    ✔ Sent with Demo Video!")
                log_dispatch({
                    "prospect_id": match["id"],
                    "organization": match["organization"],
                    "recipient": match["contact_email"],
                    "subject": match["subject"],
                    "video_attached": attach_video,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "status": "SENT"
                })
                # Throttle slightly to comply with Google SMTP rate limits and avoid spam classification
                if i < len(INDIAN_TARGET_PROSPECTS):
                    time.sleep(4)
            except Exception as e:
                print(f"    ✖ Failed: {e}")


if __name__ == "__main__":
    main()
