
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd


# =========================================================
# 1. PATHS AND SETTINGS
# =========================================================

BASE_DIR = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project"
)

RAW_DIR = BASE_DIR / "Data" / "Raw"
OUTPUT_DIR = BASE_DIR / "pipeline_v2" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

QUARTERS = [
    RAW_DIR / "faers_ascii_2026q1.zip",
    RAW_DIR / "faers_ascii_2026q2.zip",
]

# Assumption: DELETE file identifiers are CASEIDs.
# Verify this against the official documentation for these files.
DELETE_ID_FIELD = "caseid"

OUTPUT_CSV_NAME = "faers_ror_signals_v7.csv"
OUTPUT_SUMMARY_NAME = "pipeline_summary_v7.txt"


# =========================================================
# 2. READ FAERS TABLES
# =========================================================

def read_table(zip_file, table):
    quarter = "26Q1" if "q1" in zip_file.name.lower() else "26Q2"
    target = f"{table}{quarter}.TXT"

    with ZipFile(zip_file, "r") as archive:
        member = next(
            (
                name for name in archive.namelist()
                if name.upper().endswith("/" + target)
            ),
            None,
        )

        if member is None:
            raise FileNotFoundError(
                f"{target} not found in {zip_file.name}"
            )

        with archive.open(member) as file:
            df = pd.read_csv(
                file,
                sep="$",
                dtype=str,
                encoding="latin-1",
                on_bad_lines="skip",
                low_memory=False,
            )

    df.columns = [column.strip().lower() for column in df.columns]
    return df


def read_deleted_ids(zip_file):
    """Read identifiers from the headerless DELETE text file."""

    with ZipFile(zip_file, "r") as archive:
        members = [
            name for name in archive.namelist()
            if "DELETE" in Path(name).name.upper()
            and name.upper().endswith(".TXT")
        ]

        if not members:
            print("WARNING: No DELETE file found in", zip_file.name)
            return set()

        if len(members) > 1:
            raise ValueError(
                f"Multiple DELETE files found in {zip_file.name}: {members}"
            )

        with archive.open(members[0]) as file:
            deleted = pd.read_csv(
                file,
                sep="$",
                header=None,
                dtype=str,
                encoding="latin-1",
                on_bad_lines="skip",
            )

    if deleted.empty:
        return set()

    values = (
        deleted.iloc[:, 0]
        .dropna()
        .astype(str)
        .str.strip()
    )

    return set(values[values.ne("")])


# =========================================================
# 3. LOAD Q1 + Q2 DATA
# =========================================================

demo_parts = []
drug_parts = []
reaction_parts = []
deleted_ids = set()

for zip_file in QUARTERS:
    if not zip_file.exists():
        raise FileNotFoundError(
            f"FAERS ZIP file not found: {zip_file}"
        )

    print(f"\nReading {zip_file.name} ...")

    demo_parts.append(read_table(zip_file, "DEMO"))
    drug_parts.append(read_table(zip_file, "DRUG"))
    reaction_parts.append(read_table(zip_file, "REAC"))

    quarter_deleted_ids = read_deleted_ids(zip_file)
    deleted_ids.update(quarter_deleted_ids)

    print("DELETE IDs in this ZIP:", len(quarter_deleted_ids))

demo = pd.concat(demo_parts, ignore_index=True)
drug = pd.concat(drug_parts, ignore_index=True)
reac = pd.concat(reaction_parts, ignore_index=True)

print("\nRaw DEMO rows:", len(demo))
print("Raw DRUG rows:", len(drug))
print("Raw REAC rows:", len(reac))
print("Unique DELETE IDs:", len(deleted_ids))


# =========================================================
# 4. CLEAN IDS, DEDUPLICATE, THEN FILTER DELETE CASEIDS
# =========================================================

required_demo_columns = {"primaryid", "caseid", "caseversion"}
missing_columns = required_demo_columns - set(demo.columns)

if missing_columns:
    raise ValueError(
        f"DEMO table is missing columns: {sorted(missing_columns)}"
    )

if DELETE_ID_FIELD != "caseid":
    raise ValueError(
        "This V5 script expects DELETE_ID_FIELD='caseid'. "
        "Verify the official DELETE file identifier definition first."
    )

# Clean report identifiers consistently.
for df in (demo, drug, reac):
    for column in ("primaryid", "caseid"):
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .replace("", pd.NA)
            )

demo = demo.dropna(subset=["primaryid", "caseid"]).copy()

# Convert CASEVERSION to numeric before sorting.
demo["caseversion_num"] = pd.to_numeric(
    demo["caseversion"], errors="coerce"
).fillna(-1)

# Sort by CASEID, version, then PRIMARYID for deterministic tie handling.
demo = demo.sort_values(
    ["caseid", "caseversion_num", "primaryid"]
)

# Keep the latest available version of each CASEID.
latest_demo = demo.drop_duplicates(
    subset=["caseid"],
    keep="last",
).copy()

print(
    "\nLatest unique CASEIDs before DELETE filtering:",
    latest_demo["caseid"].nunique(),
)

# Filter DELETE identifiers after case-version deduplication.
deleted_mask = latest_demo["caseid"].isin(deleted_ids)

