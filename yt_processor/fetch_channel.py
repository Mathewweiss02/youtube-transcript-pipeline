import yt_utils
import os
import sys

# Helper script to fetch all video titles + URLs for a channel and write
# them to a local text file. This uses the same yt_utils helpers as the
# web app but runs standalone.

# Make sure yt-dlp from this Python installation can be found, even if
# its Scripts directory is not on PATH.
scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
candidate = os.path.join(scripts_dir, "yt-dlp.exe")
if os.path.exists(candidate):
    yt_utils.YT_DLP_PATH = candidate

print(f"Using yt-dlp command: {yt_utils.YT_DLP_PATH}")

channel_url = "https://www.youtube.com/@saamirir"
videos = yt_utils.get_video_metadata(channel_url)

print(f"Found {len(videos)} videos")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(BASE_DIR, "saamirir_video_list.txt")

written = 0
with open(output_path, "w", encoding="utf-8") as f:
    for v in videos:
        vid = v.get("id")
        title = (v.get("title") or vid or "video").replace("\n", " ")
        if not vid:
            continue
        url = f"https://www.youtube.com/watch?v={vid}"
        f.write(f"{title}\t{url}\n")
        written += 1

print(f"Wrote {written} entries to {output_path}")
