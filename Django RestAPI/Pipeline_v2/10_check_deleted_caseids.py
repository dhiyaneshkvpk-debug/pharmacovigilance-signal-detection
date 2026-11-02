from pathlib import Path
from zipfile import ZipFile
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

paths = [
    base / "Data" / "Raw" / "faers_ascii_2026q1.zip",
    base / "Data" / "Raw" / "faers_ascii_2026q2.zip",
]

deleted_ids = set()
demos = []

for path in paths:
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
    for col in ["primaryid", "caseid", "caseversion", "fda_dt"]:
        if col not in demo.columns:
            raise ValueError(f"Missing column: {col}")

    deleted_ids.update(deleted.iloc[:, 0].dropna().str.strip())
    demos.append(demo)

demo = pd.concat(demos, ignore_index=True)

for col in ["primaryid", "caseid", "caseversion", "fda_dt"]:
    demo[col] = demo[col].astype("string").str.strip()

print("Combined DEMO rows:", len(demo))
print("Unique DELETE IDs:", len(deleted_ids))
print("DELETE IDs matching combined CASEID:",
      len(deleted_ids & set(demo["caseid"].dropna())))
print("DELETE IDs matching combined PRIMARYID:",
      len(deleted_ids & set(demo["primaryid"].dropna())))

# Preview rows belonging to deleted CASEIDs
matched = demo[demo["caseid"].isin(deleted_ids)]

print("DEMO rows with DELETE CASEIDs:", len(matched))
print("Distinct matching CASEIDs:", matched["caseid"].nunique())
print(matched[["primaryid", "caseid", "caseversion", "fda_dt"]]
      .head(20).to_string(index=False))