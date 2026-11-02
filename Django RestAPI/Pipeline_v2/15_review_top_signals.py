from pathlib import Path
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

source = base / "pipeline_v2" / "output" / "faers_interpretable_shortlist_v1.csv"

df = pd.read_csv(source, low_memory=False)

# Review the highest RORs and the largest report counts separately.
print("\n=== TOP 20 BY ROR ===")
print(
    df.sort_values("ROR", ascending=False)[
        ["drug_key", "reaction_key", "a", "b", "c", "d",
         "drug_reports", "reaction_reports",
         "ROR", "ROR_CI_lower", "ROR_CI_upper"]
    ].head(20).to_string(index=False)
)

print("\n=== TOP 20 BY CO-REPORTED CASE COUNT ===")
print(
    df.sort_values("a", ascending=False)[
        ["drug_key", "reaction_key", "a", "b", "c", "d",
         "ROR", "ROR_CI_lower", "ROR_CI_upper"]
    ].head(20).to_string(index=False)
)