
import zipfile
import pandas as pd
from pathlib import Path

RAW_DIR = Path("Data/Raw")

ZIP_FILES = [
    RAW_DIR / "faers_ascii_2026q1.zip",
    RAW_DIR / "faers_ascii_2026q2.zip",
]

TARGETS = [
    "SOAP",
    "GUANIDINE",
    "MEDROXYPROGESTERONE ACETATE",
]


def audit_zip(zip_path):
    print(f"\n{'=' * 70}")
    print(f"Checking: {zip_path}")

    if not zip_path.exists():
        print(f"ERROR: ZIP file not found: {zip_path.resolve()}")
        return

    with zipfile.ZipFile(zip_path, "r") as zf:
        drug_files = [
            name for name in zf.namelist()
            if Path(name).name.upper() == "DRUG.TXT"
        ]

        if not drug_files:
            print("ERROR: DRUG.TXT not found inside this ZIP.")
            return

        for drug_file in drug_files:
            print(f"Reading: {drug_file}")
            found = 0

            with zf.open(drug_file) as file:
                for chunk in pd.read_csv(
                    file,
                    sep="$",
                    dtype=str,
                    encoding="latin-1",
                    on_bad_lines="skip",
                    chunksize=100_000,
                ):
                    chunk.columns = [
                        str(col).strip().upper()
                        for col in chunk.columns
                    ]

                    for col in ["DRUGNAME", "PROD_AI"]:
                        if col not in chunk.columns:
                            chunk[col] = ""

                    mask = pd.Series(False, index=chunk.index)

                    for target in TARGETS:
                        mask |= (
                            chunk["DRUGNAME"].fillna("").str.upper()
                            .str.contains(target, regex=False)
                            |
                            chunk["PROD_AI"].fillna("").str.upper()
                            .str.contains(target, regex=False)
                        )

                    matches = chunk.loc[mask].copy()

                    if not matches.empty:
                        columns = [
                            col for col in [
                                "PRIMARYID",
                                "CASEID",
                                "ROLE_COD",
                                "DRUGNAME",
                                "PROD_AI",
                            ]
                            if col in matches.columns
                        ]

                        print(matches[columns].to_string(index=False))
                        found += len(matches)

            print(f"Matching rows found in this file: {found}")


def main():
    print("FAERS RAW DRUG AUDIT STARTED")
    print("Searching for SOAP, GUANIDINE, and "
          "MEDROXYPROGESTERONE ACETATE.")

    for zip_path in ZIP_FILES:
        audit_zip(zip_path)

    print("\nFAERS RAW DRUG AUDIT FINISHED")


if __name__ == "__main__":
    main()
