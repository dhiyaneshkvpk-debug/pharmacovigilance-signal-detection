
from pathlib import Path
from zipfile import ZipFile

# Original FAERS ZIP files
data_folder = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw"
)

zip_files = [
    data_folder / "faers_ascii_2026q1.zip",
    data_folder / "faers_ascii_2026q2.zip",
]

for zip_path in zip_files:
    print("\n" + "=" * 60)
    print(f"Checking: {zip_path.name}")

    if not zip_path.exists():
        print("NOT FOUND - Check the file path.")
        continue

    print(f"File size: {zip_path.stat().st_size / (1024 * 1024):.2f} MB")

    try:
        with ZipFile(zip_path, "r") as archive:
            files = archive.namelist()
            print("\nFiles inside ZIP:")

            for name in files:
                if name.lower().endswith((".txt", ".csv")):
                    print(" -", name)

            print(f"\nTotal files in ZIP: {len(files)}")

    except Exception as error:
        print("Could not read ZIP:", error)

print("\nCheck complete.")
