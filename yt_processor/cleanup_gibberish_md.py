import os
import re

root = r"C:\Users\aweis\Downloads\New folder (3)\transcripts\MuayThaiPros"
pattern = re.compile(r'^[A-Za-z0-9_-]{11}\.md$')

deleted = 0
for dirpath, _, filenames in os.walk(root):
    for fname in filenames:
        if pattern.match(fname):
            fpath = os.path.join(dirpath, fname)
            print(f"Deleting {fpath}")
            os.remove(fpath)
            deleted += 1

print(f"Deleted {deleted} gibberish .md files.")
