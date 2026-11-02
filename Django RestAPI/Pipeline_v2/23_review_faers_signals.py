
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project"
)

OUTPUT_DIR = BASE_DIR / "pipeline_v2" / "output"

INPUT_CSV = OUTPUT_DIR / "faers_ror_signals_v7.csv"
OUTPUT_CSV = OUTPUT_DIR / "faers_signal_review_v1.csv"
SUMMARY_TXT = OUTPUT_DIR / "faers_signal_review_summary_v1.txt"

if not INPUT_CSV.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

df = pd.read_csv(INPUT_CSV, low_memory=False)

required = {
    "drug_key", "reaction_key", "a", "b", "c", "d",
    "ROR", "ROR_CI_lower", "ROR_CI_upper",
}
missing = required - set(df.columns)

if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

numeric_columns = [
    "a", "b", "c", "d", "ROR", "ROR_CI_lower", "ROR_CI_upper"
]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["review_candidate"] = (
    (df["a"] >= 5)
    & (df["b"] >= 5)
    & (df["c"] >= 5)
    & (df["ROR_CI_lower"] > 1)
    & np.isfinite(df["ROR"])
    & np.isfinite(df["ROR_CI_lower"])
    & np.isfinite(df["ROR_CI_upper"])
)

df["review_reason"] = np.select(
    [
        df["a"] < 5,
        df["b"] < 5,
        df["c"] < 5,
        df["ROR_CI_lower"] <= 1,
    ],
    [
        "Low co-reported count",
        "Low drug-without-reaction count",
        "Low reaction-without-drug count",
        "Lower confidence bound not above 1",
    ],
    default="Meets exploratory review criteria",
)

df = df.sort_values(
    ["review_candidate", "ROR_CI_lower", "a"],
    ascending=[False, False, False],
).reset_index(drop=True)

df.to_csv(OUTPUT_CSV, index=False)

summary = (
    "FAERS signal review — exploratory only\n"
    f"Input rows: {len(df)}\n"
    f"Review candidates: {int(df['review_candidate'].sum())}\n"
    "Criteria: a >= 5, b >= 5, c >= 5, lower 95% CI > 1\n"
    "These are review-prioritization criteria, not clinically validated thresholds.\n"
    "FAERS disproportionality does not establish causality or incidence.\n"
    f"Output: {OUTPUT_CSV}\n"
)

SUMMARY_TXT.write_text(summary, encoding="utf-8")

print(summary)
print("Top 10 review candidates:")
print(
    df.loc[df["review_candidate"]].head(10)[
        ["drug_key", "reaction_key", "a", "b", "c",
         "ROR", "ROR_CI_lower", "ROR_CI_upper"]
    ].to_string(index=False)
)