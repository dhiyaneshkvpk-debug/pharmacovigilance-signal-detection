from pathlib import Path
from zipfile import ZipFile
from pypdf import PdfReader
import io
base = Path(r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw")
for filename in ["faers_ascii_2026q1.zip", "faers_ascii_2026q2.zip"]:
    print("\n==========", filename, "==========")
    with ZipFile(base / filename) as z:
        pdf_name = next(n for n in z.namelist()
                        if Path(n).name.lower() == "faqs.pdf")
        reader = PdfReader(io.BytesIO(z.read(pdf_name)))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "What is this used for?" in line:
                print("\n".join(lines[max(0, i-2):min(len(lines), i+18)]))
                break
