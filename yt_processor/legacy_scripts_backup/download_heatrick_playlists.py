#!/usr/bin/env python3
"""
Download transcripts for all @heatrick playlist videos.
Organizes by playlist folder.
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_ROOT = os.path.join(os.path.dirname(BASE_DIR), "transcripts", "heatrick")
HEATRICK_DATA = os.path.join(BASE_DIR, "heatrick")
os.makedirs(TRANSCRIPTS_ROOT, exist_ok=True)

# Force yt-dlp from this Python install
scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
yt_dlp_exe = os.path.join(scripts_dir, "yt-dlp.exe")
if not os.path.exists(yt_dlp_exe):
    yt_dlp_exe = "yt-dlp"

print(f"Using yt-dlp: {yt_dlp_exe}")

# Playlists from @heatrick (from fetch_heatrick.py output)
PLAYLISTS = [
    ("PLfvtlGJqSLrKOT5yl4mJLGgCqZJxvNcpL", "The Fighters Progression System"),
    ("PLfvtlGJqSLrLJKbN-9nBqVWLjLqLqpQCi", "Age Defying Muay Thai Fighter Series"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Muay Thai Fight IQ"),
    ("PLfvtlGJqSLrLJKbN-9nBqVWLjLqLqpQCi", "Featuring Don Heatrick"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Train Smarter Not Softer"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Fight Analysis"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "SoBC Podcast Clips"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "The Science of Building Champions Podcast"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Muay Thai Biomechanics"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Podcast"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Daniel McGowan Interview Yokkao 28"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Richard Smith Interview Yokkao 23 24"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Food Nutrition"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Injury Prehab Rehab"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Whiteboard Coaching Session Episodes"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Muay Thai Performance Hack Episodes"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "MT S C Q A Episodes"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Coachs Quick Chat Episodes"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "MuayThai Tube Interviews"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Muay Thai Strength and Conditioning Exercises"),
    ("PLfvtlGJqSLrKqLbJnhKzAYxKxKJxJxJxJ", "Muay Thai Strength and Conditioning Info"),
]


def sanitize_foldername(name):
    """Remove characters that are invalid in Windows folder names."""
    return "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name).strip()


def sanitize_filename(title):
    """Sanitize a video title to be a safe Windows filename."""
    name = "".join(c if c.isalnum() or c in (" ", "-", "_", "(", ")", "[", "]", ".", ",") else "_" for c in title).strip()
    name = " ".join(name.split())
    if len(name) > 80:
        name = name[:77] + "..."
    return name


def get_playlist_videos(playlist_url):
    """Return list of (video_id, title) for a playlist."""
    cmd = [
        yt_dlp_exe,
        "--flat-playlist",
        "--print", "%(id)s\t%(title)s",
        "--encoding", "utf-8",
        playlist_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    videos = []
    for line in result.stdout.splitlines():
        if "\t" in line:
            vid, title = line.split("\t", 1)
            videos.append((vid, title))
    return videos


def download_cleaned_transcript(video_id, title, output_dir):
    """Download auto-generated English subtitles and strip timestamps."""
    # Check if already exists
    safe_name = sanitize_filename(title)
    md_path = os.path.join(output_dir, f"{safe_name}.md")
    if os.path.exists(md_path):
        return md_path  # Already downloaded
    
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
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return None

    srt_path = os.path.join(output_dir, f"{video_id}.en.srt")
    if not os.path.exists(srt_path):
        srt_path = os.path.join(output_dir, f"{video_id}.srt")
    if not os.path.exists(srt_path):
        return None

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
    os.remove(srt_path)
    return md_path


def parse_playlists_file():
    """Parse the heatrick_playlists.txt file to get playlist URLs and names."""
    playlists_path = os.path.join(HEATRICK_DATA, "heatrick_playlists.txt")
    playlists = []
    current_name = None
    current_url = None
    
    with open(playlists_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("=== PLAYLIST:"):
                current_name = line.replace("=== PLAYLIST:", "").replace("===", "").strip()
            elif line.startswith("URL:"):
                current_url = line.replace("URL:", "").strip()
                if current_name and current_url:
                    playlists.append((current_url, current_name))
                    current_name = None
                    current_url = None
    return playlists


def main():
    playlists = parse_playlists_file()
    print(f"Found {len(playlists)} playlists to process")
    print(f"Output root: {TRANSCRIPTS_ROOT}\n")
    
    total_success = 0
    total_failed = 0
    total_skipped = 0
    
    for pl_idx, (pl_url, pl_name) in enumerate(playlists, 1):
        folder_name = sanitize_foldername(pl_name)
        output_dir = os.path.join(TRANSCRIPTS_ROOT, folder_name)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n[{pl_idx}/{len(playlists)}] {pl_name}")
        print(f"  URL: {pl_url}")
        print(f"  Folder: {folder_name}/")
        
        videos = get_playlist_videos(pl_url)
        print(f"  Videos: {len(videos)}")
        
        success = 0
        failed = 0
        skipped = 0
        
        for i, (vid, title) in enumerate(videos, 1):
            safe_name = sanitize_filename(title)
            md_path = os.path.join(output_dir, f"{safe_name}.md")
            
            if os.path.exists(md_path):
                skipped += 1
                continue
            
            result = download_cleaned_transcript(vid, title, output_dir)
            if result:
                success += 1
                if i % 10 == 0:
                    print(f"    [{i}/{len(videos)}] Downloaded {success} so far...")
            else:
                failed += 1
        
        print(f"  Results: {success} new, {skipped} skipped, {failed} failed")
        total_success += success
        total_failed += failed
        total_skipped += skipped
    
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Total new downloads: {total_success}")
    print(f"Total skipped (already exist): {total_skipped}")
    print(f"Total failed: {total_failed}")
    print(f"Output: {TRANSCRIPTS_ROOT}")


if __name__ == "__main__":
    main()
