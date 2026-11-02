
from pathlib import Path
from zipfile import ZipFile
import pandas as pd

raw_dir = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw"
)

zip_files = [
    raw_dir / "faers_ascii_2026q1.zip",
    raw_dir / "faers_ascii_2026q2.zip",
]

for zip_path in zip_files:
    print("\n" + "=" * 60)
    print("ZIP:", zip_path.name)

    with ZipFile(zip_path, "r") as archive:
        delete_files = [
            name for name in archive.namelist()
            if "DELETE" in name.upper() and name.upper().endswith(".TXT")
        ]

        for member in delete_files:
            print("\nDELETE file:", member)

            with archive.open(member) as file:
                df = pd.read_csv(
                    file,
                    sep="$",
                    dtype=str,
                    encoding="latin-1",
                    nrows=5,
                    on_bad_lines="skip",
                )

            print("Columns:", df.columns.tolist())
            print(df.head(3).to_string(index=False))

print("\nDELETE inspection complete.")
