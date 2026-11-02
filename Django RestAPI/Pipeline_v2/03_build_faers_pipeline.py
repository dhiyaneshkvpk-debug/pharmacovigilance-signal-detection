
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

# Keep this as PRIMARYID unless the official DELETE file
# documentation for these exact archives specifies otherwise.
DELETE_ID_FIELD = "caseid"

# All drug roles are included consistently for this exploratory
# drug-event co-reporting analysis.
# This is not a causal analysis.
OUTPUT_CSV_NAME = "faers_ror_signals_v5.csv"
OUTPUT_SUMMARY_NAME = "pipeline_summary_v5.txt"

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
    """Read the headerless DELETE file as a set of identifiers."""

    with ZipFile(zip_file, "r") as archive:
        member = next(
            (
                name for name in archive.namelist()
                if "DELETE" in name.upper()
                and name.upper().endswith(".TXT")
            ),
            None,
        )

        if member is None:
            print("No DELETE file found in", zip_file.name)
            return set()

        with archive.open(member) as file:
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

    return set(
        deleted.iloc[:, 0]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda values: values.ne("")]
    )


# =========================================================
# 3. LOAD Q1 + Q2
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
# 4. CLEAN IDS, DEDUPLICATE CASES, THEN FILTER DELETED CASES
# =========================================================

for df in (demo, drug, reac):
    for column in ("primaryid", "caseid"):
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip()

required_demo_columns = {"primaryid", "caseid", "caseversion"}
missing_columns = required_demo_columns - set(demo.columns)

if missing_columns:
    raise ValueError(
        f"DEMO table is missing columns: {sorted(missing_columns)}"
    )

demo = demo.dropna(subset=["primaryid", "caseid"]).copy()

# Select the latest available version for each CASEID first.
demo["caseversion_num"] = pd.to_numeric(
    demo["caseversion"], errors="coerce"
).fillna(-1)

demo = demo.sort_values(
    ["caseid", "caseversion_num", "primaryid"]
)

latest_demo = demo.drop_duplicates(
    subset=["caseid"],
    keep="last",
).copy()

print("\nLatest unique CASEIDs before DELETE filtering:",
      latest_demo["caseid"].nunique())

# Remove CASEIDs present in the combined DELETE ID list.
deleted_mask = latest_demo["caseid"].isin(deleted_ids)

print("Latest cases matching DELETE IDs:",
      int(deleted_mask.sum()))

latest_demo = latest_demo.loc[~deleted_mask].copy()

valid_ids = set(latest_demo["primaryid"].dropna())

drug = drug[drug["primaryid"].isin(valid_ids)].copy()
reac = reac[reac["primaryid"].isin(valid_ids)].copy()

N = latest_demo["primaryid"].nunique()

if N == 0:
    raise ValueError("No retained reports after DELETE filtering.")

print("Latest retained cases:", latest_demo["caseid"].nunique())
print("Retained report IDs (N):", N)

# =========================================================
# 5. BUILD REPORT-LEVEL DRUG AND REACTION SETS
# =========================================================

# Normalize drug names. Ingredient name is preferred when available.
if "prod_ai" not in drug.columns:
    drug["prod_ai"] = ""

if "drugname" not in drug.columns:
    raise ValueError("DRUG table is missing DRUGNAME.")

preferred = drug["prod_ai"].fillna("").astype(str).str.strip()
fallback = drug["drugname"].fillna("").astype(str).str.strip()

drug["drug_key"] = preferred.where(
    preferred.ne(""),
    fallback,
)

drug["drug_key"] = (
    drug["drug_key"]
    .str.upper()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

# Include all recorded roles consistently.
# Each (report, drug) combination is counted only once.
report_drugs = drug.loc[
    drug["drug_key"].ne(""),
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
    reac["reaction_key"].ne(""),
    ["primaryid", "reaction_key"],
].drop_duplicates()

# Unique reports containing each drug or reaction.
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

pair_counts["drug_reports"] = pair_counts["drug_key"].map(
    drug_counts
)

pair_counts["reaction_reports"] = pair_counts["reaction_key"].map(
    reaction_counts
)

# =========================================================
# 6. BUILD 2x2 CONTINGENCY TABLE
# =========================================================
#
#                       Reaction present   Reaction absent
# Drug present                  a                 b
# Drug absent                   c                 d
#
# N = same retained report universe for every cell.
#
# a = reports with this drug AND this reaction
# b = reports with this drug but NOT this reaction
# c = reports with this reaction but NOT this drug
# d = reports with neither this drug nor this reaction

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
    pair_counts["log_ROR"]
    - 1.96 * pair_counts["SE_log_ROR"]
)

pair_counts["ROR_CI_upper"] = np.exp(
    pair_counts["log_ROR"]
    + 1.96 * pair_counts["SE_log_ROR"]
)

# Exploratory screening threshold, not proof of causality.
pair_counts["potential_signal"] = (
    (pair_counts["a"] >= 3)
    & (pair_counts["ROR_CI_lower"] > 1)
)

pair_counts = pair_counts.sort_values(
    ["potential_signal", "ROR", "a"],
    ascending=[False, False, False],
).reset_index(drop=True)


# =========================================================
# 8. SAVE TO NEW FILES ONLY
# =========================================================

csv_path = OUTPUT_DIR / OUTPUT_CSV_NAME
summary_path = OUTPUT_DIR / OUTPUT_SUMMARY_NAME

# Refuse to overwrite a previous v3 result.
if csv_path.exists() or summary_path.exists():
    raise FileExistsError(
        "v4 output already exists. Back up or rename the existing "
        "v4 files before running again."
    )
pair_counts.to_csv(csv_path, index=False)

summary = (
    "Source: FAERS 2026 Q1 + Q2\n"
    f"DELETE ID field configured: {DELETE_ID_FIELD}\n"
    f"Unique DELETE IDs listed: {len(deleted_ids)}\n"
    f"Latest retained cases: {latest_demo['caseid'].nunique()}\n"
    f"Retained report IDs (N): {N}\n"
    f"Unique drug names: {report_drugs['drug_key'].nunique()}\n"
    f"Unique reactions: {report_reactions['reaction_key'].nunique()}\n"
    f"Drug-reaction pairs: {len(pair_counts)}\n"
    f"Pairs with a >= 3: {int((pair_counts['a'] >= 3).sum())}\n"
    f"Exploratory potential signals: "
    f"{int(pair_counts['potential_signal'].sum())}\n"
    "Drug role definition: all recorded roles\n"
    "Interpretation: exploratory disproportionality screening only\n"
    f"Output CSV: {csv_path}\n"
)

summary_path.write_text(summary, encoding="utf-8")

print("\nPipeline completed.")
print("CSV:", csv_path)
print("Summary:", summary_path)
print("\nTop 10 results:")
print(pair_counts.head(10).to_string(index=False))