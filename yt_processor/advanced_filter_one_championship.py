#!/usr/bin/env python3
"""
Advanced Filter for ONE Championship Videos
Apply stricter criteria to get only the best instructional content
"""

import json
from pathlib import Path
from datetime import datetime

def apply_advanced_filter(video):
    """
    Apply stricter filtering criteria
    Returns (keep: bool, reason: str)
    """
    
    title = video.get('title', '').lower() if video.get('title') else ''
    uploader = video.get('uploader', '').lower() if video.get('uploader') else ''
    duration = video.get('duration')
    view_count = video.get('view_count')
    quality_score = video.get('quality_score', 0)
    categories = video.get('categories', [])
    
    # Filter 1: Must have good quality score
    if quality_score < 70:
        return False, "Quality score too low (< 70)"
    
    # Filter 2: Prefer videos with instructional categories
    instructional_categories = [
        'strength_conditioning', 'warmup_mobility', 'training_routine',
        'pad_work', 'technique_tutorial', 'shadow_boxing', 'cardio_running',
        'clinch_work'
    ]
    
    has_instructional = any(cat in instructional_categories for cat in categories)
    
    # If it's only fight_analysis, interview, or other, be more selective
    if not has_instructional:
        if view_count and view_count < 10000:
            return False, "Non-instructional with low views (< 10K)"
    
    # Filter 3: Duration sweet spot (prefer 2-20 minutes for instructional content)
    if duration:
        if duration < 120:  # Less than 2 minutes
            return False, "Too short for quality instruction (< 2 min)"
        if duration > 3600:  # More than 1 hour
            return False, "Too long (> 1 hour)"
    
    # Filter 4: View count threshold (prefer popular content)
    if view_count and view_count < 500:
        return False, "Low view count (< 500)"
    
    # Filter 5: Exclude certain uploader patterns
    spam_uploaders = ['compilation', 'highlights', 'clips', 'shorts']
    if any(spam in uploader for spam in spam_uploaders):
        return False, f"Spam uploader pattern"
    
    # Filter 6: Title must have some substance
    if len(title) < 10:
        return False, "Title too short"
    
    # Filter 7: Prefer known quality channels
    quality_channels = [
        'fightlore', 'evolve', 'fairtex', 'yokkao', 'one championship',
        'muay thai', 'kickboxing', 'official', 'gym', 'training center',
        'academy', 'workshop', 'breakdown', 'pros', 'masterclass'
    ]
    
    has_quality_channel = any(channel in uploader for channel in quality_channels)
    
    # If not from quality channel, must have high views
    if not has_quality_channel:
        if view_count and view_count < 5000:
            return False, "Unknown channel with low views (< 5K)"
    
    # Filter 8: Exclude generic/vague titles
    vague_titles = [
        'training', 'workout', 'session', 'gym', 'sparring',
        'fight', 'vs', 'highlights', 'best'
    ]
    
    # If title is ONLY these words (too generic)
    title_words = set(title.split())
    if title_words and title_words.issubset(set(vague_titles)):
        return False, "Title too generic"
    
    return True, None

