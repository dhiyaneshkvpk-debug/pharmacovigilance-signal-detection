from pathlib import Path
from zipfile import ZipFile
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

zip_paths = [
    base / "Data" / "Raw" / "faers_ascii_2026q1.zip",
    base / "Data" / "Raw" / "faers_ascii_2026q2.zip",
]

all_delete_ids = set()
all_caseids = set()
all_primaryids = set()

for path in zip_paths:
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
                f, sep="$", dtype=str, encoding="latin-1",
                on_bad_lines="skip", low_memory=False
            )

        with z.open(delete_name) as f:
            deleted = pd.read_csv(
                f, sep="$", header=None, dtype=str,
                encoding="latin-1", on_bad_lines="skip"
            )

    demo.columns = [c.strip().lower() for c in demo.columns]

    ids = set(deleted.iloc[:, 0].dropna().str.strip())
    cases = set(demo["caseid"].dropna().str.strip())
    primary = set(demo["primaryid"].dropna().str.strip())

    print(f"\n--- {quarter} ---")
    print("DEMO file:", demo_name)
    print("DELETE file:", delete_name)
    print("DEMO columns:", demo.columns.tolist())
    print("DEMO rows:", len(demo))
    print("DELETE sample rows:")
    print(deleted.head(5).to_string(index=False, header=False))
    print("CASEID matches within quarter:", len(ids & cases))
    print("PRIMARYID matches within quarter:", len(ids & primary))

    all_delete_ids.update(ids)
    all_caseids.update(cases)
    all_primaryids.update(primary)

print("\n--- COMBINED CHECK ---")
print("Unique DELETE IDs:", len(all_delete_ids))
print("Unique CASEIDs:", len(all_caseids))
print("Unique PRIMARYIDs:", len(all_primaryids))
print("Combined CASEID matches:", len(all_delete_ids & all_caseids))
print("Combined PRIMARYID matches:", len(all_delete_ids & all_primaryids))