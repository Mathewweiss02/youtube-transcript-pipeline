#!/usr/bin/env python3
"""Format video list from separate lines to tab-separated format"""

with open('hyperarch_videos.txt', 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

with open('hyperarch_formatted.txt', 'w', encoding='utf-8') as f:
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            title = lines[i]
            video_id = lines[i + 1]
            url = f"https://www.youtube.com/watch?v={video_id}"
            f.write(f"{title}\t{url}\n")

print(f"Formatted {len(lines)//2} videos")
