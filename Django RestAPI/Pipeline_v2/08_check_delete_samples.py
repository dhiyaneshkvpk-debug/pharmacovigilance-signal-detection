from pathlib import Path
from zipfile import ZipFile
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

files = [
    base / "Data" / "Raw" / "faers_ascii_2026q1.zip",
    base / "Data" / "Raw" / "faers_ascii_2026q2.zip",
]

for path in files:
    quarter = "26Q1" if "q1" in path.name.lower() else "26Q2"

    with ZipFile(path) as z:
        demo_name = next(
            n for n in z.namelist()
            if n.upper().endswith(f"/DEMO{quarter}.TXT")
        )
        delete_name = next(
            n for n in z.namelist()
            if "DELETE" in n.upper() and n.upper().endswith(".TXT")
        )

        with z.open(demo_name) as f:
            demo = pd.read_csv(
                f, sep="$", dtype=str,
                encoding="latin-1", on_bad_lines="skip"
            )

        with z.open(delete_name) as f:
            deleted = pd.read_csv(
                f, sep="$", header=None, dtype=str,
                encoding="latin-1", on_bad_lines="skip"
            )

    demo.columns = [c.strip().lower() for c in demo.columns]

    delete_ids = set(
        deleted.iloc[:, 0].dropna().str.strip()
    )
    caseids = set(demo["caseid"].dropna().str.strip())
    primaryids = set(demo["primaryid"].dropna().str.strip())

    print(f"\n--- {quarter} ---")
    print("DELETE IDs:", len(delete_ids))
    print("CASEID matches:", len(delete_ids & caseids))
    print("PRIMARYID matches:", len(delete_ids & primaryids))
    print("Sample DELETE IDs:", list(sorted(delete_ids))[:10])
    print("Sample unmatched IDs:",
          list(sorted(delete_ids - caseids))[:10])