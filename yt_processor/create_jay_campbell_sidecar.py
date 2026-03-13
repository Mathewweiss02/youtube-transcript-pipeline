#!/usr/bin/env python3
"""Create sidecar JSON for Jay Campbell transcripts."""

import json
from pathlib import Path
from datetime import datetime

# Load inventory
with open('jay_campbell_full_inventory.json', 'r') as f:
    data = json.load(f)

videos = data.get('videos', {}).get('missing', []) + data.get('videos', {}).get('with_transcripts', [])

# Create sidecar
sidecar = {
    'channel': 'Jay_Campbell',
    'slug': 'jay-campbell',
    'generated_at': datetime.utcnow().isoformat() + 'Z',
    'total_videos': len(videos),
    'videos': []
}

for v in videos:
    sidecar['videos'].append({
        'video_id': v['video_id'],
        'title': v['title'],
        'url': v['url'],
        'duration': v.get('duration_formatted', '0:00'),
        'thumbnail': f"https://img.youtube.com/vi/{v['video_id']}/mqdefault.jpg"
    })

# Save to wiki app data folder
output_path = Path('../../youtuber wiki apps/my-app/data/transcript-video-sidecars.json')
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump({'jay-campbell': sidecar}, f, indent=2, ensure_ascii=False)

print(f'Sidecar created: {len(videos)} videos')
print(f'Output: {output_path}')
