"""AegisTruth Email Dispatcher Verification Script."""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    env_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().replace(" ", "")
    return env_vars


def send_test_email():
    env = load_env()
    sender = env.get("SENDER_EMAIL", "aryansachinixd@gmail.com")
    password = env.get("GMAIL_APP_PASSWORD", "")

    if not password:
        print("ERROR: GMAIL_APP_PASSWORD not found in .env")
        return False

    receiver = sender
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🛡️ AegisTruth Sentinel: Email Dispatcher Connected"
    msg["From"] = f"AegisTruth Sentinel <{sender}>"
    msg["To"] = receiver

    text = (
        "Hello Aryan,\n\n"
        "Your AegisTruth email dispatcher is now successfully connected to "
        f"{sender} via secure TLS on smtp.gmail.com:587.\n\n"
        "The automated B2B sales outreach engine is authenticated and ready to dispatch."
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 25px; margin: 0;">
  <div style="max-width: 600px; margin: 0 auto; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
    <div style="display: flex; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 20px;">
      <div style="font-size: 24px; margin-right: 10px;">🛡️</div>
      <div>
        <h2 style="margin: 0; color: #38bdf8; font-size: 18px; letter-spacing: 0.5px;">AEGIS-TRUTH SENTINEL</h2>
        <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px;">AUTONOMOUS COGNITIVE DEFENSE DISPATCHER</div>
      </div>
    </div>
    
    <p style="font-size: 15px; color: #cbd5e1; line-height: 1.6;">
      Hello <strong>Aryan</strong>,<br><br>
      Your email dispatcher is now <strong>successfully connected and authenticated</strong> for <code>{sender}</code> via secure Google SMTP (TLS port 587).
    </p>

    <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 14px 16px; border-radius: 6px; margin: 20px 0;">
      <div style="font-size: 14px; font-weight: bold; color: #34d399;">✔ SMTP HANDSHAKE: SUCCESS</div>
      <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Outbound connection authenticated. Ready to launch B2B outreach to prospective organizations.</div>
    </div>

    <div style="border-top: 1px solid #1e293b; padding-top: 16px; font-size: 11px; color: #64748b;">
      AegisTruth Sentinel Engine • Cryptographic Provenance &amp; Multi-Modal Forensics
    </div>
  </div>
</body>
</html>"""

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"SUCCESS: Verification email successfully delivered to {receiver}!")
        return True
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    send_test_email()

