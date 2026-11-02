from pathlib import Path
from zipfile import ZipFile
from pypdf import PdfReader
import io
base = Path(r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw")
files = ["faers_ascii_2026q1.zip", "faers_ascii_2026q2.zip"]
keywords = ("DELETE", "CASEID", "CASEVERSION", "DELETED CASE")
for filename in files:
    print(f"\n{'=' * 70}\nZIP: {filename}\n{'=' * 70}")
    with ZipFile(base / filename) as z:
        pdfs = [
            name for name in z.namelist()
            if name.lower().endswith(".pdf")
            and any(k in Path(name).name.upper()
                    for k in ("README", "FAQ", "ASC_NTS"))
        ]
        for name in pdfs:
            print(f"\n--- DOCUMENT: {name} ---")
            reader = PdfReader(io.BytesIO(z.read(name)))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            lines = text.splitlines()
            hits = [i for i, line in enumerate(lines)
                    if any(k in line.upper() for k in keywords)]
            if not hits:
                print("No matching terms found in extracted text.")
            else:
                shown = set()
                for i in hits:
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        if j not in shown:
                            print(f"{j+1}: {lines[j]}")
                            shown.add(j)
                    print("---")
