#!/usr/bin/env python3
"""
Create Final Instructional Catalog
Remove unwanted categories and keep only training-focused content
"""

import json
from pathlib import Path
from datetime import datetime

def create_final_catalog():
    """Create final catalog with only instructional categories"""
    
    # Load elite videos
    results_dir = Path('one_championship_search_results')
    elite_file = results_dir / 'one_championship_elite_20260108_020544.json'
    
    with open(elite_file, 'r', encoding='utf-8') as f:
        elite_videos = json.load(f)
    
    print("=" * 80)
    print("CREATING FINAL INSTRUCTIONAL CATALOG")
    print("=" * 80)
    print(f"Starting with {len(elite_videos)} elite videos")
    print()
    
    # Categories to REMOVE
    unwanted_categories = {
        'other',
        'interview',
        'fight_analysis',
        'pad_work',
        'clinch_work'
    }
    
    # Categories to KEEP
    wanted_categories = {
        'training_routine',
        'strength_conditioning',
        'shadow_boxing',
        'cardio_running',
        'warmup_mobility',
        'technique_tutorial'  # KEEP - flag for later review
    }
    
    print("Removing unwanted categories:")
    for cat in unwanted_categories:
        print(f"  - {cat}")
    print()
    
    print("Keeping only instructional categories:")
    for cat in wanted_categories:
        print(f"  ✓ {cat}")
    print()
    
    # Filter videos
    instructional_videos = []
    removed_count = 0
    
    for video in elite_videos:
        categories = video.get('categories', [])
        
        # Check if video has any unwanted categories
        has_unwanted = any(cat in unwanted_categories for cat in categories)
        
        # Check if video has any wanted categories
        has_wanted = any(cat in wanted_categories for cat in categories)
        
        # Keep only if it has wanted categories and no unwanted categories
        if has_wanted and not has_unwanted:
            instructional_videos.append(video)
        else:
            removed_count += 1
    
    print(f"✓ Kept {len(instructional_videos)} instructional videos")
    print(f"✓ Removed {removed_count} videos")
    print()
    
    # Sort by final score
    instructional_videos.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    
    # Save final catalog
    output_file = results_dir / f'final_instructional_catalog_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(instructional_videos, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved final catalog to: {output_file}")
    
    # Create text version with links
    txt_file = results_dir / f'final_instructional_catalog_links_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("ONE CHAMPIONSHIP FINAL INSTRUCTIONAL CATALOG\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Videos: {len(instructional_videos)}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Group by category
        for category in wanted_categories:
            category_videos = [v for v in instructional_videos if category in v.get('categories', [])]
            
            if category_videos:
                f.write(f"\n{'='*80}\n")
                f.write(f"{category.upper().replace('_', ' ')} ({len(category_videos)} videos)\n")
                f.write(f"{'='*80}\n\n")
                
                for i, video in enumerate(category_videos, 1):
                    f.write(f"{i}. {video.get('title', 'No title')}\n")
                    f.write(f"   Fighter: {video.get('fighter', 'Unknown')}\n")
                    f.write(f"   URL: {video.get('url', 'No URL')}\n")
                    f.write(f"   Views: {video.get('view_count', 'N/A')}\n")
                    f.write(f"   Duration: {video.get('duration', 'N/A')}s\n")
                    f.write(f"   Score: {video.get('final_score', 'N/A')}\n")
                    f.write("\n")
    
    print(f"✓ Saved text catalog to: {txt_file}")
    print()
    
    # Generate statistics
    print("=" * 80)
    print("FINAL CATALOG STATISTICS")
    print("=" * 80)
    
    # Count by category
    category_counts = {}
    for video in instructional_videos:
        for category in video.get('categories', []):
            if category in wanted_categories:
                category_counts[category] = category_counts.get(category, 0) + 1
    
    print("\nVideos by Category:")
    for category in wanted_categories:
        count = category_counts.get(category, 0)
        print(f"  {category.upper().replace('_', ' ')}: {count} videos ({count/len(instructional_videos)*100:.1f}%)")
    
    # Count by fighter
    fighter_counts = {}
    for video in instructional_videos:
        fighter = video.get('fighter', 'Unknown')
        fighter_counts[fighter] = fighter_counts.get(fighter, 0) + 1
    
    print("\nTop 20 Fighters by Video Count:")
    for fighter, count in sorted(fighter_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {fighter}: {count} videos")
    
    # Score distribution
    elite_count = len([v for v in instructional_videos if v.get('final_score', 0) >= 85])
    high_count = len([v for v in instructional_videos if 75 <= v.get('final_score', 0) < 85])
    
    print(f"\nQuality Score Distribution:")
    print(f"  Elite (85-100): {elite_count} videos ({elite_count/len(instructional_videos)*100:.1f}%)")
    print(f"  High (75-84): {high_count} videos ({high_count/len(instructional_videos)*100:.1f}%)")
    
    # Show top 10 videos
    print(f"\nTop 10 Highest Scoring Videos:")
    for i, video in enumerate(instructional_videos[:10], 1):
        print(f"  {i}. [{video.get('final_score', 'N/A')}] {video.get('title', 'No title')[:60]}...")
        print(f"     Fighter: {video.get('fighter', 'Unknown')} | Views: {video.get('view_count', 'N/A')}")
    
    print()
    print("=" * 80)
    print("FINAL CATALOG CREATED!")
    print("=" * 80)
    print()
    print(f"Journey: 7,700 → 1,103 → 402 → {len(instructional_videos)} videos")
    print()
    print("Final catalog contains only:")
    print("  ✓ Training routines")
    print("  ✓ Strength & conditioning")
    print("  ✓ Shadow boxing")
    print("  ✓ Cardio & running")
    print("  ✓ Warm-up & mobility")
    print()
    print("Next steps:")
    print("  1. Download transcripts from final catalog")
    print("  2. Combine with Tawanchai results")
    print("  3. Create master training resource")

if __name__ == '__main__':
    create_final_catalog()
