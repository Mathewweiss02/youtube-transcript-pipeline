#!/usr/bin/env python3
"""
Jay Campbell Title Matcher

Matches transcript titles from your existing files against the 269 YouTube videos
to identify which videos have transcripts and which are missing.

Outputs:
    - jay_campbell_missing_detailed.json - Videos needing transcripts
    - jay_campbell_match_report.txt - Human-readable report
"""

import json
import re
from pathlib import Path
from typing import Any

# Paths
TRANSCRIPT_DIR = Path("../../transcripts/Jay_Campbell")
INVENTORY_PATH = Path("jay_campbell_full_inventory.json")
OUTPUT_JSON = Path("jay_campbell_missing_detailed.json")
OUTPUT_REPORT = Path("jay_campbell_match_report.txt")


def extract_titles_from_transcripts() -> list[str]:
    """Extract all episode titles from Jay Campbell transcript files."""
    titles = []
    
    if not TRANSCRIPT_DIR.exists():
        print(f"⚠️ Transcript directory not found: {TRANSCRIPT_DIR}")
        return titles
    
    md_files = list(TRANSCRIPT_DIR.glob("*.md"))
    print(f"📄 Found {len(md_files)} transcript files")
    
    for md_file in md_files:
        content = md_file.read_text(encoding='utf-8', errors='ignore')
        
        # Extract titles from Table of Contents section
        in_toc = False
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect start of TOC
            if line.lower().startswith('## table of contents'):
                in_toc = True
                continue
            
            # Detect end of TOC (next ## header or --- separator)
            if in_toc and (line.startswith('---') or (line.startswith('##') and 'table of contents' not in line.lower())):
                in_toc = False
                continue
            
            # Extract title from TOC bullet
            if in_toc and line.startswith('- '):
                # Remove bullet and .en suffix
                title = line[2:].strip()
                title = re.sub(r'\.en$', '', title, flags=re.IGNORECASE)
                if title and not title.lower().startswith('part ') and not title.lower().startswith('chunk '):
                    titles.append(title)
            
            # Also extract from ## headers (episode headers)
            if line.startswith('## ') and not line.startswith('## Table') and not line.startswith('## Part'):
                title = line[3:].strip()
                title = re.sub(r'\.en$', '', title, flags=re.IGNORECASE)
                if title and len(title) > 10:  # Filter out short lines
                    titles.append(title)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for t in titles:
        normalized = normalize_title(t)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(t)
    
    print(f"✅ Extracted {len(unique)} unique titles from transcripts")
    return unique


