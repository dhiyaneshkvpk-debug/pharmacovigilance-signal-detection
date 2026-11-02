from pathlib import Path
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

source = base / "pipeline_v2" / "output" / "faers_ror_signals_v4.csv"
output = base / "pipeline_v2" / "output" / "faers_signal_candidates_v1.csv"

df = pd.read_csv(source, low_memory=False)

# Conservative exploratory screening criteria.
candidates = df[
    (df["a"] >= 5)
    & (df["b"] > 0)
    & (df["c"] > 0)
    & (df["ROR_CI_lower"] > 1)
].copy()

candidates = candidates.sort_values(
    ["a", "ROR_CI_lower"],
    ascending=[False, False]
)

if output.exists():
    raise FileExistsError(
        f"Output already exists: {output}. "
        "Rename it before creating another version."
    )

candidates.to_csv(output, index=False)

print("Total drug-reaction pairs:", len(df))
print("Candidate pairs after screening:", len(candidates))
print("Pairs with at least 5 co-reports:", int((df["a"] >= 5).sum()))
print("Candidates with ROR lower CI > 1:", int(
    (candidates["ROR_CI_lower"] > 1).sum()
))
print("Candidates with b=0 or c=0:", int(
    ((candidates["b"] == 0) | (candidates["c"] == 0)).sum()
))
print("\nTop 20 candidates:")
print(candidates[
    ["drug_key", "reaction_key", "a", "drug_reports",
     "reaction_reports", "ROR", "ROR_CI_lower", "ROR_CI_upper"]
].head(20).to_string(index=False))

print("\nSaved:", output)