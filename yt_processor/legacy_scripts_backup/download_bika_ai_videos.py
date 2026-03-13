import subprocess
import pathlib
import json

OUTPUT_DIR = pathlib.Path(r"c:/Users/aweis/Downloads/YouTube_Tools_Scripts/Videos/bika_ai")
CHANNEL_URL = "https://www.youtube.com/@bika_ai/videos"

def download_all_videos():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", str(OUTPUT_DIR / "%(title)s.%(ext)s"),
        "--write-info-json",
        "--no-write-subs",
        "--no-write-auto-subs",
        "--no-playlist",
        CHANNEL_URL
    ]
    
    print(f"Downloading videos from {CHANNEL_URL}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print("Download complete!")
        print(result.stdout)

if __name__ == "__main__":
    download_all_videos()
