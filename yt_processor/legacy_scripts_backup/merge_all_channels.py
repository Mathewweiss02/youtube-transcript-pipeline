#!/usr/bin/env python3
"""
Merge all channel transcripts into NotebookLM-ready files.
Excludes irrelevant videos and creates files under 450k words each.
"""
from pathlib import Path
import re

TRANSCRIPTS_BASE = Path(r'C:\Users\aweis\Downloads\anything youtube\transcripts')
OUTPUT_DIR = Path(r'C:\Users\aweis\Downloads\anything youtube\transcripts\merged_combat_sports')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

channels = {
    'daru': 'DaruStrongPerformance',
    'warriorcollective': 'Warrior Collective',
    'combatathletephysio': 'Combat Athlete Physio',
    'coachmicahb': 'Coach Micah B'
}

# Keywords to identify videos to EXCLUDE
EXCLUDE_PATTERNS = [
    r'things every man',
    r'confidence',
    r'opening your own gym',
    r'fitness empire',
    r'coaching celebrities',
    r'business',
    r'entrepreneur',
    r'lifestyle',
    r'advice',
    r'motivation',
    r'challenge',
    r'\bpr\b',
    r'max effort',
    r'phenom',
    r'world.?s strongest',
    r'celebrity',
    r'review',
    r'unboxing',
    r'supplement',
    r'gear',
    r'equipment review',
    r'vlog',
    r'day in',
    r'behind the scenes',
    r'tour',
    r'q&a',
    r'ask.*anything',
]

def should_exclude(filename):
    """Check if a file should be excluded based on title."""
    title_lower = filename.lower()
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, title_lower, re.IGNORECASE):
            return True
    return False

def merge_channel_files(channel_folder, channel_name, max_words=400000):
    """Merge all files from a channel into one or more output files."""
    channel_dir = TRANSCRIPTS_BASE / channel_folder
    if not channel_dir.exists():
        print(f"Skipping {channel_name} - folder not found")
        return []
    
    files = sorted(channel_dir.glob('*.md'))
    
    # Filter out excluded files
    included_files = []
    excluded_count = 0
    for f in files:
        if should_exclude(f.stem):
            excluded_count += 1
        else:
            included_files.append(f)
    
    print(f"\n{channel_name}:")
    print(f"  Total files: {len(files)}")
    print(f"  Excluded: {excluded_count}")
    print(f"  Including: {len(included_files)}")
    
    if not included_files:
        return []
    
    # Split into multiple files if needed
    output_files = []
    current_file_num = 1
    current_words = 0
    current_content = []
    
    for file_path in included_files:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            words = len(content.split())
            
            # If adding this would exceed limit, save current and start new
            if current_words + words > max_words and current_content:
                output_file = OUTPUT_DIR / f"{channel_folder}_part{current_file_num}.txt"
                output_file.write_text('\n\n---\n\n'.join(current_content), encoding='utf-8')
                output_files.append((output_file, current_words))
                print(f"  Created: {output_file.name} ({current_words:,} words)")
                
                current_file_num += 1
                current_content = []
                current_words = 0
            
            current_content.append(content)
            current_words += words
            
        except Exception as e:
            print(f"  Error reading {file_path.name}: {e}")
    
    # Save remaining content
    if current_content:
        output_file = OUTPUT_DIR / f"{channel_folder}_part{current_file_num}.txt"
        output_file.write_text('\n\n---\n\n'.join(current_content), encoding='utf-8')
        output_files.append((output_file, current_words))
        print(f"  Created: {output_file.name} ({current_words:,} words)")
    
    return output_files

def main():
    print("="*80)
    print("MERGING ALL CHANNELS FOR NOTEBOOKLM")
    print("="*80)
    
    all_outputs = []
    
    for folder, name in channels.items():
        outputs = merge_channel_files(folder, name)
        all_outputs.extend(outputs)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total merged files created: {len(all_outputs)}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("\nFiles created:")
    for file_path, word_count in all_outputs:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"  {file_path.name}: {word_count:,} words ({size_mb:.1f} MB)")
    
    total_words = sum(wc for _, wc in all_outputs)
    print(f"\nTotal words across all files: {total_words:,}")
    print(f"Average words per file: {total_words // len(all_outputs):,}")

if __name__ == "__main__":
    main()
