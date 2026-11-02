from pathlib import Path
import zipfile
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

raw_dir = base / "Data" / "Raw"
files = [
    raw_dir / "faers_ascii_2026q1.zip",
    raw_dir / "faers_ascii_2026q2.zip",
]

for zip_path in files:
    print(f"\nChecking: {zip_path.name}")

    if not zip_path.exists():
        print("ZIP NOT FOUND")
        continue

    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()

        delete_files = [
            name for name in names
            if "DELETE" in name.upper()
            and not name.endswith("/")
        ]
        demo_files = [
            name for name in names
            if "DEMO" in name.upper() and name.lower().endswith(".txt")
        ]

        print("DELETE files:", delete_files)
        print("DEMO files:", demo_files)

        if not delete_files or not demo_files:
            print("Required file missing; skipping.")
            continue

        delete_df = pd.read_csv(
            z.open(delete_files[0]),
            sep="$",
            header=None,
            dtype=str,
        )
        delete_ids = set(
            delete_df.iloc[:, 0].dropna().str.strip()
        )

        demo_df = pd.read_csv(
            z.open(demo_files[0]),
            sep="$",
            dtype=str,
            low_memory=False,
        )
        demo_df.columns = demo_df.columns.str.strip().str.lower()

        print("DELETE identifiers:", len(delete_ids))
        print("DEMO rows:", len(demo_df))
        print("CASEID matches in this quarter:",
              demo_df["caseid"].str.strip().isin(delete_ids).sum())
        print("PRIMARYID matches in this quarter:",
              demo_df["primaryid"].str.strip().isin(delete_ids).sum())

        print("Sample DELETE identifiers:", list(delete_ids)[:5])