print(
    "Latest cases matching DELETE IDs:",
    int(deleted_mask.sum()),
)

latest_demo = latest_demo.loc[~deleted_mask].copy()

# The retained PRIMARYIDs define the report universe for DRUG and REAC.
valid_ids = set(latest_demo["primaryid"].dropna())

drug = drug.loc[drug["primaryid"].isin(valid_ids)].copy()
reac = reac.loc[reac["primaryid"].isin(valid_ids)].copy()

N = latest_demo["primaryid"].nunique()

if N == 0:
    raise ValueError("No retained reports after DELETE filtering.")

if latest_demo["primaryid"].duplicated().any():
    raise ValueError(
        "Duplicate PRIMARYIDs found in latest DEMO. "
        "Investigate source records before continuing."
    )

print("Latest retained cases:", latest_demo["caseid"].nunique())
print("Retained report IDs (N):", N)


# =========================================================
# 5. BUILD REPORT-LEVEL DRUG AND REACTION SETS
# =========================================================

if "drugname" not in drug.columns:
    raise ValueError("DRUG table is missing DRUGNAME.")

if "prod_ai" not in drug.columns:
    drug["prod_ai"] = ""

# Prefer active ingredient when populated; otherwise use DRUGNAME.
preferred = drug["prod_ai"].fillna("").astype(str).str.strip()
fallback = drug["drugname"].fillna("").astype(str).str.strip()

drug["drug_key"] = preferred.where(preferred.ne(""), fallback)

