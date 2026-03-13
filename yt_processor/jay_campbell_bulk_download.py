#!/usr/bin/env python3
"""
Jay Campbell Bulk Re-Downloader

Re-downloads all 269 Jay Campbell videos with:
- Proper video IDs embedded in transcripts
- Clean markdown format with URL: lines
- Titles matched to YouTube metadata
- Parallel downloading for speed

Usage:
    python jay_campbell_bulk_download.py [--dry-run] [--max-workers N]
"""

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Paths
INVENTORY_PATH = Path("jay_campbell_full_inventory.json")
OUTPUT_DIR = Path("../../transcripts/Jay_Campbell_Redownload")
LOG_PATH = Path("jay_campbell_download_log.json")

# yt-dlp settings
YT_DLP_OPTS = [
    "--write-auto-subs",  # Auto-generated subtitles
    "--sub-langs", "en",
    "--convert-subs", "srt",
    "--skip-download",  # Only subs, no video
    "--output", "%(id)s.%(ext)s",
]


def load_inventory() -> list[dict[str, Any]]:
    """Load the 269 videos from inventory."""
    if not INVENTORY_PATH.exists():
        print(f"❌ Inventory not found: {INVENTORY_PATH}")
        print("Run: python jay_campbell_collector.py")
        sys.exit(1)
    
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos = data.get('videos', {}).get('missing', []) + \
             data.get('videos', {}).get('with_transcripts', [])
    
    return videos


def clean_vtt_to_markdown(vtt_content: str, video: dict) -> str:
    """Convert VTT to clean markdown with proper format."""
    lines = vtt_content.split('\n')
    
    # Extract transcript text
    transcript_lines = []
    for line in lines:
        # Skip VTT headers and timing lines
        if line.strip().startswith('WEBVTT'):
            continue
        if re.match(r'^\d+:\d+', line.strip()):
            continue
        if line.strip() == '':
            continue
        # Remove VTT tags like <c>...</c>
        line = re.sub(r'<[^>]+>', '', line)
        if line.strip():
            transcript_lines.append(line.strip())
    
    # Join and clean
    transcript = ' '.join(transcript_lines)
    transcript = re.sub(r'\s+', ' ', transcript).strip()
    
    # Build canonical format
    title = video['title']
    url = video['url']
    video_id = video['video_id']
    
    # Format duration
    duration = video.get('duration_formatted', '0:00')
    
    markdown = f"""# {title}

URL: {url}
Video ID: {video_id}
Duration: {duration}

{transcript}

---

"""
    return markdown


def download_single_video(video: dict, output_dir: Path, dry_run: bool = False) -> dict[str, Any]:
    """Download and process a single video."""
    video_id = video['video_id']
    url = video['url']
    title = video['title']
    
    result = {
        'video_id': video_id,
        'title': title[:80] + '...' if len(title) > 80 else title,
        'status': 'pending',
        'error': None,
        'output_file': None
    }
    
    if dry_run:
        result['status'] = 'dry_run'
        return result
    
    try:
        # Create temp directory for this download
        temp_dir = output_dir / f"temp_{video_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Download subtitles with yt-dlp
        cmd = [
            "yt-dlp",
            "--write-auto-subs",
            "--sub-langs", "en",
            "--convert-subs", "srt",
            "--skip-download",
            "--output", f"{video_id}.%(ext)s",
            "--quiet",
            url
        ]
        
        subprocess.run(cmd, cwd=temp_dir, check=True, capture_output=True, timeout=120)
        
        # Find the subtitle file
        sub_files = list(temp_dir.glob(f"{video_id}*.srt")) + list(temp_dir.glob(f"{video_id}*.vtt"))
        
        if not sub_files:
            result['status'] = 'no_subtitles'
            # Clean up temp dir
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return result
        
        # Read and convert
        sub_content = sub_files[0].read_text(encoding='utf-8', errors='ignore')
        markdown = clean_vtt_to_markdown(sub_content, video)
        
        # Write markdown file
        safe_title = re.sub(r'[^\w\s-]', '', title[:50]).strip()
        output_file = output_dir / f"{video_id}_{safe_title}.md"
        output_file.write_text(markdown, encoding='utf-8')
        
        result['status'] = 'success'
        result['output_file'] = str(output_file.relative_to(output_dir.parent.parent))
        
        # Clean up temp dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except subprocess.TimeoutExpired:
        result['status'] = 'timeout'
        result['error'] = 'Download timed out after 120s'
    except subprocess.CalledProcessError as e:
        result['status'] = 'failed'
        result['error'] = f"yt-dlp error: {e.stderr.decode()[:200] if e.stderr else 'unknown'}"
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)[:200]
    
    return result


def save_log(results: list[dict]):
    """Save download log."""
    log_data = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'results': results,
        'summary': {
            'total': len(results),
            'success': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] in ['failed', 'error']]),
            'no_subtitles': len([r for r in results if r['status'] == 'no_subtitles']),
            'timeout': len([r for r in results if r['status'] == 'timeout']),
        }
    }
    
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Log saved: {LOG_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Bulk re-download Jay Campbell videos")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    parser.add_argument("--max-workers", type=int, default=5, help="Parallel downloads (default: 5)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of videos to download")
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎙️ Jay Campbell Bulk Re-Downloader")
    print("=" * 70)
    
    # Load videos
    videos = load_inventory()
    
    if args.limit:
        videos = videos[:args.limit]
    
    print(f"\n📺 Videos to download: {len(videos)}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"⚡ Parallel workers: {args.max_workers}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No actual downloads")
        for v in videos[:10]:
            print(f"  Would download: {v['title'][:60]}...")
        if len(videos) > 10:
            print(f"  ... and {len(videos) - 10} more")
        return
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download
    print(f"\n⬇️  Starting downloads...")
    results = []
    
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(download_single_video, v, OUTPUT_DIR, args.dry_run): v
            for v in videos
        }
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            
            status_icon = {
                'success': '✅',
                'failed': '❌',
                'error': '❌',
                'no_subtitles': '⚠️',
                'timeout': '⏱️',
                'dry_run': '🔍'
            }.get(result['status'], '❓')
            
            print(f"  [{i}/{len(videos)}] {status_icon} {result['title'][:50]}... ({result['status']})")
            
            # Save progress every 10 videos
            if i % 10 == 0:
                save_log(results)
    
    # Final save
    save_log(results)
    
    # Summary
    success = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] in ['failed', 'error']])
    no_subs = len([r for r in results if r['status'] == 'no_subtitles'])
    
    print("\n" + "=" * 70)
    print("📊 DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"✅ Success: {success}/{len(videos)}")
    print(f"❌ Failed: {failed}/{len(videos)}")
    print(f"⚠️ No subtitles: {no_subs}/{len(videos)}")
    print(f"\n📁 Files saved to: {OUTPUT_DIR}")
    print(f"📄 Log: {LOG_PATH}")
    print("=" * 70)
    
    if success > 0:
        print("\n💡 Next steps:")
        print("   1. Review downloaded files in Jay_Campbell_Redownload/")
        print("   2. Run chunker to merge into consolidated parts")
        print("   3. Update sidecar with new video IDs")
        print("   4. Delete old Jay_Campbell/ directory when ready")


if __name__ == '__main__':
    main()
