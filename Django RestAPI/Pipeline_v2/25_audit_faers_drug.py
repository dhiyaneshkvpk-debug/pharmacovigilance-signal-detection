import zipfile
import pandas as pd
from pathlib import Path
RAW_DIR = Path("../Data/Raw")
ZIP_FILES = [
    RAW_DIR / "faers_ascii_2026q1.zip",
    RAW_DIR / "faers_ascii_2026q2.zip",
]
TARGETS = ["SOAP", "GUANIDINE", "MEDROXYPROGESTERONE ACETATE"]
def audit_zip(zip_path):
    print(f"\n{'=' * 70}\nChecking: {zip_path}")
    if not zip_path.exists():
        print(f"ZIP NOT FOUND: {zip_path.resolve()}")
        return
    with zipfile.ZipFile(zip_path) as zf:
        drug_files = [
            name for name in zf.namelist()
            if Path(name).name.upper().startswith("DRUG") and Path(name).suffix.lower() == ".txt"
        ]
        if not drug_files:
            print("DRUG.TXT not found inside ZIP")
            return
        for drug_file in drug_files:
            print(f"Reading {drug_file}")
            count = 0
            with zf.open(drug_file) as f:
                for chunk in pd.read_csv(
                    f, sep="$", dtype=str, encoding="latin-1",
                    on_bad_lines="skip", chunksize=100000
                ):
                    chunk.columns = [str(c).strip().upper() for c in chunk.columns]
                    for col in ["DRUGNAME", "PROD_AI"]:
                        if col not in chunk.columns:
                            chunk[col] = ""
                    mask = pd.Series(False, index=chunk.index)
                    for target in TARGETS:
                        mask |= (
                            chunk["DRUGNAME"].fillna("").str.upper().str.contains(target, regex=False)
                            | chunk["PROD_AI"].fillna("").str.upper().str.contains(target, regex=False)
                        )
                    matches = chunk.loc[mask]
                    if not matches.empty:
                        cols = [
                            c for c in ["PRIMARYID", "CASEID", "ROLE_COD", "DRUGNAME", "PROD_AI"]
                            if c in matches.columns
                        ]
                        print(matches[cols].to_string(index=False))
                        count += len(matches)
            print(f"Matching rows: {count}")
def main():
    print("FAERS RAW DRUG AUDIT STARTED")
    for path in ZIP_FILES:
        audit_zip(path)
    print("\nFAERS RAW DRUG AUDIT FINISHED")
if __name__ == "__main__":
    main()
