import os
import subprocess
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_PATH = os.path.join(os.path.dirname(BASE_DIR), "saamirir_video_list.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "saamirir_transcripts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Force yt-dlp from this Python install
scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
yt_dlp_exe = os.path.join(scripts_dir, "yt-dlp.exe")
if not os.path.exists(yt_dlp_exe):
    yt_dlp_exe = "yt-dlp"

print(f"Using yt-dlp: {yt_dlp_exe}")

def download_cleaned_transcript(video_id, title):
    """Download auto-generated English subtitles and strip timestamps."""
    # 1) Download .srt to a temp location
    temp_template = os.path.join(OUTPUT_DIR, f"{video_id}.%(ext)s")
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
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  - FAILED {video_id}: {e.stderr.strip()}")
        return None

    # 2) Find the .en.srt file
    srt_path = os.path.join(OUTPUT_DIR, f"{video_id}.en.srt")
    if not os.path.exists(srt_path):
        srt_path = os.path.join(OUTPUT_DIR, f"{video_id}.srt")
    if not os.path.exists(srt_path):
        print(f"  - NO SUBS {video_id}")
        return None

    # 3) Clean timestamps and write .md file
    md_path = os.path.join(OUTPUT_DIR, f"{video_id}.md")
    with open(srt_path, "r", encoding="utf-8") as f_in, open(md_path, "w", encoding="utf-8") as f_out:
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
    # Clean up the .srt file
    os.remove(srt_path)
    return md_path

# Main loop
def read_lines_fallback(path):
    for enc in ("utf-8-sig", "utf-16"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("Failed to decode file as UTF-8 or UTF-16")

lines = read_lines_fallback(LIST_PATH)

print(f"Processing {len(lines)} videos from {LIST_PATH}")

for i, line in enumerate(lines, 1):
    if "\t" not in line:
        continue
    title, url = line.strip().split("\t", 1)
    video_id = url.split("v=")[-1].split("&")[0]
    print(f"[{i}/{len(lines)}] {title[:60]}...")
    md_path = download_cleaned_transcript(video_id, title)
    if md_path:
        print(f"  -> {md_path}")

print("Done.")
