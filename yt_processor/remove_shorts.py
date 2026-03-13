#!/usr/bin/env python3
"""Detect and remove YouTube Shorts (videos ≤60 seconds) based on transcript length"""
import os
from pathlib import Path

RAW_DIR = Path("../transcripts/Hyperarch_Fascia_Raw")

# YouTube Shorts typically have very short transcripts
# Files under ~2KB with <30 lines are likely Shorts
SHORT_THRESHOLD_LINES = 30
SHORT_THRESHOLD_SIZE = 2500  # bytes

shorts_found = []

for file in RAW_DIR.glob("*.md"):
    size = file.stat().st_size
    with open(file, 'r', encoding='utf-8') as f:
        lines = len(f.readlines())
    
    # If file is very small and has few lines, it's likely a Short
    if size < SHORT_THRESHOLD_SIZE and lines < SHORT_THRESHOLD_LINES:
        shorts_found.append((file.name, size, lines))
        print(f"🗑️  SHORT DETECTED: {file.name} ({size} bytes, {lines} lines)")
        os.remove(file)

print(f"\n✅ Removed {len(shorts_found)} YouTube Shorts")
