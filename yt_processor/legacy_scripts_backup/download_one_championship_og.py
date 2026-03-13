import os
import subprocess
import sys
import json
from pathlib import Path

# Load ONE Championship catalog
catalog_file = Path('one_championship_search_results/final_instructional_catalog_20260108_022119.json')

with open(catalog_file, 'r', encoding='utf-8') as f:
    videos = json.load(f)

print(f"Loaded {len(videos)} videos from catalog")
print()

# Output directory
OUTPUT_DIR = Path('one_championship_transcripts')
OUTPUT_DIR.mkdir(exist_ok=True)

# Force yt-dlp from this Python install
scripts_dir = Path(sys.executable).parent / 'Scripts'
yt_dlp_exe = scripts_dir / 'yt-dlp.exe'
if not yt_dlp_exe.exists():
    yt_dlp_exe = "yt-dlp"

print(f"Using yt-dlp: {yt_dlp_exe}")
print(f"Output directory: {OUTPUT_DIR}")
print()
print("Starting download (no rate limiting between videos)...")
print()

def download_cleaned_transcript(video):
    """Download auto-generated English subtitles and strip timestamps."""
    video_id = video['video_id']
    title = video['title']
    
    # 1) Download .srt to temp location
    temp_template = OUTPUT_DIR / f"{video_id}.%(ext)s"
    cmd = [
        str(yt_dlp_exe),
        "--write-auto-sub",
        "--sub-langs", "en",
        "--skip-download",
        "--convert-subs", "srt",
        "-o", str(temp_template),
        video['url']
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  - FAILED {video_id}: {e.stderr.strip()}")
        return None

    # 2) Find the .en.srt file
    srt_path = OUTPUT_DIR / f"{video_id}.en.srt"
    if not srt_path.exists():
        srt_path = OUTPUT_DIR / f"{video_id}.srt"
    
    if not srt_path.exists():
        print(f"  - NO SUBS {video_id}")
        return None

    # 3) Clean timestamps and write .md file
    md_path = OUTPUT_DIR / f"{video_id}.md"
    with open(srt_path, 'r', encoding='utf-8') as f_in, open(md_path, 'w', encoding='utf-8') as f_out:
        seen = set()
        f_out.write(f"# {title}\n\n")
        f_out.write(f"URL: {video['url']}\n")
        f_out.write(f"Fighter: {video.get('fighter', 'Unknown')}\n")
        f_out.write(f"Categories: {', '.join(video.get('categories', []))}\n")
        f_out.write(f"Score: {video.get('final_score', 'N/A')}\n\n")
        f_out.write("---\n\n")
        
        for line in f_in:
            line = line.strip()
            if not line: continue
            if line.isdigit(): continue
            if "-->" in line: continue
            if line in seen: continue
            seen.add(line)
            f_out.write(line + "\n")
    
    # Clean up the .srt file
    srt_path.unlink()
    return md_path

# Main loop
successful = []
failed = []

for i, video in enumerate(videos, 1):
    video_id = video['video_id']
    title = video['title'][:60] + '...' if len(video['title']) > 60 else video['title']
    
    print(f"[{i}/{len(videos)}] {title}")
    
    md_path = download_cleaned_transcript(video)
    if md_path:
        print(f"  -> {md_path.name}")
        successful.append(video)
    else:
        failed.append(video)
    
    # No sleep between downloads - let it rip!

print()
print("=" * 80)
print("DONE!")
print("=" * 80)
print()
print(f"✓ Successfully downloaded: {len(successful)} videos")
print(f"✗ Failed: {len(failed)} videos")
print()
print(f"Transcripts saved to: {OUTPUT_DIR}")
