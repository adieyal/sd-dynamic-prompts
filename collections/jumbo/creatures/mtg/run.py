import shutil
from glob import glob
from pathlib import Path

def clean(s):
    return s.replace(" ", "_").replace("'", "").replace('"', "").lower()

for f in Path("creatures/").glob("*.txt"):
    parts = f.stem.split("-")
    if len(parts) == 1:
        # move file to current directory
        shutil.move(f, f"{clean(parts[0])}.txt")
    elif len(parts) == 2:
        name = clean(f.stem.split("-")[1])
        shutil.move(f, f"{name}.txt")
    #print(f.stem.split("-")[1])