drug["drug_key"] = (
    drug["drug_key"]
    .str.upper()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

report_drugs = drug.loc[
    drug["primaryid"].notna() & drug["drug_key"].ne(""),
    ["primaryid", "drug_key"],
].drop_duplicates()

if "pt" not in reac.columns:
    raise ValueError("REAC table is missing PT.")

reac["reaction_key"] = (
    reac["pt"].fillna("").astype(str)
    .str.upper()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

report_reactions = reac.loc[
    reac["primaryid"].notna() & reac["reaction_key"].ne(""),
    ["primaryid", "reaction_key"],
].drop_duplicates()

# Reports containing each drug and each reaction.
drug_counts = (
    report_drugs.groupby("drug_key")["primaryid"]
    .nunique()
    .rename("drug_reports")
)

reaction_counts = (
    report_reactions.groupby("reaction_key")["primaryid"]
    .nunique()
    .rename("reaction_reports")
)

# Reports containing both the drug and reaction.
pairs = report_drugs.merge(
    report_reactions,
    on="primaryid",
    how="inner",
)

pairs = pairs.drop_duplicates(
    ["primaryid", "drug_key", "reaction_key"]
)

pair_counts = (
    pairs.groupby(["drug_key", "reaction_key"])["primaryid"]
    .nunique()
    .rename("a")
    .reset_index()
)

pair_counts["drug_reports"] = pair_counts["drug_key"].map(drug_counts)
pair_counts["reaction_reports"] = pair_counts["reaction_key"].map(
    reaction_counts
)

if pair_counts.empty:
    raise ValueError(
        "No drug-reaction pairs were created. Check source data."
    )


# =========================================================
# 6. BUILD 2x2 CONTINGENCY TABLE
# =========================================================
#
#                         Reaction present   Reaction absent
# Drug present                    a                  b
# Drug absent                     c                  d
#
# a = reports with this drug AND this reaction
# b = reports with this drug but NOT this reaction
# c = reports with this reaction but NOT this drug
# d = reports with neither this drug nor this reaction
# N = total retained reports in the analysis cohort
# =========================================================

pair_counts["b"] = (
    pair_counts["drug_reports"] - pair_counts["a"]
)

pair_counts["c"] = (
    pair_counts["reaction_reports"] - pair_counts["a"]
)

pair_counts["d"] = (
    N
    - pair_counts["a"]
    - pair_counts["b"]
    - pair_counts["c"]
)

cell_columns = ["a", "b", "c", "d"]

if pair_counts[cell_columns].isna().any().any():
    raise ValueError("Missing values found in contingency-table cells.")

if (pair_counts[cell_columns] < 0).any().any():
    raise ValueError("Negative contingency-table cell found.")

if (pair_counts["a"] > pair_counts["drug_reports"]).any():
    raise ValueError("a exceeds drug_reports.")

if (pair_counts["a"] > pair_counts["reaction_reports"]).any():
    raise ValueError("a exceeds reaction_reports.")

if (pair_counts["drug_reports"] > N).any():
    raise ValueError("drug_reports exceeds N.")

if (pair_counts["reaction_reports"] > N).any():
    raise ValueError("reaction_reports exceeds N.")

# Check cell identities.
if not (
    pair_counts["a"] + pair_counts["b"]
    == pair_counts["drug_reports"]
).all():
    raise ValueError("Drug total identity check failed.")

if not (
    pair_counts["a"] + pair_counts["c"]
    == pair_counts["reaction_reports"]
).all():
    raise ValueError("Reaction total identity check failed.")

if not (
    pair_counts["a"] + pair_counts["b"]
    + pair_counts["c"] + pair_counts["d"] == N
).all():
    raise ValueError("Cohort total identity check failed.")

print("\nContingency-table validation passed.")
print("Number of drug-reaction pairs:", len(pair_counts))
print("Pairs with a = 0:", int((pair_counts["a"] == 0).sum()))
print("Pairs with b = 0:", int((pair_counts["b"] == 0).sum()))
print("Pairs with c = 0:", int((pair_counts["c"] == 0).sum()))
print("Pairs with d = 0:", int((pair_counts["d"] == 0).sum()))


# =========================================================
# 7. CALCULATE ROR AND 95% CONFIDENCE INTERVAL
# =========================================================

# Haldane-Anscombe correction: add 0.5 to each cell.
a_adj = pair_counts["a"].astype(float) + 0.5
b_adj = pair_counts["b"].astype(float) + 0.5
c_adj = pair_counts["c"].astype(float) + 0.5
d_adj = pair_counts["d"].astype(float) + 0.5

pair_counts["ROR"] = (
    (a_adj * d_adj) / (b_adj * c_adj)
)

pair_counts["log_ROR"] = np.log(pair_counts["ROR"])

pair_counts["SE_log_ROR"] = np.sqrt(
    (1 / a_adj)
    + (1 / b_adj)
    + (1 / c_adj)
    + (1 / d_adj)
)

pair_counts["ROR_CI_lower"] = np.exp(
    pair_counts["log_ROR"] - 1.96 * pair_counts["SE_log_ROR"]
)

pair_counts["ROR_CI_upper"] = np.exp(
    pair_counts["log_ROR"] + 1.96 * pair_counts["SE_log_ROR"]
)

# =========================================================
# 7A. V6 EXPLORATORY SIGNAL SCREENING AND RANKING
# =========================================================

MIN_CASES = 5

pair_counts["potential_signal"] = (
    (pair_counts["a"] >= MIN_CASES)
    & (pair_counts["b"] > 0)
    & (pair_counts["c"] > 0)
    & (pair_counts["ROR_CI_lower"] > 1)
)

pair_counts = pair_counts.sort_values(
    ["potential_signal", "ROR_CI_lower", "a"],
    ascending=[False, False, False],
).reset_index(drop=True)

# =========================================================
# 7B. V6 NUMERICAL VALIDATION
# =========================================================

for column in ["ROR", "ROR_CI_lower", "ROR_CI_upper"]:
    if not np.isfinite(pair_counts[column]).all():
        raise ValueError(f"Non-finite values found in {column}.")

if not (
    (pair_counts["ROR_CI_lower"] <= pair_counts["ROR_CI_upper"]).all()
):
    raise ValueError("Invalid ROR confidence interval bounds.")

print("V6 validation passed.")
print("Minimum co-reported cases:", MIN_CASES)
print(
    "V6 exploratory candidates:",
    int(pair_counts["potential_signal"].sum()),
)

# =========================================================
# 8. SAVE NEW V6 OUTPUT FILES ONLY
# =========================================================

csv_path = OUTPUT_DIR / OUTPUT_CSV_NAME
summary_path = OUTPUT_DIR / OUTPUT_SUMMARY_NAME

# Do not overwrite an existing V5 result.
if csv_path.exists() or summary_path.exists():
    raise FileExistsError(
        "V6 output already exists. Rename or back up existing V6 files "
        "before running this script again."
    )
pair_counts.to_csv(csv_path, index=False)

summary = (
    "Source: FAERS 2026 Q1 + Q2\n"
    "Processing order: latest CASEVERSION per CASEID, then DELETE filter\n"
    f"DELETE identifier field assumed: {DELETE_ID_FIELD}\n"
    f"Unique DELETE IDs listed: {len(deleted_ids)}\n"
    f"Latest unique CASEIDs before DELETE filter: {demo['caseid'].nunique()}\n"
    f"Latest cases matching DELETE IDs: {int(deleted_mask.sum())}\n"
    f"Latest retained cases: {latest_demo['caseid'].nunique()}\n"
    f"Retained report IDs (N): {N}\n"
    f"Unique drug keys: {report_drugs['drug_key'].nunique()}\n"
    f"Unique reaction terms: {report_reactions['reaction_key'].nunique()}\n"
    f"Drug-reaction pairs: {len(pair_counts)}\n"
    f"Pairs with a >= 3: {int((pair_counts['a'] >= 3).sum())}\n"
    f"Minimum co-reported cases for V6 screening: {MIN_CASES}\n"
    f"V6 exploratory potential signals: {int(pair_counts['potential_signal'].sum())}\n"
    "Drug role definition: all recorded roles\n"
    "Interpretation: exploratory disproportionality screening only\n"
    "Limitations: reporting bias, confounding, duplicates and incomplete reports\n"
    "Signals do not establish causality or incidence.\n"
    f"Output CSV: {csv_path}\n"
)

summary_path.write_text(summary, encoding="utf-8")

print("\nPipeline completed.")
print("CSV:", csv_path)
print("Summary:", summary_path)
print("\nTop 10 results:")
print(pair_counts.head(10).to_string(index=False))
