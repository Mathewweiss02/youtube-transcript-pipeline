import pathlib
import json
import subprocess
import shutil
from collections import defaultdict

VIDEO_DIR = pathlib.Path(r"c:/Users/aweis/Downloads/YouTube_Tools_Scripts/Videos/bika_ai")
OUTPUT_DIR = VIDEO_DIR / "Merged"
MAX_DURATION = 45 * 60  # 45 minutes in seconds

OUTPUT_DIR.mkdir(exist_ok=True)

def get_duration_from_json(info_file):
    try:
        with open(info_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('duration', 0)
    except:
        return 0

def categorize_video(title):
    title_lower = title.lower()
    
    if 'beginner guide' in title_lower:
        if 'agent' in title_lower:
            return '01_Agents_Beginner'
        return '00_Beginner_Guides'
    elif 'automation' in title_lower or 'template' in title_lower:
        if 'email' in title_lower:
            return '02_Email_Automation'
        elif 'stock' in title_lower:
            return '03_Stock_Automation'
        elif 'reminder' in title_lower:
            return '04_Reminders'
        elif 'slack' in title_lower:
            return '05_Slack'
        elif 'invoice' in title_lower or 'ocr' in title_lower:
            return '06_Invoice_OCR'
        elif 'ai' in title_lower:
            return '07_AI_Features'
        else:
            return '08_General_Automation'
    elif 'agent' in title_lower:
        return '09_Agents_Advanced'
    else:
        return '10_Other'

def get_videos_with_durations():
    videos = []
    for video_file in VIDEO_DIR.glob("*.mp4"):
        info_file = video_file.with_suffix('.info.json')
        duration = get_duration_from_json(info_file)
        if duration > 0:
            category = categorize_video(video_file.stem)
            videos.append({
                'path': video_file,
                'title': video_file.stem,
                'duration': duration,
                'category': category
            })
    
    # Sort by category, then by title
    videos.sort(key=lambda x: (x['category'], x['title']))
    return videos

def merge_videos(video_list, output_name):
    # Create temp directory for safe filenames
    temp_dir = OUTPUT_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    concat_file = temp_dir / f"concat_list.txt"
    temp_files = []
    
    with open(concat_file, 'w', encoding='utf-8') as f:
        for i, video in enumerate(video_list):
            # Copy to temp with safe name
            temp_name = f"temp_{i:03d}.mp4"
            temp_path = temp_dir / temp_name
            shutil.copy2(video['path'], temp_path)
            temp_files.append(temp_path)
            f.write(f"file '{temp_path.absolute()}'\n")
    
    output_file = OUTPUT_DIR / f"{output_name}.mp4"
    
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-c', 'copy',
        '-y',
        str(output_file)
    ]
    
    print(f"Merging {len(video_list)} videos into {output_file}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Cleanup temp files
    for temp_file in temp_files:
        if temp_file.exists():
            temp_file.unlink()
    concat_file.unlink()
    
    if result.returncode != 0:
        print(f"Error merging: {result.stderr}")
        return False
    
    return True

def smart_merge():
    videos = get_videos_with_durations()
    print(f"Found {len(videos)} videos")
    
    # Group by category
    categories = defaultdict(list)
    for video in videos:
        categories[video['category']].append(video)
    
    # Process each category
    merge_number = 1
    total_merged = 0
    
    for category_name in sorted(categories.keys()):
        category_videos = categories[category_name]
        print(f"\nProcessing category: {category_name} ({len(category_videos)} videos)")
        
        current_chunk = []
        current_duration = 0
        
        for video in category_videos:
            if current_duration + video['duration'] <= MAX_DURATION:
                current_chunk.append(video)
                current_duration += video['duration']
            else:
                # Merge current chunk
                if current_chunk:
                    chunk_name = f"{category_name}_PART_{merge_number:02d}"
                    if merge_videos(current_chunk, chunk_name):
                        total_merged += len(current_chunk)
                    merge_number += 1
                
                # Start new chunk
                current_chunk = [video]
                current_duration = video['duration']
        
        # Merge remaining chunk
        if current_chunk:
            chunk_name = f"{category_name}_PART_{merge_number:02d}"
            if merge_videos(current_chunk, chunk_name):
                total_merged += len(current_chunk)
            merge_number += 1
    
    print(f"\nComplete! Merged {total_merged} videos into {merge_number - 1} files")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Clean up temp directory
    temp_dir = OUTPUT_DIR / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    smart_merge()
