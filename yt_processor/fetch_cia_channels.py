#!/usr/bin/env python3
"""
Fetch CIA Podcast Channels - Danny Jones & Julian Dorey
Uses yt_utils to get all videos and filter for CIA/intelligence content
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yt_utils
import re

# Ensure yt-dlp is found
scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
candidate = os.path.join(scripts_dir, "yt-dlp.exe")
if os.path.exists(candidate):
    yt_utils.YT_DLP_PATH = candidate

print(f"Using yt-dlp: {yt_utils.YT_DLP_PATH}\n")

# CIA-related keywords to search for
CIA_KEYWORDS = [
    'cia', 'spy', 'intelligence', 'fbi', 'agent', 'operative',
    'bustamante', 'kiriakou', 'baer', 'mendez', 'soufan',
    'mossad', 'epstein', 'whistleblower', 'covert', 'terrorism',
    'interrogation', 'disguise', 'cold war', 'kgb'
]

def fetch_channel(channel_url, output_filename, channel_name):
    """Fetch all videos from a channel and save to file"""
    print(f"\n{'='*60}")
    print(f"Fetching: {channel_name}")
    print(f"URL: {channel_url}")
    print(f"{'='*60}\n")
    
    videos = yt_utils.get_video_metadata(channel_url)
    print(f"Found {len(videos)} total videos\n")
    
    if not videos:
        print(f"⚠ No videos found for {channel_name}")
        return []
    
    # Save all videos
    output_path = os.path.join(os.path.dirname(__file__), output_filename)
    written = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for v in videos:
            vid = v.get('id')
            title = (v.get('title') or vid or 'video').replace('\n', ' ')
            if not vid:
                continue
            url = f'https://www.youtube.com/watch?v={vid}'
            f.write(f'{title}\t{url}\n')
            written += 1
    
    print(f"✓ Wrote {written} videos to {output_path}\n")
    return videos

def filter_cia_videos(all_videos, output_filename):
    """Filter videos for CIA/intelligence related content"""
    print(f"\n{'='*60}")
    print("Filtering for CIA/Intelligence Content")
    print(f"{'='*60}\n")
    
    cia_videos = []
    for v in all_videos:
        title = (v.get('title') or '').lower()
        if any(keyword in title for keyword in CIA_KEYWORDS):
            cia_videos.append(v)
            print(f"✓ MATCH: {v.get('title', '')[:70]}")
    
    print(f"\nFound {len(cia_videos)} CIA-related videos\n")
    
    # Save filtered list
    output_path = os.path.join(os.path.dirname(__file__), output_filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        for v in cia_videos:
            vid = v.get('id')
            title = (v.get('title') or vid or 'video').replace('\n', ' ')
            url = f'https://www.youtube.com/watch?v={vid}'
            f.write(f'{title}\t{url}\n')
    
    print(f"✓ Saved CIA videos to {output_path}\n")
    return cia_videos

def main():
    all_cia_videos = []
    
    # Fetch Danny Jones
    danny_videos = fetch_channel(
        'https://www.youtube.com/@Koncrete',
        'danny_jones_all.txt',
        'Danny Jones Podcast (@Koncrete)'
    )
    
    if danny_videos:
        danny_cia = filter_cia_videos(danny_videos, 'danny_jones_cia_filtered.txt')
        all_cia_videos.extend(danny_cia)
    
    # Fetch Julian Dorey
    julian_videos = fetch_channel(
        'https://www.youtube.com/@JulianDorey',
        'julian_dorey_all.txt',
        'Julian Dorey Podcast'
    )
    
    if julian_videos:
        julian_cia = filter_cia_videos(julian_videos, 'julian_dorey_cia_filtered.txt')
        all_cia_videos.extend(julian_cia)
    
    # Create combined CIA video list
    print(f"\n{'='*60}")
    print("Creating Combined CIA Video List")
    print(f"{'='*60}\n")
    
    # Also add known verified CIA videos from other channels
    additional_videos = [
        ("Andrew Bustamante: CIA Spy | Lex Fridman Podcast #310", "T3FC7qIAGZk"),
        ("Andrew Bustamante (Ex-CIA Spy) Reveals All | Diary of a CEO #192", "-RoC949yrjU"),
        ("CIA Spy: 'Leave The USA Before 2030!' | Diary of a CEO", "Gv-YWfNWwkM"),
        ("Joe Rogan Experience #2392 - John Kiriakou", "TZqADzuu73g"),
        ("Former CIA Agent On Where The World Is Heading | Robert Baer", "6_QzcDgL5dI"),
        ("Ex-CIA Agent Bob Baer Unveils CIA Secrets", "G2_6ZWXXFr4"),
        ("Conversations With History: Robert Baer | UC Berkeley", "paS1-ee-5cU"),
        ("Jonna Mendez, CIA Chief of Disguise | In True Face", "1HZIe9-BrHU"),
        ("Former CIA Chief of Disguise Answers Spy Questions | WIRED", "XDBWjfUgaR8"),
        ("The Interrogator | FRONTLINE with Ali Soufan", "n1ivoWW1-4U"),
    ]
    
    output_path = os.path.join(os.path.dirname(__file__), 'cia_intelligence_video_list.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write Danny Jones CIA videos
        for v in all_cia_videos:
            vid = v.get('id')
            title = (v.get('title') or vid or 'video').replace('\n', ' ')
            url = f'https://www.youtube.com/watch?v={vid}'
            f.write(f'{title}\t{url}\n')
        
        # Write additional verified videos
        for title, vid in additional_videos:
            url = f'https://www.youtube.com/watch?v={vid}'
            f.write(f'{title}\t{url}\n')
    
    total_count = len(all_cia_videos) + len(additional_videos)
    print(f"✓ Created combined list: {output_path}")
    print(f"  Total videos: {total_count}")
    print(f"  - From Danny Jones/Julian Dorey: {len(all_cia_videos)}")
    print(f"  - Additional verified sources: {len(additional_videos)}\n")
    
    # Copy to CIA project folder
    cia_path = r'C:\Users\aweis\Downloads\CIA\video_list.txt'
    with open(output_path, 'r', encoding='utf-8') as f_src:
        content = f_src.read()
    with open(cia_path, 'w', encoding='utf-8') as f_dst:
        f_dst.write(content)
    print(f"✓ Copied to CIA project: {cia_path}\n")

if __name__ == "__main__":
    main()
