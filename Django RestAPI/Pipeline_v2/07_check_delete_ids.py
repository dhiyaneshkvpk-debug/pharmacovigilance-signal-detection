
from pathlib import Path
from zipfile import ZipFile
import pandas as pd

base_dir = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project"
)

zip_paths = [
    base_dir / "Data" / "Raw" / "faers_ascii_2026q1.zip",
    base_dir / "Data" / "Raw" / "faers_ascii_2026q2.zip",
]

all_deleted = set()
all_caseids = set()
all_primaryids = set()

for zip_path in zip_paths:
    quarter = "26Q1" if "q1" in zip_path.name.lower() else "26Q2"

    with ZipFile(zip_path) as archive:
        demo_name = next(
            n for n in archive.namelist()
            if n.upper().endswith(f"/DEMO{quarter}.TXT")
        )
        delete_name = next(
            n for n in archive.namelist()
            if "DELETE" in n.upper() and n.upper().endswith(".TXT")
        )

        with archive.open(demo_name) as f:
            demo = pd.read_csv(
                f, sep="$", dtype=str, encoding="latin-1",
                on_bad_lines="skip", low_memory=False
            )

        with archive.open(delete_name) as f:
            deleted = pd.read_csv(
                f, sep="$", header=None, dtype=str,
                encoding="latin-1", on_bad_lines="skip"
            )

    demo.columns = [c.strip().lower() for c in demo.columns]

    all_caseids.update(
        demo["caseid"].dropna().astype(str).str.strip()
    )
    all_primaryids.update(
        demo["primaryid"].dropna().astype(str).str.strip()
    )
    all_deleted.update(
        deleted.iloc[:, 0].dropna().astype(str).str.strip()
    )

print("Unique DELETE IDs:", len(all_deleted))
print("Matching CASEID:", len(all_deleted & all_caseids))
print("Matching PRIMARYID:", len(all_deleted & all_primaryids))