from pathlib import Path
from zipfile import ZipFile
import pandas as pd
RAW_DIR = Path("../Data/Raw")
FILES = [
    RAW_DIR / "faers_ascii_2026q1.zip",
    RAW_DIR / "faers_ascii_2026q2.zip",
]
def read_table(zip_path, prefix):
    with ZipFile(zip_path) as z:
        names = [
            n for n in z.namelist()
            if Path(n).name.upper().startswith(prefix)
            and n.lower().endswith(".txt")
        ]
        if not names:
            raise FileNotFoundError(f"{prefix} file missing in {zip_path}")
        with z.open(names[0]) as f:
            df = pd.read_csv(
                f, sep="$", dtype=str, low_memory=False,
                encoding="latin1", on_bad_lines="warn"
            )
    df.columns = [c.strip().upper() for c in df.columns]
    return df
drug_frames, reac_frames = [], []
for path in FILES:
    print(f"Reading {path.name} ...")
    drug_frames.append(read_table(path, "DRUG"))
    reac_frames.append(read_table(path, "REAC"))
drugs = pd.concat(drug_frames, ignore_index=True).fillna("")
reac = pd.concat(reac_frames, ignore_index=True).fillna("")
required_drug = {"PRIMARYID", "CASEID", "ROLE_COD", "DRUGNAME", "PROD_AI"}
required_reac = {"PRIMARYID", "CASEID", "PT"}
if not required_drug.issubset(drugs.columns):
    raise ValueError(f"Missing DRUG columns: {required_drug - set(drugs.columns)}")
if not required_reac.issubset(reac.columns):
    raise ValueError(f"Missing REAC columns: {required_reac - set(reac.columns)}")
# Identify medroxyprogesterone acetate records using ingredient or brand/name.
ingredient = (
    drugs["PROD_AI"].str.contains("MEDROXYPROGESTERONE ACETATE", case=False, na=False)
    | drugs["DRUGNAME"].str.contains("DEPO-PROVERA", case=False, na=False)
)
med = drugs.loc[ingredient].copy()
# Identify reports with a reaction term containing MENINGIOMA.
men = reac.loc[
    reac["PT"].str.contains("MENINGIOMA", case=False, na=False),
    ["PRIMARYID", "CASEID", "PT"]
].drop_duplicates()
med["ROLE_COD"] = med["ROLE_COD"].str.upper().str.strip()
med_reports = set(med["PRIMARYID"])
men_reports = set(men["PRIMARYID"])
overlap = med_reports & men_reports
def report_summary(label, drug_rows):
    ids = set(drug_rows["PRIMARYID"])
    matched = ids & men_reports
    print(f"\n{label}")
    print(f"  Drug rows: {len(drug_rows):,}")
    print(f"  Unique report IDs (PRIMARYID): {len(ids):,}")
    print(f"  Unique case IDs (CASEID): {drug_rows['CASEID'].nunique():,}")
    print(f"  Reports also containing a meningioma reaction: {len(matched):,}")
print("\n=== RAW FAERS AUDIT: MEDROXYPROGESTERONE / MENINGIOMA ===")
report_summary("All identified drug roles", med)
report_summary("Primary-suspect (PS) role only", med[med["ROLE_COD"] == "PS"])
print("\nMeningioma reaction terms in overlapping reports:")
if overlap:
    print(
        men[men["PRIMARYID"].isin(overlap)]["PT"]
        .value_counts().head(15).to_string()
    )
else:
    print("No overlapping PRIMARYIDs found.")
print("\nImportant: these are co-reported FAERS records, not proof of causation.")
