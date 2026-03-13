# Instructions for Computer 2 - Mark Bell Video Download (Part 2)

## Overview
This computer will download the **SECOND HALF** of Mark Bell's Power Project filtered videos.

**Computer 1** is downloading videos **1-951**  
**Computer 2** (this one) will download videos **952-1903**

**Total videos to download on this computer:** 952 videos

---

## Setup Instructions

### 1. Copy Required Files
Make sure you have these files from Computer 1:
- `mark_bell_filtered_list.txt` (the filtered video list)
- `yt-dlp.exe` (or path to yt-dlp executable)
- `download_mark_bell_part2.py` (the download script for this computer)

### 2. File Locations
Place files in this structure:
```
YouTube_Tools_Scripts/
├── yt-dlp-2025.11.12/
│   └── yt-dlp-2025.11.12/
│       └── yt-dlp.exe
└── yt_processor/
    ├── mark_bell_filtered_list.txt
    ├── download_mark_bell_part2.py
    └── downloads/  (will be created automatically)
```

---

## Running the Download

### Command:
```powershell
cd C:\Users\[YOUR_USERNAME]\Downloads\YouTube_Tools_Scripts
python yt_processor\download_mark_bell_part2.py
```

### What It Does:
1. Reads `mark_bell_filtered_list.txt`
2. Skips the first 951 videos (already done by Computer 1)
3. Downloads transcripts for videos **952-1903**
4. Saves cleaned transcripts to `yt_processor/downloads/`
5. Tracks progress and word counts

---

## Expected Results

- **Videos to download:** 952 (second half)
- **Estimated time:** 3-5 hours (depends on internet speed)
- **Estimated storage:** ~150-200 MB
- **Output format:** Clean text files (`.txt`) with video IDs as filenames

---

## Video Range Details

**Start:** Video #952  
**End:** Video #1903  
**Total:** 952 videos

This ensures **ZERO OVERLAP** with Computer 1's downloads.

---

## Monitoring Progress

The script will show:
- Current video number (e.g., `[1/952]`)
- Video title
- Success/failure status
- Word count for each transcript
- Progress updates every 50 videos

---

## After Download Completes

1. **Check the summary** - it will show:
   - Total successful downloads
   - Total failed downloads
   - Total word count
   - Estimated bundles needed

2. **Transfer files** - Copy the `downloads/` folder to merge with Computer 1's downloads

3. **Combine results** - Both computers' downloads will be merged for final processing

---

## Troubleshooting

### If yt-dlp is not found:
Edit `download_mark_bell_part2.py` and update the path on line 13:
```python
r'C:\Users\YOUR_USERNAME\Downloads\YouTube_Tools_Scripts\yt-dlp-2025.11.12\yt-dlp-2025.11.12\yt-dlp.exe'
```

### If download fails:
- Check internet connection
- Verify video URLs are accessible
- Check disk space (need ~200 MB free)

### If script errors:
- Make sure Python 3.x is installed
- Verify all files are in correct locations
- Check file paths match your system

---

## Important Notes

⚠️ **DO NOT modify the video range** - it's set to avoid overlap with Computer 1  
⚠️ **DO NOT delete** `mark_bell_filtered_list.txt` - needed for the script  
⚠️ **DO NOT interrupt** the download mid-process - let it complete or restart from beginning  

✅ The script is safe to restart - it will skip already downloaded videos  
✅ Progress is shown in real-time  
✅ All transcripts are cleaned and ready for NotebookLM  

---

## Final Step: Merging

After both computers finish:
1. Copy Computer 2's `downloads/` folder
2. Merge with Computer 1's `downloads/` folder
3. Run the bundling script to create NotebookLM-ready files
4. You'll have ~1,900 transcripts ready for processing!

---

**Questions?** Check the main script or contact the person who set this up.

**Good luck!** 🚀
