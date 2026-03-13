#!/usr/bin/env python3
"""
Download transcripts for @heatrick videos NOT in playlists (excluding fight footage).
Categorize each into the most appropriate existing playlist folder.
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_ROOT = os.path.join(os.path.dirname(BASE_DIR), "transcripts", "heatrick")
os.makedirs(TRANSCRIPTS_ROOT, exist_ok=True)

# Force yt-dlp from this Python install
scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
yt_dlp_exe = os.path.join(scripts_dir, "yt-dlp.exe")
if not os.path.exists(yt_dlp_exe):
    yt_dlp_exe = "yt-dlp"

print(f"Using yt-dlp: {yt_dlp_exe}")

# Videos to download with their categorization
# Format: (video_id, title, playlist_folder)
VIDEOS_TO_DOWNLOAD = [
    # Assessments / Training Info
    ("oT0MdnbGy88", "The 5-Minute Assessment That Will Transform Your Muay Thai Training", "Muay Thai Strength and Conditioning Info"),
    
    # Podcast / Interviews
    ("X6lwGg4wNqQ", "Muay Thai & The Quest for Self Discovery w/ Abasolo, Ten Pow, Ghazali, and Todd", "Podcast"),
    ("tE9kidT1qMU", "Embracing Imperfect Progress in Muay Thai with Kevin Ross", "Podcast"),
    ("VAGPn7wPZRI", "The Truth About Fighters Achieving Goals w/ Matt Lucas", "Podcast"),
    
    # Mindset / Coach's Quick Chat
    ("8qSe8puRYgg", "Hindsight - My Young Fighter Training Mistake", "Coachs Quick Chat Episodes"),
    ("vX4ZyI67sSI", "Developing a Growth Mindset For Fighters - My Own Battle", "Coachs Quick Chat Episodes"),
    ("sxOwM-Lwov8", "Muay Thai - Setbacks ALREADY", "Coachs Quick Chat Episodes"),
    ("-z-yecdpqrQ", "Pre-fight Fear, Introverts Shifting State, & Champs Need More Than S&C", "Coachs Quick Chat Episodes"),
    ("8fCCkEHMVzw", "I won my fight, but nearly lost everything", "Coachs Quick Chat Episodes"),
    ("Z-doSVUR0lM", "How to Remain On It Without an Upcoming Fight", "Coachs Quick Chat Episodes"),
    ("xok8y0pmG5Y", "Mind, Body, and Spirit in Muay Thai - The Hidden Qualities of a Complete Fighter", "Coachs Quick Chat Episodes"),
    ("eH5htM3ldwk", "Tell Me, Who Are You Muay Thai fighter, coach", "Coachs Quick Chat Episodes"),
    ("TIRhupiPemE", "Powerful Lessons From The Legacy Of Jordan Coe A Tribute to his Legacy", "Coachs Quick Chat Episodes"),
    
    # S&C Info / Training
    ("jvJdE_-QVRM", "Muay Thai Sport Specific Training Overkill The Hidden Risks", "Muay Thai Strength and Conditioning Info"),
    ("EugZxbpisdU", "Jumping Higher For Fighters - Muay Thai Jump Knee Analysis", "Muay Thai Biomechanics"),
    ("Do33QudKyYo", "How To Fight Stronger Muay Thai Fighters - Strategy", "Muay Thai Fight IQ"),
    ("uOyOyKCjYH0", "Train Like This Now or Quit Muay Thai Early (Age-Proof Your Fighting)", "Age Defying Muay Thai Fighter Series"),
    ("0YW4mNHfJgs", "Worked Example Planning Muay Thai S&C For Two Fight Dates", "Muay Thai Strength and Conditioning Info"),
    ("Wr3Qu6LmrT0", "The Biggest Mistakes Fighters Make in S&C for Muay Thai", "Muay Thai Strength and Conditioning Info"),
    ("L0u0Y4L_kIw", "How To Choose Exercises For a Fighters S&C Session", "Muay Thai Strength and Conditioning Info"),
    ("5s5k2_q1BU8", "Weekly Commitment - Setting Expectations For Muay Thai Strength and Conditioning", "Muay Thai Strength and Conditioning Info"),
    
    # Q&A
    ("jDOD-OVEvnI", "IG Live Don Heatrick Muay Thai S&C Q&A 04", "MT_S_C Q_A Episodes"),
    
    # Exercises
    ("VCC40thN0-Y", "Shuttle Run Technique for Optimal Cardio for Fighters MAS Training", "Muay Thai Strength and Conditioning Exercises"),
    ("P-EK7oMqEUo", "Nothing To Pull From Body Weight Exercise - Floor Wiper Press", "Muay Thai Strength and Conditioning Exercises"),
    ("3ZYnzbWQam8", "Muay Thai Clinch Strength Exercise - Alternate Side Chin Grip Chin Ups", "Muay Thai Strength and Conditioning Exercises"),
    
    # Injury / Mobility
    ("E0VRrd7HtjA", "Mid Back Rotation Mobility For Fighters Thoracic Spine", "Injury Prehab_Rehab"),
    ("U5IFOOp3ZWo", "Thoracic Spine Rotation Test For Fighters", "Injury Prehab_Rehab"),
    
    # Fight Analysis
    ("vQDKvDbtzbg", "Nungubon vs Rittidet - Muay Thai Fight Analysis shorts", "Fight Analysis"),
    
    # Shorts / Misc (put in Coach's Quick Chat)
    ("gKHLdTG0G14", "How Pre Fight Rituals Boost Confidence & Performance - Part 2", "Coachs Quick Chat Episodes"),
    ("06KCqsymTnI", "Splits Routine for Fighters shorts", "Muay Thai Strength and Conditioning Exercises"),
    ("A0EZHsBZIGs", "Pre-Fight Nerves shorts", "Coachs Quick Chat Episodes"),
    ("ATLtGxiBcQQ", "Muay Thai Kids Are On A Different Level shorts", "Coachs Quick Chat Episodes"),
    ("Z99VRXmpz6k", "45 years old and just won a muay thai title shorts", "Age Defying Muay Thai Fighter Series"),
    ("eapMRJSY8Lo", "Golden Era Muay Thai fighters whos your favorite shorts", "Coachs Quick Chat Episodes"),
    ("HjlyuFkXByY", "Fight Skill Part 2 shorts", "Muay Thai Fight IQ"),
    
    # Testimonials / Intro
    ("M9toK3E3nDw", "Ajay Al Saeed - S&C Program Testimonial", "Featuring Don Heatrick"),
    ("GTNyFFGC_aw", "Don Heatricks Muay Thai Strength and Conditioning Program Testimonials", "Featuring Don Heatrick"),
    ("xYVcOlr8XF0", "Welcome to MuayThai Tube - message from Don Heatrick", "Featuring Don Heatrick"),
]


def sanitize_foldername(name):
    """Remove characters that are invalid in Windows folder names."""
    return "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name).strip()


def sanitize_filename(title):
    """Sanitize a video title to be a safe Windows filename."""
    name = "".join(c if c.isalnum() or c in (" ", "-", "_", "(", ")", "[", "]", ".", ",") else "_" for c in title).strip()
    name = " ".join(name.split())
    if len(name) > 80:
        name = name[:77] + "..."
    return name


def download_cleaned_transcript(video_id, title, output_dir):
    """Download auto-generated English subtitles and strip timestamps."""
    os.makedirs(output_dir, exist_ok=True)
    
    temp_template = os.path.join(output_dir, f"{video_id}.%(ext)s")
    cmd = [
        yt_dlp_exe,
        "--write-auto-sub",
        "--sub-langs", "en",
        "--skip-download",
        "--convert-subs", "srt",
        "-o", temp_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  - FAILED {video_id}: {e.stderr.strip()[:100]}")
        return None

    srt_path = os.path.join(output_dir, f"{video_id}.en.srt")
    if not os.path.exists(srt_path):
        srt_path = os.path.join(output_dir, f"{video_id}.srt")
    if not os.path.exists(srt_path):
        print(f"  - NO SUBS {video_id}")
        return None

    safe_name = sanitize_filename(title)
    md_path = os.path.join(output_dir, f"{safe_name}.md")
    with open(srt_path, "r", encoding="utf-8") as f_in, open(md_path, "w", encoding="utf-8") as f_out:
        seen = set()
        f_out.write(f"# {title}\n\n")
        f_out.write(f"https://www.youtube.com/watch?v={video_id}\n\n")
        for line in f_in:
            line = line.strip()
            if not line: continue
            if line.isdigit(): continue
            if "-->" in line: continue
            if line in seen: continue
            seen.add(line)
            f_out.write(line + "\n")
    os.remove(srt_path)
    return md_path


def main():
    print(f"Downloading {len(VIDEOS_TO_DOWNLOAD)} transcripts...")
    print(f"Output root: {TRANSCRIPTS_ROOT}\n")
    
    success = 0
    failed = 0
    
    for i, (vid, title, playlist) in enumerate(VIDEOS_TO_DOWNLOAD, 1):
        folder_name = sanitize_foldername(playlist)
        output_dir = os.path.join(TRANSCRIPTS_ROOT, folder_name)
        
        print(f"[{i}/{len(VIDEOS_TO_DOWNLOAD)}] {title[:50]}...")
        print(f"  -> {folder_name}/")
        
        md_path = download_cleaned_transcript(vid, title, output_dir)
        if md_path:
            success += 1
            print(f"  OK: {os.path.basename(md_path)}")
        else:
            failed += 1
    
    print(f"\n=== DONE ===")
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    print(f"Output: {TRANSCRIPTS_ROOT}")


if __name__ == "__main__":
    main()
