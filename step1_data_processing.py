"""
STEP 1 - DATA PROCESSING
------------------------
Reads the raw FAERS zip files (put them in data/raw/) and cleans them.

What we do:
  1. Read 3 tables from each zip:  DEMO (patient), DRUG (drugs), REAC (reactions)
  2. Remove cases the FDA has deleted
  3. Keep only the LATEST version of each case (reports get updated)
  4. Keep only the PRIMARY SUSPECT drug (role_cod = PS)
  5. Clean text (upper-case, remove spaces), convert age to years
  6. Save clean tables in data/processed/

Run:  python step1_data_processing.py
"""
import re
import zipfile
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
RAW_FOLDER = BASE / "data" / "raw"
OUT_FOLDER = BASE / "data" / "processed"
OUT_FOLDER.mkdir(parents=True, exist_ok=True)

AGE_UNITS = {"YR": 1, "DEC": 10, "MON": 1 / 12, "WK": 7 / 365.25, "DY": 1 / 365.25, "HR": 1 / 8766}


def read_table(zip_file, prefix, columns, only_primary_suspect=False):
    """Read one table (DEMO / DRUG / REAC) from inside the zip file."""
    # find the .txt file whose name starts with the prefix, e.g. ASCII/DEMO26Q1.txt
    name = [n for n in zip_file.namelist()
            if Path(n).name.upper().startswith(prefix) and n.lower().endswith(".txt")][0]
    pieces = []
    with zip_file.open(name) as f:
        # The DRUG file is big, so we read it in chunks of 400,000 rows to save memory
        for chunk in pd.read_csv(f, sep="$", dtype=str, quoting=3, on_bad_lines="skip",
                                 encoding_errors="replace", chunksize=400_000,
                                 usecols=lambda c: c.lower() in columns):
            chunk.columns = chunk.columns.str.lower()
            if only_primary_suspect:
                chunk = chunk[chunk["role_cod"] == "PS"]
            pieces.append(chunk)
    return pd.concat(pieces, ignore_index=True)


def clean_text(series):
    """UPPER CASE, remove extra spaces."""
    return series.fillna("").str.upper().str.replace(r"\s+", " ", regex=True).str.strip()


all_cases, all_drugs, all_reactions, deleted_ids = [], [], [], set()
quality = []   # we collect row counts to prove the cleaning worked

zip_files = sorted(RAW_FOLDER.glob("faers_ascii_*.zip"))
if not zip_files:
    raise SystemExit(f"No zip files found in {RAW_FOLDER}. Copy faers_ascii_2026q1.zip etc. there.")

for zip_path in zip_files:
    quarter = zip_path.stem.split("_")[-1]          # 'faers_ascii_2026q1' -> '2026q1'
    print(f"Reading {zip_path.name} ...")
    with zipfile.ZipFile(zip_path) as z:
        demo = read_table(z, "DEMO", {"primaryid", "caseid", "caseversion", "fda_dt", "age", "age_cod", "sex"})
        drug = read_table(z, "DRUG", {"primaryid", "role_cod", "drugname"}, only_primary_suspect=True)
        reac = read_table(z, "REAC", {"primaryid", "pt"})
        # FDA lists withdrawn case ids in a small 'Deleted' file
        for n in z.namelist():
            if Path(n).name.upper().startswith("DELETE") and n.lower().endswith(".txt"):
                deleted_ids |= {int(x) for x in re.findall(r"\d+", z.read(n).decode("utf-8", "replace"))}

    # ---- clean the DEMO table (patients) ----
    for col in ["primaryid", "caseid", "caseversion", "fda_dt"]:
        demo[col] = pd.to_numeric(demo[col], errors="coerce")
    demo = demo.dropna(subset=["primaryid", "caseid", "caseversion"])
    age = pd.to_numeric(demo["age"], errors="coerce")
    demo["age_years"] = age * demo["age_cod"].fillna("YR").str.upper().map(AGE_UNITS).fillna(1)
    demo.loc[(demo["age_years"] < 0) | (demo["age_years"] > 120), "age_years"] = None   # impossible ages
    demo["sex"] = demo["sex"].map({"M": "Male", "F": "Female"}).fillna("Unknown")
    demo["quarter"] = quarter

    # ---- clean the DRUG table ----
    drug["primaryid"] = pd.to_numeric(drug["primaryid"], errors="coerce")
    drug["drug"] = clean_text(drug["drugname"])
    drug = drug[~drug["drug"].isin(["", "UNKNOWN", "UNSPECIFIED", "NONE", "NA", "N/A"])]

    # ---- clean the REACTION table ----
    reac["primaryid"] = pd.to_numeric(reac["primaryid"], errors="coerce")
    reac["reaction"] = clean_text(reac["pt"])
    reac = reac[reac["reaction"] != ""]

    quality.append({"quarter": quarter, "raw_patient_rows": len(demo), "raw_ps_drug_rows": len(drug),
                    "raw_reaction_rows": len(reac)})
    all_cases.append(demo[["primaryid", "caseid", "caseversion", "fda_dt", "age_years", "sex", "quarter"]])
    all_drugs.append(drug[["primaryid", "drug"]])
    all_reactions.append(reac[["primaryid", "reaction"]])

# ---- combine the quarters ----
cases = pd.concat(all_cases, ignore_index=True)
drugs = pd.concat(all_drugs, ignore_index=True)
reactions = pd.concat(all_reactions, ignore_index=True)

# Remove cases the FDA deleted
cases = cases[~cases["caseid"].isin(deleted_ids)]

# Keep only the LATEST version of each case
cases = cases.sort_values(["caseid", "caseversion", "fda_dt"], ascending=[True, False, False])
cases = cases.drop_duplicates(subset="caseid", keep="first")

# Keep drugs / reactions only for the cases we kept, and remove exact duplicates
valid_ids = set(cases["primaryid"])
drugs = drugs[drugs["primaryid"].isin(valid_ids)].drop_duplicates()
reactions = reactions[reactions["primaryid"].isin(valid_ids)].drop_duplicates()

# Make ids whole numbers
for table in (cases, drugs, reactions):
    table["primaryid"] = table["primaryid"].astype("int64")
cases["caseid"] = cases["caseid"].astype("int64")

# ---- save ----
cases.to_csv(OUT_FOLDER / "cases.csv", index=False)
drugs.to_csv(OUT_FOLDER / "drugs.csv", index=False)
reactions.to_csv(OUT_FOLDER / "reactions.csv", index=False)

# ---- CHECKPOINTS: print proof that the cleaning worked ----
print("\n========== DATA PROCESSING RESULT ==========")
print(f"Patient rows read (all versions) : {sum(q['raw_patient_rows'] for q in quality):,}")
print(f"Unique cases after cleaning      : {len(cases):,}")
print(f"Deleted case ids removed         : {len(deleted_ids):,}")
print(f"Drug rows (primary suspect only) : {len(drugs):,}")
print(f"Reaction rows                    : {len(reactions):,}")
print("\nCHECK 1 - every case appears only once :", cases["caseid"].is_unique)
print("CHECK 2 - every drug row belongs to a case :", drugs["primaryid"].isin(cases["primaryid"]).all())
print("CHECK 3 - ages are between 0 and 120 :", cases["age_years"].dropna().between(0, 120).all())
print("\nCases per quarter:\n", cases["quarter"].value_counts().sort_index().to_string())
print(f"\nSaved clean files in {OUT_FOLDER}")
