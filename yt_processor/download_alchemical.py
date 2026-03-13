import subprocess
import json

result = subprocess.run(
    ['yt-dlp', '--flat-playlist', '--print', '%(title)s|%(id)s', 'https://www.youtube.com/@AlchemicalScience'],
    capture_output=True, text=True
)

videos = []
for line in result.stdout.strip().split('\n'):
    if '|' in line:
        parts = line.split('|')
        videos.append({
            'title': parts[0],
            'video_id': parts[1],
            'url': f'https://www.youtube.com/watch?v={parts[1]}'
        })

print(f'Found {len(videos)} videos')

with open('alchemical_science_videos.json', 'w') as f:
    json.dump(videos, f, indent=2)

print('Saved to alchemical_science_videos.json')
