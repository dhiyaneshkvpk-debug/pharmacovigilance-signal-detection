import zipfile
import pandas as pd


# ============================================================
# 1. FILE PATHS
# ============================================================

zip_q1 = r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw\faers_ascii_2026q1.zip"

zip_q2 = r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw\faers_ascii_2026q2.zip"


# ============================================================
# 2. LOAD FAERS QUARTER
# ============================================================

def load_faers_quarter(zip_path):

    with zipfile.ZipFile(zip_path, "r") as z:

        files = z.namelist()

        demo_file = next(
            f for f in files
            if "DEMO" in f.upper() and f.lower().endswith(".txt")
        )

        drug_file = next(
            f for f in files
            if "DRUG" in f.upper() and f.lower().endswith(".txt")
        )

        reac_file = next(
            f for f in files
            if "REAC" in f.upper() and f.lower().endswith(".txt")
        )

        print(f"\nLoading: {zip_path}")

        demo_df = pd.read_csv(
            z.open(demo_file),
            sep="$",
            low_memory=False
        )

        drug_df = pd.read_csv(
            z.open(drug_file),
            sep="$",
            low_memory=False
        )

        reac_df = pd.read_csv(
            z.open(reac_file),
            sep="$",
            low_memory=False
        )

    return demo_df, drug_df, reac_df


# ============================================================
# 3. LOAD Q1 AND Q2
# ============================================================

demo_q1, drug_q1, reac_q1 = load_faers_quarter(zip_q1)

demo_q2, drug_q2, reac_q2 = load_faers_quarter(zip_q2)


# ============================================================
# 4. COMBINE QUARTERS
# ============================================================

demo_all = pd.concat(
    [demo_q1, demo_q2],
    ignore_index=True
)

drug_all = pd.concat(
    [drug_q1, drug_q2],
    ignore_index=True
)

reac_all = pd.concat(
    [reac_q1, reac_q2],
    ignore_index=True
)


print("\n========== RAW DATA ==========")

print(f"Demo rows   : {len(demo_all):,}")
print(f"Drug rows   : {len(drug_all):,}")
print(f"Reaction rows: {len(reac_all):,}")


# ============================================================
# 5. CLEAN DEMO DATA
# ============================================================

# Convert identifiers to numeric where possible

demo_all["caseid"] = pd.to_numeric(
    demo_all["caseid"],
    errors="coerce"
)

demo_all["caseversion"] = pd.to_numeric(
    demo_all["caseversion"],
    errors="coerce"
)

demo_all["primaryid"] = pd.to_numeric(
    demo_all["primaryid"],
    errors="coerce"
)


# Remove records without required identifiers

demo_all = demo_all.dropna(
    subset=["caseid", "caseversion", "primaryid"]
)


# Keep latest version of each case

demo_clean = (
    demo_all
    .sort_values(
        ["caseid", "caseversion"],
        ascending=[True, False]
    )
    .drop_duplicates(
        subset=["caseid"],
        keep="first"
    )
)


print("\n========== CLEANING ==========")

print(
    f"Unique FAERS cases: {len(demo_clean):,}"
)


# ============================================================
# 6. FILTER DRUG AND REACTION TABLES
# ============================================================

valid_ids = set(
    demo_clean["primaryid"]
)


drug_clean = drug_all[
    drug_all["primaryid"].isin(valid_ids)
].copy()


reac_clean = reac_all[
    reac_all["primaryid"].isin(valid_ids)
].copy()


# ============================================================
# 7. PRIMARY SUSPECT DRUGS
# ============================================================

drug_ps = drug_clean[
    drug_clean["role_cod"].eq("PS")
].copy()


# Standardize drug names

drug_ps["drugname_clean"] = (
    drug_ps["drugname"]
    .fillna("")
    .astype(str)
    .str.upper()
    .str.strip()
)


# Remove empty drug names

drug_ps = drug_ps[
    drug_ps["drugname_clean"].ne("")
]


print(
    f"Primary suspect drug rows: {len(drug_ps):,}"
)


# ============================================================
# 8. STANDARDIZE REACTIONS
# ============================================================

reac_clean["pt_clean"] = (
    reac_clean["pt"]
    .fillna("")
    .astype(str)
    .str.upper()
    .str.strip()
)


reac_clean = reac_clean[
    reac_clean["pt_clean"].ne("")
]


# ============================================================
# 9. DRUG–REACTION PAIRS
# ============================================================

drug_reaction_pairs = pd.merge(

    drug_ps[
        ["primaryid", "drugname_clean"]
    ],

    reac_clean[
        ["primaryid", "pt_clean"]
    ],

    on="primaryid",

    how="inner"
)


# One drug-reaction pair per report

drug_reaction_pairs = (
    drug_reaction_pairs
    .drop_duplicates()
)


drug_reaction_pairs.rename(
    columns={
        "pt_clean": "side_effect"
    },
    inplace=True
)


print(
    f"Unique drug-reaction pairs: "
    f"{len(drug_reaction_pairs):,}"
)


# ============================================================
# 10. TOP DRUG–SIDE EFFECT COMBINATIONS
# ============================================================

top_drug_side_effects = (

    drug_reaction_pairs

    .groupby(
        [
            "drugname_clean",
            "side_effect"
        ]
    )

    .size()

    .reset_index(
        name="report_count"
    )

    .sort_values(
        "report_count",
        ascending=False
    )
)


# ============================================================
# 11. TOP REPORTED DRUGS
# ============================================================

top_drugs = (

    drug_ps

    .groupby("drugname_clean")

    .size()

    .reset_index(
        name="total_reports"
    )

    .sort_values(
        "total_reports",
        ascending=False
    )

    .head(50)
)


# ============================================================
# 12. SAVE RESULTS
# ============================================================

top_drugs.to_csv(
    "top_50_reported_drugs.csv",
    index=False
)


top_drug_side_effects.head(100).to_csv(
    "top_100_drug_side_effects.csv",
    index=False
)


print("\n========== OUTPUT ==========")

print("1. top_50_reported_drugs.csv")
print("2. top_100_drug_side_effects.csv")

print("\nProcessing completed successfully.")