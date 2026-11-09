"""AegisTruth Video Walkthrough Renderer.

Combines 1080p captured frames, synthesized voiceover tracks,
and synchronized burned-in subtitles into a broadcast-ready demo MP4.
"""

import glob
import os
import shutil
import subprocess
from pathlib import Path
import imageio_ffmpeg


def format_srt_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def get_audio_duration(ffmpeg_exe, audio_path):
    cmd = [ffmpeg_exe, "-i", audio_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            dur_str = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = dur_str.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 10.0


def main():
    root_dir = Path(__file__).parent.parent
    scripts_dir = root_dir / "scripts"
    frames_dir = scripts_dir / "frames"
    audio_dir = scripts_dir / "audio"
    output_dir = scripts_dir / "video_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    scene_data = [
        {
            "id": 1,
            "title": "AegisTruth Sentinel: Overview & Telemetry Radar",
            "subtitle": "Welcome to AegisTruth Sentinel: Multi-Modal AI Forensics & Cognitive Defense Suite."
        },
        {
            "id": 2,
            "title": "Visual Forensics Studio: ELA Heatmaps & 2D Fourier (FFT)",
            "subtitle": "Visual Forensics Studio: Error Level Analysis (ELA), 2D Fourier Harmonics & CMOS Sensor Noise."
        },
        {
            "id": 3,
            "title": "Temporal Video Sentinel: Boundary Warp & Edge Flicker",
            "subtitle": "Temporal Video Sentinel: Inter-Frame Motion Continuity & Boundary Warp Detection (Sora, Kling, FaceSwap)."
        },
        {
            "id": 4,
            "title": "Acoustic Voice Clone Lab: Mel-Spectrogram & Pitch Jitter",
            "subtitle": "Acoustic Voice Clone Lab: Mel-Spectrogram & Pitch Jitter Analysis Exposing ElevenLabs & TTS Clones."
        },
        {
            "id": 5,
            "title": "Cognitive Text & Fact Sentinel: Entropy & Contradictions",
            "subtitle": "Cognitive Text & Fact Sentinel: Perplexity, Shannon Entropy & Cross-Sentence Contradiction Detection."
        },
        {
            "id": 6,
            "title": "AI Agent Zero-Trust Guard: Jailbreak & Tool Firewall",
            "subtitle": "AI Agent Zero-Trust Guard: Real-Time Jailbreak Quarantine & Destructive Tool Execution Firewall."
        },
        {
            "id": 7,
            "title": "C2PA Provenance Manifests & Legal Proof Certificates",
            "subtitle": "C2PA Cryptographic Provenance: Tamper-Evident SHA-256 Manifests & Exportable Court Proof Certificates."
        },
        {
            "id": 8,
            "title": "100% Privacy & Zero Data Leakage: Live at aryan9891.github.io/AegisTruth",
            "subtitle": "100% Privacy & Zero Data Leakage: Operates Offline & In-Browser. Live at aryan9891.github.io/AegisTruth."
        }
    ]

    print("[*] Calculating exact audio durations and generating SRT subtitle file...")
    timeline = []
    current_time = 0.0

    srt_entries = []

    for item in scene_data:
        idx = item["id"]
        audio_file = audio_dir / f"scene_{idx}.wav"
        frame_file = frames_dir / f"scene_{idx}.png"

        dur = get_audio_duration(ffmpeg_exe, str(audio_file))
        start_t = current_time
        end_t = current_time + dur
        current_time = end_t

        timeline.append({
            "idx": idx,
            "audio": audio_file,
            "frame": frame_file,
            "duration": dur,
            "start": start_t,
            "end": end_t,
            "subtitle": item["subtitle"]
        })

        srt_entry = f"{idx}\n{format_srt_time(start_t)} --> {format_srt_time(end_t)}\n{item['subtitle']}\n"
        srt_entries.append(srt_entry)

    srt_path = output_dir / "demo_subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))
    print(f"  [✔] Subtitle file generated: {srt_path} (Total duration: {round(current_time, 2)}s)")

    print("\n[*] Rendering individual scene video clips...")
    clip_files = []
    for item in timeline:
        idx = item["idx"]
        clip_path = output_dir / f"clip_{idx}.mp4"
        cmd = [
            ffmpeg_exe, "-y",
            "-loop", "1",
            "-i", str(item["frame"]),
            "-i", str(item["audio"]),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(item["duration"]),
            str(clip_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clip_files.append(clip_path)
        print(f"  [✔] Rendered Scene {idx} ({round(item['duration'], 2)}s)")

    print("\n[*] Concatenating scene clips into unified video...")
    concat_list_path = output_dir / "concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for c in clip_files:
            # Escape path for ffmpeg concat
            escaped = str(c).replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    unsubbed_video = output_dir / "aegistruth_demo_unsubbed.mp4"
    cmd_concat = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(unsubbed_video)
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("  [✔] Unification complete.")

    print("\n[*] Burning in high-clarity subtitles and rendering final master video...")
    final_video = root_dir / "aegistruth_demo_walkthrough.mp4"
    
    # Subtitle style: Clear modern typography, centered with translucent dark background box
    # On Windows, path to srt must have escaped backslashes or forward slashes
    escaped_srt = str(srt_path).replace("\\", "/").replace(":", "\\:")

    sub_filter = f"subtitles='{escaped_srt}':force_style='FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H99000000,BorderStyle=4,Outline=1,Shadow=1,Alignment=2,MarginV=30'"

    cmd_burn = [
        ffmpeg_exe, "-y",
        "-i", str(unsubbed_video),
        "-vf", sub_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "copy",
        str(final_video)
    ]
    subprocess.run(cmd_burn, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    file_size_mb = os.path.getsize(final_video) / (1024 * 1024)
    print(f"\n[✔ MASTER DEMO VIDEO RENDERED SUCCESSFULLY]")
    print(f"  Path: {final_video}")
    print(f"  Duration: {round(current_time, 2)} seconds")
    print(f"  Size: {file_size_mb:.2f} MB")

    # Copy video to static downloads for GitHub Pages and web application access
    downloads_dir = root_dir / "aegistruth" / "static" / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    target_dl = downloads_dir / "aegistruth_demo_walkthrough.mp4"
    shutil.copyfile(final_video, target_dl)
    print(f"  [✔] Copied to web downloads: {target_dl}")

    static_dir = root_dir / "aegistruth" / "static"
    shutil.copyfile(final_video, static_dir / "aegistruth_demo_walkthrough.mp4")


if __name__ == "__main__":
    main()
