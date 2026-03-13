import pathlib
import json
import subprocess
import shutil

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

def get_videos_with_durations():
    videos = []
    for video_file in VIDEO_DIR.glob("*.mp4"):
        info_file = video_file.with_suffix('.info.json')
        duration = get_duration_from_json(info_file)
        if duration > 0:
            videos.append({
                'path': video_file,
                'title': video_file.stem,
                'duration': duration
            })
    
    videos.sort(key=lambda x: x['title'])
    return videos

def merge_videos(video_list, output_name):
    temp_dir = OUTPUT_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    concat_file = temp_dir / f"concat_list.txt"
    temp_files = []
    
    with open(concat_file, 'w', encoding='utf-8') as f:
        for i, video in enumerate(video_list):
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
    
    for temp_file in temp_files:
        if temp_file.exists():
            temp_file.unlink()
    concat_file.unlink()
    
    if result.returncode != 0:
        print(f"Error merging: {result.stderr}")
        return False
    
    return True

def simple_merge():
    videos = get_videos_with_durations()
    print(f"Found {len(videos)} videos")
    
    current_chunk = []
    current_duration = 0
    merge_number = 1
    total_merged = 0
    
    for video in videos:
        if current_duration + video['duration'] <= MAX_DURATION:
            current_chunk.append(video)
            current_duration += video['duration']
        else:
            if current_chunk:
                chunk_name = f"bika_ai_merged_PART_{merge_number:02d}"
                if merge_videos(current_chunk, chunk_name):
                    total_merged += len(current_chunk)
                merge_number += 1
            
            current_chunk = [video]
            current_duration = video['duration']
    
    if current_chunk:
        chunk_name = f"bika_ai_merged_PART_{merge_number:02d}"
        if merge_videos(current_chunk, chunk_name):
            total_merged += len(current_chunk)
    
    temp_dir = OUTPUT_DIR / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    print(f"\nComplete! Merged {total_merged} videos into {merge_number} files")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    simple_merge()
