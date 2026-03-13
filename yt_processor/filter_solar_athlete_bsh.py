#!/usr/bin/env python3
"""
Filter Solar_Athlete pending videos to only include BSH and StrongHER episodes.
"""
import json
import re

def filter_solar_athlete_episodes():
    with open('pending_updates.json', 'r', encoding='utf-8') as f:
        pending = json.load(f)
    
    if 'Solar_Athlete' not in pending['channels']:
        print("No Solar_Athlete in pending updates")
        return
    
    all_videos = pending['channels']['Solar_Athlete']['new_videos']
    
    # Pattern: "BSH Ep X" or "StrongHER Ep X"
    pattern = r'^(BSH|StrongHER)\s+Ep\.?\s+\d+'
    
    filtered = []
    skipped = []
    
    for video in all_videos:
        title = video['title']
        if re.match(pattern, title):
            filtered.append(video)
        else:
            skipped.append(title)
    
    print(f"\nSolar_Athlete Filter Results:")
    print(f"  Total pending: {len(all_videos)}")
    print(f"  BSH/StrongHER episodes: {len(filtered)}")
    print(f"  Skipped (non-series): {len(skipped)}")
    
    if filtered:
        print(f"\nEpisodes to download:")
        for v in filtered[:10]:
            print(f"  - {v['title']}")
        if len(filtered) > 10:
            print(f"  ... and {len(filtered) - 10} more")
    
    # Save filtered list
    with open('solar_athlete_bsh_episodes.txt', 'w', encoding='utf-8') as f:
        for video in filtered:
            f.write(f"{video['url']}\n")
    
    print(f"\nFiltered list saved to: solar_athlete_bsh_episodes.txt")
    return filtered

if __name__ == '__main__':
    filter_solar_athlete_episodes()
