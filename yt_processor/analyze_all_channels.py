#!/usr/bin/env python3
"""Analyze all channel transcripts for merging strategy."""
from pathlib import Path

TRANSCRIPTS_BASE = Path(r'C:\Users\aweis\Downloads\anything youtube\transcripts')

channels = {
    'daru': 'DaruStrongPerformance',
    'warriorcollective': 'Warrior Collective',
    'combatathletephysio': 'Combat Athlete Physio',
    'coachmicahb': 'Coach Micah B'
}

print("="*80)
print("TRANSCRIPT ANALYSIS - ALL CHANNELS")
print("="*80)

total_all_words = 0
total_all_files = 0
total_all_bytes = 0

for folder, name in channels.items():
    channel_dir = TRANSCRIPTS_BASE / folder
    if not channel_dir.exists():
        print(f"\n{name}: Folder not found")
        continue
    
    files = list(channel_dir.glob('*.md'))
    total_words = 0
    total_bytes = 0
    
    for f in files:
        content = f.read_text(encoding='utf-8', errors='ignore')
        words = len(content.split())
        bytes_ = len(content.encode('utf-8'))
        total_words += words
        total_bytes += bytes_
    
    total_all_words += total_words
    total_all_files += len(files)
    total_all_bytes += total_bytes
    
    print(f"\n{name}:")
    print(f"  Files: {len(files)}")
    print(f"  Words: {total_words:,}")
    print(f"  Size: {total_bytes / (1024*1024):.1f} MB")
    print(f"  Avg words/file: {total_words // len(files) if files else 0:,}")

print("\n" + "="*80)
print(f"GRAND TOTAL:")
print(f"  Files: {total_all_files}")
print(f"  Words: {total_all_words:,}")
print(f"  Size: {total_all_bytes / (1024*1024):.1f} MB")
print("="*80)

print(f"\nNotebookLM Constraints:")
print(f"  Max words per source: 500,000")
print(f"  Safe target: 450,000 words per file")
print(f"  Max file size: ~200 MB")

print(f"\nMerging Strategy:")
min_files = (total_all_words // 450000) + 1
max_files = (total_all_words // 350000) + 1
print(f"  Need {min_files}-{max_files} merged files to stay under 450k words each")
print(f"\nRecommended approach:")
print(f"  - Keep each channel separate (4 files)")
print(f"  - OR merge by topic across channels (5-7 files)")
print(f"  - OR chronological batches (6-8 files)")
