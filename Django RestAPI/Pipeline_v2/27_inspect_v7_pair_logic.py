from pathlib import Path
import runpy
script = Path("Pipeline_v2/22_build_faers_pipeline_v7.py")
if not script.exists():
    raise FileNotFoundError(script)
# First inspect the existing output and key processing code without rerunning V7.
text = script.read_text(encoding="utf-8-sig").splitlines()
for start, end in [(230, 310), (310, 345)]:
    print(f"\n--- V7 lines {start}-{end} ---")
    for i in range(start - 1, min(end, len(text))):
        print(f"{i+1}: {text[i]}")
