from pathlib import Path
import zipfile
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

raw_dir = base / "Data" / "Raw"
zip_names = [
    "faers_ascii_2026q1.zip",
    "faers_ascii_2026q2.zip",
]

all_delete_ids = set()
all_demo = []

for zip_name in zip_names:
    with zipfile.ZipFile(raw_dir / zip_name) as z:
        names = z.namelist()

        delete_file = next(
            n for n in names
            if "DELETE" in n.upper()
            and not n.endswith("/")
        )
        demo_file = next(
            n for n in names
            if "/DEMO" in n.upper()
            and n.lower().endswith(".txt")
        )

        delete_df = pd.read_csv(
            z.open(delete_file),
            sep="$",
            header=None,
            dtype=str,
        )

        all_delete_ids.update(
            delete_df.iloc[:, 0].dropna().str.strip()
        )

        demo = pd.read_csv(
            z.open(demo_file),
            sep="$",
            dtype=str,
            low_memory=False,
        )
        demo.columns = demo.columns.str.strip().str.lower()
        all_demo.append(demo)

combined = pd.concat(all_demo, ignore_index=True)
combined["caseid"] = combined["caseid"].str.strip()
combined["caseversion"] = pd.to_numeric(
    combined["caseversion"], errors="coerce"
)

matched = combined[
    combined["caseid"].isin(all_delete_ids)
].copy()

print("Combined DEMO rows:", len(combined))
print("Unique DELETE IDs:", len(all_delete_ids))
print("Matching DEMO rows:", len(matched))
print("Unique matched CASEIDs:", matched["caseid"].nunique())

print("\nMatched rows by quarter source:")
print(matched.groupby("primaryid").size().describe())

print("\nMatched cases with multiple versions:")
versions = matched.groupby("caseid")["caseversion"].agg(
    ["count", "max"]
)
print(versions[versions["count"] > 1].head(20).to_string())