def calculate_final_score(video):
    """
    Calculate final score with additional criteria (0-100)
    """
    
    score = video.get('quality_score', 50)
    
    title = video.get('title', '').lower() if video.get('title') else ''
    uploader = video.get('uploader', '').lower() if video.get('uploader') else ''
    duration = video.get('duration')
    view_count = video.get('view_count')
    categories = video.get('categories', [])
    
    # Bonus for instructional categories
    instructional_categories = [
        'strength_conditioning', 'warmup_mobility', 'training_routine',
        'pad_work', 'technique_tutorial', 'shadow_boxing'
    ]
    
    instructional_count = sum(1 for cat in categories if cat in instructional_categories)
    score += instructional_count * 5
    
    # Bonus for quality keywords in title
    quality_keywords = [
        'tutorial', 'breakdown', 'technique', 'masterclass', 'training',
        'routine', 'workout', 'session', 'exclusive', 'full'
    ]
    
    keyword_count = sum(1 for keyword in quality_keywords if keyword in title)
    score += min(keyword_count * 3, 15)
    
    # Bonus for quality channels
    quality_channels = [
        'fightlore', 'evolve', 'fairtex', 'yokkao', 'one championship',
        'official'
    ]
    
    if any(channel in uploader for channel in quality_channels):
        score += 10
    
    # Bonus for optimal duration (3-15 minutes)
    if duration and 180 <= duration <= 900:
        score += 10
    
    # Bonus for very high view count
    if view_count:
        if view_count >= 50000:
            score += 15
        elif view_count >= 20000:
            score += 10
        elif view_count >= 10000:
            score += 5
    
    # Cap at 100
    return min(score, 100)

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("ADVANCED ONE CHAMPIONSHIP VIDEO FILTER")
    print("Applying stricter criteria for best instructional content")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load the filtered videos
    results_dir = Path('one_championship_search_results')
    
    # Get the most recent filtered file
    filtered_files = list(results_dir.glob('one_championship_filtered_*.json'))
    
    if not filtered_files:
        print("ERROR: No filtered files found in", results_dir)
        return
    
    latest_file = max(filtered_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        all_videos = json.load(f)
    
    print(f"Loaded {len(all_videos)} videos")
    print()
    
    # Apply advanced filter
    print("Applying advanced filters...")
    best_videos = []
    filtered_out = {}
    
    for video in all_videos:
        keep, reason = apply_advanced_filter(video)
        
        if not keep:
            if reason not in filtered_out:
                filtered_out[reason] = []
            filtered_out[reason].append(video)
        else:
            # Recalculate score with additional criteria
            video['final_score'] = calculate_final_score(video)
            best_videos.append(video)
    
    print(f"✓ Kept {len(best_videos)} videos ({len(best_videos)/len(all_videos)*100:.1f}%)")
    print(f"✓ Filtered out {len(all_videos) - len(best_videos)} more videos")
    print()
    
    # Show filter breakdown
    print("ADVANCED FILTER BREAKDOWN:")
    for reason, videos in sorted(filtered_out.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {reason}: {len(videos)} videos")
    print()
    
    # Sort by final score
    best_videos.sort(key=lambda x: x['final_score'], reverse=True)
    
    # Save best videos
    output_file = results_dir / f'one_championship_best_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(best_videos, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved best videos to: {output_file}")
    
    # Save elite videos (score >= 85)
    elite_videos = [v for v in best_videos if v['final_score'] >= 85]
    elite_file = results_dir / f'one_championship_elite_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(elite_file, 'w', encoding='utf-8') as f:
        json.dump(elite_videos, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(elite_videos)} elite videos (score >= 85) to: {elite_file}")
    print()
    
    # Generate statistics
    print("=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    
    # Count by fighter
    fighter_counts = {}
    for video in best_videos:
        fighter = video.get('fighter', 'Unknown')
        fighter_counts[fighter] = fighter_counts.get(fighter, 0) + 1
    
    print(f"\nTop 20 Fighters by Video Count ({len(best_videos)} total):")
    for fighter, count in sorted(fighter_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {fighter}: {count} videos")
    
    # Count by category
    category_counts = {}
    for video in best_videos:
        for category in video.get('categories', []):
            category_counts[category] = category_counts.get(category, 0) + 1
    
    print("\nVideos by Category:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count} videos")
    
    # Score distribution
    elite_count = len([v for v in best_videos if v['final_score'] >= 85])
    high_count = len([v for v in best_videos if 75 <= v['final_score'] < 85])
    medium_count = len([v for v in best_videos if v['final_score'] < 75])
    
    print(f"\nFinal Score Distribution:")
    print(f"  Elite (85-100): {elite_count} videos ({elite_count/len(best_videos)*100:.1f}%)")
    print(f"  High (75-84): {high_count} videos ({high_count/len(best_videos)*100:.1f}%)")
    print(f"  Medium (0-74): {medium_count} videos ({medium_count/len(best_videos)*100:.1f}%)")
    
    # Show top 10 videos
    print(f"\nTop 10 Highest Scoring Videos:")
    for i, video in enumerate(best_videos[:10], 1):
        print(f"  {i}. [{video['final_score']}] {video['title'][:60]}...")
        print(f"     Fighter: {video['fighter']} | Views: {video.get('view_count', 'N/A')}")
    
    # Channel quality
    channel_counts = {}
    for video in best_videos:
        channel = video.get('uploader', 'Unknown')
        channel_counts[channel] = channel_counts.get(channel, 0) + 1
    
    print(f"\nTop 15 Channels:")
    for channel, count in sorted(channel_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {channel}: {count} videos")
    
    print()
    print("=" * 80)
    print("FILTERING COMPLETE!")
    print("=" * 80)
    print()
    print(f"Journey: 7,700 → 1,103 → {len(best_videos)} videos")
    print(f"Elite content (score ≥ 85): {elite_count} videos")
    print()
    print("Next steps:")
    print("  1. Review elite videos for transcript download")
    print("  2. Download transcripts from best content")
    print("  3. Create master training catalog")

if __name__ == '__main__':
    main()
