from glob import glob
import os
misc = []

with open("misc.txt", "w") as outfile:
    for fn in glob("*.txt"):
        rows = open(fn).readlines()
        rows = [r.strip() for r in rows]
        if len(rows) <= 2:
            misc.extend(rows)
            print(fn)
            # delete the file
            #os.remove(fn)
    outfile.write("\n".join(misc))
