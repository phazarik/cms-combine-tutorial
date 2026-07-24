import os
import glob
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
stray_patterns = [
    "combine_logger.out",
    "workspace*.root",
    "higgsCombine*.root",
    "roostats*",
    "*~", "*/*~",
    "*#", "*/*#",
    "datacard*.txt",
    "shapes/*"
]

for pattern in stray_patterns:
    target_path = os.path.join(script_dir, pattern)
    matched_paths = glob.glob(target_path)
    
    for path in matched_paths:
        if os.path.exists(path):
            print(f">> Removing: {path}")
            subprocess.run(["rm", "-rf", path])

print("Done.")
