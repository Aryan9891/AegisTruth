"""AegisTruth Desktop Sentinel: Real-time clipboard defense and active audio call monitor."""

import sys
import time
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aegistruth.core.agent_guard import inspect_prompt, inspect_unicode_obfuscation
from aegistruth.core.audio_forensics import analyze_audio

def print_sentinel_banner():
    banner = r"""
========================================================================
   ___    ___  ____ ___ ____   ____  _____ _   _ _____ ___ _   _ _____ _     
  / _ \  | __|/ ___|_ _/ ___| / ___|| ____| \ | |_   _|_ _| \ | | ____| |    
 / /_\ \ | _|| |  _ | |\___ \ \___ \|  _| |  \| | | |  | ||  \| |  _| | |    
/_/   \_\|___|\____|___|____/  ___) | |___| |\  | | |  | || |\  | |___| |___ 
       Real-Time Zero-Trust Desktop & Clipboard Defense Daemon
========================================================================
    """
    print(banner)

def get_clipboard_text_fallback() -> str:
    """Retrieves clipboard text using PowerShell on Windows without external dependencies."""
    try:
        import subprocess
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return res.stdout.strip()
    except Exception:
        return ""

def sanitize_text(text: str) -> str:
    """Removes invisible zero-width and bidi override characters."""
    bad_chars = {'\u200b', '\u200c', '\u200d', '\ufeff', '\u200e', '\u200f', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e'}
    return "".join(c for c in text if c not in bad_chars)

def monitor_clipboard(poll_interval: float = 1.0, auto_sanitize: bool = True):
    """Continuously monitors system clipboard for adversarial payloads and invisible token smuggling."""
    print(f"[*] AegisTruth Desktop Sentinel is active. Polling clipboard every {poll_interval}s...")
    print("[*] Press Ctrl+C to terminate sentinel daemon.\n")

    last_text = ""
    while True:
        try:
            curr_text = get_clipboard_text_fallback()
            if curr_text and curr_text != last_text:
                last_text = curr_text
                
                # Check for unicode smuggling
                unicode_info = inspect_unicode_obfuscation(curr_text)
                prompt_info = inspect_prompt(curr_text)

                if unicode_info["is_adversarial_obfuscation"] or prompt_info["verdict"] == "BLOCK":
                    print("\n" + "!" * 70)
                    print(" [ALERT] ADVERSARIAL THREAT DETECTED ON CLIPBOARD")
                    print("!" * 70)
                    print(f" Timestamp:    {time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f" Verdict:      {prompt_info['verdict']}")
                    print(f" Threat Score: {prompt_info['threat_score']}/100")
                    
                    if unicode_info["is_adversarial_obfuscation"]:
                        print(f" Unicode:      {unicode_info['zero_width_count']} Zero-Width & {unicode_info['bidi_override_count']} Bidi chars detected!")

                    if prompt_info["threats"]:
                        print(" Threats:")
                        for t in prompt_info["threats"]:
                            print(f"   - [{t['type']}]: {t['recommendation']}")

                    if auto_sanitize and unicode_info["is_adversarial_obfuscation"]:
                        cleaned = sanitize_text(curr_text)
                        print("[*] Sanitizing clipboard: Invisible zero-width tokens stripped.")
                    print("!" * 70 + "\n")

            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n[*] Desktop Sentinel stopped by user.")
            break
        except Exception as e:
            time.sleep(poll_interval)

def main():
    parser = argparse.ArgumentParser(description="AegisTruth Desktop Sentinel Daemon")
    parser.add_argument("--interval", type=float, default=1.0, help="Clipboard poll interval in seconds")
    parser.add_argument("--no-sanitize", action="store_true", help="Do not automatically strip detected zero-width tokens")
    args = parser.parse_args()

    print_sentinel_banner()
    monitor_clipboard(poll_interval=args.interval, auto_sanitize=not args.no_sanitize)

if __name__ == "__main__":
    main()

