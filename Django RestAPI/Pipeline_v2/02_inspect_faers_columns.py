
from pathlib import Path
from zipfile import ZipFile
import pandas as pd

data_folder = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw"
)

zip_files = [
    data_folder / "faers_ascii_2026q1.zip",
    data_folder / "faers_ascii_2026q2.zip",
]

tables_to_check = ["DEMO", "DRUG", "REAC"]

for zip_path in zip_files:
    print("\n" + "=" * 70)
    print("QUARTER:", zip_path.name)

    with ZipFile(zip_path, "r") as archive:
        members = archive.namelist()

        for table in tables_to_check:
            member = next(
                (
                    name for name in members
                    if name.upper().endswith(f"/{table}{'26Q1' if 'q1' in zip_path.name.lower() else '26Q2'}.TXT")
                ),
                None,
            )

            if member is None:
                print(f"\n{table}: FILE NOT FOUND")
                continue

            with archive.open(member) as file:
                df = pd.read_csv(
                    file,
                    sep="$",
                    nrows=5,
                    dtype=str,
                    encoding="latin-1",
                    on_bad_lines="skip",
                )

            print(f"\n--- {table} ---")
            print("Columns:")
            print(df.columns.tolist())
            print("\nSample rows:")
            print(df.head(2).to_string(index=False))

print("\nInspection complete.")
