import os
import subprocess
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_ROOT = os.path.join(os.path.dirname(BASE_DIR), "transcripts")
CHANNEL_DIR = os.path.join(TRANSCRIPTS_ROOT, "MuayThaiPros")
os.makedirs(CHANNEL_DIR, exist_ok=True)

# Force yt-dlp from this Python install
scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
yt_dlp_exe = os.path.join(scripts_dir, "yt-dlp.exe")
if not os.path.exists(yt_dlp_exe):
    yt_dlp_exe = "yt-dlp"

print(f"Using yt-dlp: {yt_dlp_exe}")

# Playlists from @Muaythaipros
playlists = [
    ("Muay Thai Academy: Clinching", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R0zpW_1CrljYJ3BspnvVskW"),
    ("Muay Thai Kicking Tutorials", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R1JVF_iZGzyo4r8t1w5956F"),
    ("Beginner Muay Thai Tips", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R0G7eNMq2PrF8xF5m7ulr27"),
    ("Muay Thai Highlights", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R2XyV9nqIDMEMepuD49uP4U"),
    ("Muay Thai Breakdowns", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R0NKS3zUgrwyJ6st6S1oMxT"),
    ("General Discussion", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R2JOzaW6IwQB05nP4EXjURa"),
    ("Muay Thai Teep", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R0pmOWm-M3kSK7qa1xwoIXC"),
    ("Shadow Boxing Tips", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R3ITGdecuDsXrTOjxeEbmbM"),
    ("Muay Thai Pad Holding Tips", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R2LKy6lguPRdvR1TeWLE3dp"),
    ("Muay Thai Combinations", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R0XQsJOhSqGADwMGOByXKOk"),
    ("Muay Thai Throws & Sweeps", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R0jqSaI3V5ILpg9f7W6Ax-o"),
    ("Muay Thai Heavy Bag Training", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R1ArWi9q3DtNiv0P-5OYgXI"),
    ("Muay Thai Strategy", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R21caWM9_uejJ6GeL-YD3jI"),
    ("Muay Thai Padwork", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R0SRJv0TrU2O4HKhImVFp5C"),
    ("Heavy Bag Training", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R2x411MetiCqq2RuriwfLvr"),
    ("Muay Thai Sparring", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R0K_dCrl-NstptrqGhRwgjs"),
    ("Muay Thai Fights", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R3JCrZZoVxB4hQfWs-PONe5"),
    ("Muay Thai Techniques", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R2A05z-MlK16knlOu_yMTv1"),
    ("Muay Thai Clinching", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R1GqlD94je7cUEsbGQL4Rou"),
    ("Muay Thai Tips", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R2A19oETIzIDoU5w5K8F_zC"),
    ("Muay Thai Basics", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R3rRn6Ar5wDUSf4-WAvaSIf"),
    ("Muay Thai Sparring Drills", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R1BJGpFcRgfUgVUef31GhyL"),
    ("Muay Thai Tutorials", "https://www.youtube.com/playlist?list=PLJ6iDGSc-0R3iJBNVdBCpfNKyHwY_acqK"),
]

def sanitize_foldername(name):
    """Remove characters that are invalid in Windows folder names."""
    return "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name).strip()

def sanitize_filename(title):
    """Sanitize a video title to be a safe Windows filename (without extension)."""
    # Remove/rename invalid characters for filenames
    name = "".join(c if c.isalnum() or c in (" ", "-", "_", "(", ")", "[", "]", ".", ",") else "_" for c in title).strip()
    # Replace multiple spaces with a single space
    name = " ".join(name.split())
    # Truncate very long names to avoid Windows path limits
    if len(name) > 80:
        name = name[:77] + "..."
    return name

def download_cleaned_transcript(video_id, title, output_dir):
    """Download auto-generated English subtitles and strip timestamps."""
    # 1) Download .srt to a temp location
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
        print(f"  - FAILED {video_id}: {e.stderr.strip()}")
        return None

    # 2) Find the .en.srt file
    srt_path = os.path.join(output_dir, f"{video_id}.en.srt")
    if not os.path.exists(srt_path):
        srt_path = os.path.join(output_dir, f"{video_id}.srt")
    if not os.path.exists(srt_path):
        print(f"  - NO SUBS {video_id}")
        return None

    # 3) Clean timestamps and write .md file
    safe_name = sanitize_filename(title)
    md_path = os.path.join(output_dir, f"{safe_name}.md")
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

def get_playlist_videos(playlist_url):
    """Return list of (video_id, title) for a playlist."""
    cmd = [
        yt_dlp_exe,
        "--flat-playlist",
        "--print",
        "%(id)s\t%(title)s",
        "--encoding", "utf-8",
        playlist_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    videos = []
    for line in result.stdout.splitlines():
        if "\t" in line:
            vid, title = line.split("\t", 1)
            videos.append((vid, title))
    return videos

# Main loop
for idx, (playlist_name, playlist_url) in enumerate(playlists, 1):
    folder_name = sanitize_foldername(playlist_name)
    playlist_dir = os.path.join(CHANNEL_DIR, folder_name)
    os.makedirs(playlist_dir, exist_ok=True)
    print(f"\n[{idx}/{len(playlists)}] Playlist: {playlist_name}")
    print(f"  URL: {playlist_url}")
    print(f"  Folder: {playlist_dir}")

    videos = get_playlist_videos(playlist_url)
    print(f"  Found {len(videos)} videos")

    written = 0
    for i, (vid, title) in enumerate(videos, 1):
        print(f"    [{i}/{len(videos)}] {title[:60]}...")
        md_path = download_cleaned_transcript(vid, title, playlist_dir)
        if md_path:
            written += 1
            print(f"      -> {os.path.basename(md_path)}")
    print(f"  Wrote {written} transcript(s) to {playlist_dir}")

print("\nAll playlists processed.")
print(f"Channel transcripts are in: {CHANNEL_DIR}")
