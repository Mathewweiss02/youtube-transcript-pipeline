import subprocess
import json
import os
import re
import zipfile
import time
from typing import Dict, List, Optional


def _find_yt_dlp() -> str:
    """Best-effort detection of the yt-dlp executable.

    Preference order:
    1. Any yt-dlp*.exe under C:/yt-dlp
    2. A user-provided YT_DLP_PATH env var
    3. Plain 'yt-dlp' (resolved via PATH)
    """

    # 1) Look for a local Windows binary in the classic folder
    base_dir = "C:/yt-dlp"
    try:
        if os.path.isdir(base_dir):
            for name in os.listdir(base_dir):
                lower = name.lower()
                if lower.startswith("yt-dlp") and lower.endswith(".exe"):
                    return os.path.join(base_dir, name)
    except OSError:
        pass

    # 2) Environment override
    env_path = os.environ.get("YT_DLP_PATH")
    if env_path:
        return env_path

    # 3) Fall back to relying on PATH
    return "yt-dlp"


YT_DLP_PATH = _find_yt_dlp()
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(_BASE_DIR, "downloads")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def get_video_info(url: str) -> Dict:
    """
    Fetch metadata for a single video or playlist using yt-dlp.
    Returns a dictionary of metadata.
    """
    cmd = [
        YT_DLP_PATH,
        "--flat-playlist",  # Don't list all videos details if it's a playlist, just basic info first
        "--dump-single-json",
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching info: {e.stderr}")
        return {}

def get_playlist_videos(url: str) -> List[Dict]:
    """
    Fetch all video items from a playlist/channel.
    """
    cmd = [
        YT_DLP_PATH,
        "--flat-playlist",
        "--dump-single-json",
        url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', check=True)
        data = json.loads(result.stdout)
        if 'entries' in data:
            return data['entries']
        return []
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []

def download_transcript(video_id: str) -> str:
    """
    Download auto-subs for a video and convert to txt.
    Returns the path to the cleaned text file.
    """
    # 1. Download vtt -> srt
    output_template = os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s")
    cmd = [
        YT_DLP_PATH,
        "--write-auto-sub",
        "--sub-langs",
        "en",
        "--skip-download",
        "--convert-subs",
        "srt",
        "-o",
        output_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        # Log and signal failure to caller; batch creator will skip this entry.
        print(f"[download_transcript] yt-dlp failed for {video_id}: {e.stderr}")
        return ""
    
    # 2. Find the .en.srt file
    srt_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.en.srt")
    if not os.path.exists(srt_path):
        # Fallback if it didn't download .en.srt (maybe only .srt)
        srt_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.srt")
    
    if not os.path.exists(srt_path):
        return ""

    # 3. Clean timestamps (simplified version of strip_srt_timestamps.py logic)
    txt_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.txt")
    with open(srt_path, 'r', encoding='utf-8') as f_in, open(txt_path, 'w', encoding='utf-8') as f_out:
        seen = set()
        for line in f_in:
            line = line.strip()
            if not line: continue
            if line.isdigit(): continue
            if '-->' in line: continue
            if line in seen: continue
            seen.add(line)
            f_out.write(line + "\n")
            
    return txt_path

def download_media(video_id: str, format_type: str = 'mp3') -> str:
    """
    Download audio (mp3) or video (mp4).
    Returns the path to the file.
    """
    output_template = os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s")
    cmd = [YT_DLP_PATH, "-o", output_template]
    
    if format_type == 'mp3':
        cmd.extend(["-x", "--audio-format", "mp3"])
    else:
        cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"])
        
    cmd.append(f"https://www.youtube.com/watch?v={video_id}")
    
    subprocess.run(cmd, check=True)
    
    # Predict filename
    expected_ext = "mp3" if format_type == 'mp3' else "mp4"
    return os.path.join(DOWNLOAD_DIR, f"{video_id}.{expected_ext}")


def download_srt(video_id: str) -> str:
    """Download auto-generated English subtitles as .srt and return the file path.

    This is used when the user wants transcripts *with* timestamps intact.
    """
    output_template = os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s")
    cmd = [
        YT_DLP_PATH,
        "--write-auto-sub",
        "--sub-langs",
        "en",
        "--skip-download",
        "--convert-subs",
        "srt",
        "-o",
        output_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[download_srt] yt-dlp failed for {video_id}: {e.stderr}")
        return ""

    srt_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.en.srt")
    if not os.path.exists(srt_path):
        srt_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.srt")
    return srt_path if os.path.exists(srt_path) else ""


def extract_urls(text: str) -> List[str]:
    """Extract YouTube/YouTu.be URLs from arbitrary text (multiline, markdown, etc.)."""
    if not text:
        return []
    # Basic regex for YouTube URLs; avoids trailing punctuation
    pattern = r"(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s<>'\"]+)"
    found = re.findall(pattern, text)
    cleaned: list[str] = []
    for url in found:
        cleaned.append(url.rstrip(".,);"))
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for u in cleaned:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def get_video_metadata(url: str) -> List[Dict]:
    """Return a flat list of video metadata dicts for a video, playlist, or channel URL.

    Special handling:
    - Bare channel / handle URLs like ``https://www.youtube.com/@Foo`` or
      ``https://www.youtube.com/channel/UC...`` are normalized to their
      ``/videos`` page to get the full uploads list.
    """

    url = url.strip()
    if not url:
        return []

    # Normalize channel root URLs to their "videos" tab so yt-dlp returns
    # the real uploads playlist instead of wrapper items like
    # "MyronGainesX - Videos".
    if re.match(r"^https?://(?:www\.)?youtube\.com/@[^/\s]+/?$", url):
        url = url.rstrip("/") + "/videos"
    elif re.match(r"^https?://(?:www\.)?youtube\.com/channel/[^/\s]+/?$", url):
        url = url.rstrip("/") + "/videos"

    info = get_video_info(url)
    if not info:
        return []

    # Some channel/handle URLs first resolve to another URL (e.g. the
    # channel's "Videos" playlist). In those cases yt-dlp may return a
    # lightweight URL wrapper object with ``_type == 'url'`` and a ``url``
    # field pointing at the real playlist. Follow that once so we can
    # flatten the actual playlist entries below.
    if info.get("_type") == "url" and info.get("url"):
        redirected = get_video_info(info["url"])
        if redirected:
            info = redirected

    # Playlist/channel: flatten entries
    if info.get("_type") == "playlist" or "entries" in info:
        entries = info.get("entries", []) or []
        videos: list[Dict] = []
        for entry in entries:
            # Some playlist entries are themselves URL wrappers pointing at
            # another playlist (e.g. "Videos", "Shorts" sections on a
            # channel). In that case, recursively expand that URL.
            if entry.get("_type") == "url" and entry.get("url"):
                nested = get_video_metadata(entry["url"])
                if nested:
                    videos.extend(nested)
                continue

            vid = entry.get("id")
            title = entry.get("title")
            if not vid or not title:
                continue
            videos.append(
                {
                    "id": vid,
                    "title": title,
                    "uploader": entry.get("uploader", "Unknown"),
                    "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                }
            )
        return videos

    # Single video case
    vid = info.get("id")
    title = info.get("title")
    if not vid or not title:
        return []
    return [
        {
            "id": vid,
            "title": title,
            "uploader": info.get("uploader", "Unknown"),
            "thumbnail": info.get("thumbnail", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"),
        }
    ]


def _slugify_filename(title: str, ext: str) -> str:
    """Turn a video title into a safe filename with the given extension."""
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", title).strip("_") or "video"
    return f"{base}.{ext}"


def create_zip_from_transcripts(
    videos: List[Dict],
    ext: str = "txt",
    clean_timestamps: bool = True,
    embed_url: bool = False,
) -> str:
    """Create a ZIP containing transcripts for the given videos.

    Each item in ``videos`` must have at least ``id`` and ``title`` keys.

    - If ``clean_timestamps`` is True, uses ``download_transcript`` (no timestamps).
    - If False, uses ``download_srt`` (keeps timestamps).

    ``ext`` controls the file extension inside the zip ("txt" or "md").
    If ``embed_url`` is True, a YouTube URL header is injected at the top of each file.
    """

    if not videos:
        raise ValueError("No videos provided for zipping transcripts")

    zip_name = f"transcripts_batch_{len(videos)}_{int(time.time())}.{ext}.zip"
    zip_path = os.path.join(DOWNLOAD_DIR, zip_name)

    wrote_any = False
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for v in videos:
            vid = v.get("id")
            title = v.get("title") or vid or "video"
            if not vid:
                continue

            if clean_timestamps:
                src_path = download_transcript(vid)
            else:
                src_path = download_srt(vid)

            if not src_path or not os.path.exists(src_path):
                continue

            with open(src_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Optional YouTube URL header
            if embed_url:
                url = f"https://www.youtube.com/watch?v={vid}"
                if ext == "md":
                    header = f"[YouTube link]({url})\n\n"
                else:
                    header = f"YouTube URL: {url}\n\n"
                content = header + content

            # For markdown, wrap with a simple H1 header
            if ext == "md":
                content = f"# {title}\n\n" + content

            arcname = _slugify_filename(title, ext)
            zf.writestr(arcname, content)
            wrote_any = True

    if not wrote_any:
        try:
            os.remove(zip_path)
        except OSError:
            pass
        return ""
    return zip_path