def normalize_title(title: str) -> str:
    """Normalize title for matching."""
    # Unicode replacements
    replacements = {
        '：': ':', '⧸': '/', '｜': '|', '＂': '"', '？': '?', '！': '!',
        '（': '(', '）': ')', '．': '.', '，': ',', '／': '/', '＆': '&',
        '＃': '#', '＠': '@', '％': '%', '－': '-', '［': '[', '］': ']',
        '｛': '{', '｝': '}', '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '“': '"', '”': '"', ''': "'", ''': "'",
    }
    
    title = title.strip().lower()
    for old, new in replacements.items():
        title = title.replace(old, new)
    
    # Strip episode numbers like "001 -", "204 -"
    title = re.sub(r'^\d+\s*-\s*', '', title)
    # Remove .en suffix
    title = re.sub(r'\.en$', '', title)
    # Remove podcast suffixes
    title = re.sub(r'\s*\|\s*the jay campbell podcast$', '', title)
    title = re.sub(r'\s*\|\s*jay campbell podcast$', '', title)
    title = re.sub(r'\s*\|\s*jay campbell pc$', '', title)
    title = re.sub(r'\|\s*jay campbell pc$', '', title)
    # w/ to with
    title = re.sub(r'\bw/\s*', 'with ', title)
    title = re.sub(r'\bw⧸\s*', 'with ', title)
    
    return re.sub(r'\s+', ' ', title).strip()


def match_videos_to_transcripts(
    youtube_videos: list[dict],
    transcript_titles: list[str]
) -> tuple[list[dict], list[dict], list[dict]]:
    """Match YouTube videos to transcript titles."""
    
    # Create normalized lookup
    transcript_lookup = {normalize_title(t): t for t in transcript_titles}
    
    matched = []
    unmatched = []
    potential_matches = []
    
    for video in youtube_videos:
        yt_title = video['title']
        normalized_yt = normalize_title(yt_title)
        
        # Direct match
        if normalized_yt in transcript_lookup:
            video['matched_title'] = transcript_lookup[normalized_yt]
            video['match_type'] = 'exact'
            matched.append(video)
            continue
        
        # Substring match
        found = False
        for norm_trans, orig_trans in transcript_lookup.items():
            if normalized_yt in norm_trans or norm_trans in normalized_yt:
                if len(normalized_yt) > 20 and len(norm_trans) > 20:
                    video['matched_title'] = orig_trans
                    video['match_type'] = 'substring'
                    potential_matches.append(video)
                    found = True
                    break
        
        if not found:
            unmatched.append(video)
    
    return matched, unmatched, potential_matches


def save_results(
    matched: list[dict],
    unmatched: list[dict],
    potential: list[dict],
    transcript_titles: list[str]
):
    """Save detailed results."""
    
    # JSON output
    results = {
        'generated_at': json.dumps({'now': True}),  # placeholder
        'summary': {
            'youtube_total': len(matched) + len(unmatched) + len(potential),
            'transcript_titles': len(transcript_titles),
            'matched_exact': len(matched),
            'potential_matches': len(potential),
            'missing': len(unmatched),
            'coverage_percent': round(100 * len(matched) / (len(matched) + len(unmatched) + len(potential)), 1)
        },
        'missing_videos': unmatched,
        'potential_matches': potential,
        'matched_videos': matched
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Detailed results: {OUTPUT_JSON}")
    
    # Text report
    lines = [
        "=" * 70,
        "JAY CAMPBELL TRANSCRIPT MATCH REPORT",
        "=" * 70,
        "",
        f"YouTube Videos Found: {len(matched) + len(unmatched) + len(potential)}",
        f"Transcript Titles: {len(transcript_titles)}",
        f"Exact Matches: {len(matched)}",
        f"Potential Matches: {len(potential)}",
        f"Missing: {len(unmatched)}",
        f"Coverage: {round(100 * len(matched) / (len(matched) + len(unmatched) + len(potential)), 1)}%",
        "",
        "=" * 70,
        "MISSING VIDEOS (Need Transcripts)",
        "=" * 70,
        "",
    ]
    
    for i, video in enumerate(unmatched[:50], 1):  # First 50
        lines.append(f"{i}. {video['title']}")
        lines.append(f"   URL: {video['url']}")
        lines.append(f"   Video ID: {video['video_id']}")
        lines.append("")
    
    if len(unmatched) > 50:
        lines.append(f"... and {len(unmatched) - 50} more missing videos")
        lines.append("")
    
    if potential:
        lines.extend([
            "=" * 70,
            "POTENTIAL MATCHES (Review These)",
            "=" * 70,
            "",
        ])
        
        for video in potential[:20]:
            lines.append(f"YouTube: {video['title']}")
            lines.append(f"Transcript: {video.get('matched_title', 'N/A')}")
            lines.append(f"URL: {video['url']}")
            lines.append("")
    
    report = '\n'.join(lines)
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"💾 Text report: {OUTPUT_REPORT}")
    return report


def main():
    print("=" * 70)
    print("🎙️ Jay Campbell Title Matcher")
    print("=" * 70)
    print()
    
    # Load inventory
    if not INVENTORY_PATH.exists():
        print(f"❌ Inventory not found. Run jay_campbell_collector.py first.")
        return
    
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        inventory = json.load(f)
    
    youtube_videos = inventory.get('videos', {}).get('missing', []) + \
                     inventory.get('videos', {}).get('with_transcripts', [])
    
    print(f"📺 YouTube videos: {len(youtube_videos)}")
    
    # Extract titles from transcripts
    print("\n📄 Extracting titles from transcript files...")
    transcript_titles = extract_titles_from_transcripts()
    
    if not transcript_titles:
        print("❌ No titles found in transcripts")
        return
    
    # Match
    print("\n🔍 Matching titles...")
    matched, unmatched, potential = match_videos_to_transcripts(youtube_videos, transcript_titles)
    
    # Save results
    print("\n💾 Saving results...")
    report = save_results(matched, unmatched, potential, transcript_titles)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"✅ Exact matches: {len(matched)}")
    print(f"🔍 Potential matches: {len(potential)}")
    print(f"❌ Missing (need download): {len(unmatched)}")
    print(f"📈 Coverage: {round(100 * len(matched) / len(youtube_videos), 1)}%")
    print()
    print(report.split("MISSING VIDEOS")[1].split("\n\n")[0] if "MISSING VIDEOS" in report else "")
    
    print("\n" + "=" * 70)
    print("✅ Done! Check:")
    print(f"   📄 {OUTPUT_JSON} - Full data")
    print(f"   📄 {OUTPUT_REPORT} - Text report")
    print("=" * 70)


if __name__ == '__main__':
    main()
