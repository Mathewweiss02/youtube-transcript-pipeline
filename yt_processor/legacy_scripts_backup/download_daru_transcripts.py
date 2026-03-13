#!/usr/bin/env python3
"""
Download transcripts for all @DaruStrongPerformance videos.
Saves as cleaned markdown with video URLs, no timestamps.
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_ROOT = os.path.join(os.path.dirname(BASE_DIR), "transcripts", "daru")
DARU_DATA = os.path.join(BASE_DIR, "daru")
os.makedirs(TRANSCRIPTS_ROOT, exist_ok=True)

# Force yt-dlp from this Python install
scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
yt_dlp_exe = os.path.join(scripts_dir, "yt-dlp.exe")
if not os.path.exists(yt_dlp_exe):
    yt_dlp_exe = "yt-dlp"

print(f"Using yt-dlp: {yt_dlp_exe}")
print(f"Output: {TRANSCRIPTS_ROOT}\n")

def sanitize_filename(title):
    """Sanitize a video title to be a safe Windows filename."""
    name = "".join(c if c.isalnum() or c in (" ", "-", "_", "(", ")", "[", "]", ".", ",") else "_" for c in title).strip()
    name = " ".join(name.split())
    if len(name) > 100:
        name = name[:97] + "..."
    return name

def download_cleaned_transcript(video_id, title):
    """Download auto-generated English subtitles and strip timestamps."""
    output_dir = TRANSCRIPTS_ROOT
    
    # Check if already exists
    safe_name = sanitize_filename(title)
    md_path = os.path.join(output_dir, f"{safe_name}.md")
    if os.path.exists(md_path):
        return md_path, "SKIP"
    
    temp_template = os.path.join(output_dir, f"{video_id}.%(ext)s")
    cmd = [
        yt_dlp_exe,
        "--write-auto-sub",
        "--sub-langs", "en",
        "--skip-download",
        "--convert-subs", "srt",
        "-o", temp_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    except subprocess.CalledProcessError:
        return None, "FAIL"

    srt_path = os.path.join(output_dir, f"{video_id}.en.srt")
    if not os.path.exists(srt_path):
        srt_path = os.path.join(output_dir, f"{video_id}.srt")
    if not os.path.exists(srt_path):
        return None, "NOSUB"

    # Clean and save as markdown
    with open(srt_path, "r", encoding="utf-8", errors='replace') as f_in, open(md_path, "w", encoding="utf-8") as f_out:
        seen = set()
        f_out.write(f"# {title}\n\n")
        f_out.write(f"https://www.youtube.com/watch?v={video_id}\n\n")
        for line in f_in:
            line = line.strip()
            if not line: continue
            if line.isdigit(): continue
            if "-->" in line: continue
            if line in seen: continue
            seen.add(line)
            f_out.write(line + "\n")
    
    try:
        os.remove(srt_path)
    except:
        pass
    
    return md_path, "OK"

def main():
    # Read video list
    video_list_path = os.path.join(DARU_DATA, "daru_all_videos.txt")
    videos = []
    with open(video_list_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                title, url = parts
                # Extract video ID from URL
                if 'watch?v=' in url:
                    vid = url.split('watch?v=')[1].split('&')[0]
                    videos.append((vid, title))
    
    print(f"Processing {len(videos)} videos...\n")
    
    success = 0
    failed = 0
    skipped = 0
    nosub = 0
    
    for i, (vid, title) in enumerate(videos, 1):
        result, status = download_cleaned_transcript(vid, title)
        
        if status == "OK":
            success += 1
            if i % 50 == 0:
                print(f"[{i}/{len(videos)}] Downloaded {success} so far...")
        elif status == "SKIP":
            skipped += 1
        elif status == "NOSUB":
            nosub += 1
        else:
            failed += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Success: {success}")
    print(f"Skipped (already exist): {skipped}")
    print(f"No subtitles: {nosub}")
    print(f"Failed: {failed}")
    print(f"Output: {TRANSCRIPTS_ROOT}")

if __name__ == "__main__":
    main()
