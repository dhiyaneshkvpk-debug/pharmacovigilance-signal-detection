from pathlib import Path
import numpy as np
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)
source = base / "pipeline_v2" / "output" / "faers_ror_signals_v4.csv"

df = pd.read_csv(source, low_memory=False)

required = [
    "a", "b", "c", "d", "drug_reports", "reaction_reports",
    "ROR", "ROR_CI_lower", "ROR_CI_upper",
]
missing = [col for col in required if col not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

# Check whether each cell count is a nonnegative integer.
cells = df[["a", "b", "c", "d"]]
print("Rows:", len(df))
print("Missing cell counts:", int(cells.isna().any(axis=1).sum()))
print("Negative cell counts:", int((cells < 0).any(axis=1).sum()))
print(
    "Non-integer cell counts:",
    int(((cells % 1) != 0).any(axis=1).sum())
)

# These identities must hold for a valid 2x2 table.
bad_drug_total = (df["a"] + df["b"]) != df["drug_reports"]
bad_reaction_total = (df["a"] + df["c"]) != df["reaction_reports"]

print("Drug total identity failures:", int(bad_drug_total.sum()))
print("Reaction total identity failures:", int(bad_reaction_total.sum()))

# For the stated cohort of 792,346 reports:
N = 792346
bad_cohort_total = (df["a"] + df["b"] + df["c"] + df["d"]) != N
print("Cohort total identity failures:", int(bad_cohort_total.sum()))

# Recompute corrected ROR independently.
a = df["a"].astype(float)
b = df["b"].astype(float)
c = df["c"].astype(float)
d = df["d"].astype(float)

expected_ror = ((a + 0.5) * (d + 0.5)) / (
    (b + 0.5) * (c + 0.5)
)
diff = np.abs(df["ROR"] - expected_ror)

print("Maximum absolute ROR difference:", float(diff.max()))
print("Rows with ROR difference > 1e-6:", int((diff > 1e-6).sum()))

print("\nExamples of identity failures:")
bad = df[bad_drug_total | bad_reaction_total | bad_cohort_total]
print(
    bad[["drug_key", "reaction_key", "a", "b", "c", "d",
         "drug_reports", "reaction_reports"]]
    .head(10)
    .to_string(index=False)
)