from pathlib import Path
import zipfile
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

raw_dir = base / "Data" / "Raw"
demo_parts = []
delete_ids = set()

for zip_name in [
    "faers_ascii_2026q1.zip",
    "faers_ascii_2026q2.zip",
]:
    with zipfile.ZipFile(raw_dir / zip_name) as z:
        names = z.namelist()

        delete_file = next(
            n for n in names
            if "DELETE" in n.upper() and not n.endswith("/")
        )
        demo_file = next(
            n for n in names
            if "/DEMO" in n.upper()
            and n.lower().endswith(".txt")
        )

        deleted = pd.read_csv(
            z.open(delete_file),
            sep="$",
            header=None,
            dtype=str,
        )
        delete_ids.update(
            deleted.iloc[:, 0].dropna().str.strip()
        )

        demo = pd.read_csv(
            z.open(demo_file),
            sep="$",
            dtype=str,
            low_memory=False,
        )
        demo.columns = demo.columns.str.strip().str.lower()
        demo["caseid"] = demo["caseid"].str.strip()
        demo["caseversion_num"] = pd.to_numeric(
            demo["caseversion"], errors="coerce"
        )
        demo_parts.append(demo)

combined = pd.concat(demo_parts, ignore_index=True)

# Keep latest version per CASEID for this comparison.
latest = (
    combined.sort_values(
        ["caseid", "caseversion_num", "primaryid"],
        na_position="first",
    )
    .drop_duplicates("caseid", keep="last")
)

matches_before = combined["caseid"].isin(delete_ids).sum()
matches_after = latest["caseid"].isin(delete_ids).sum()

print("Combined DEMO rows:", len(combined))
print("Latest unique CASEIDs:", len(latest))
print("DELETE matches before dedup:", matches_before)
print("DELETE matches after dedup:", matches_after)
print("Latest cases remaining after DELETE filter:",
      len(latest) - matches_after)