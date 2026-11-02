
from pathlib import Path
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project"
)

path = base / "pipeline_v2" / "output" / "faers_signal_review_v1.csv"

df = pd.read_csv(
    path,
    usecols=[
        "drug_key",
        "reaction_key",
        "a",
        "b",
        "c",
        "ROR",
        "ROR_CI_lower",
        "review_candidate",
    ],
)

print("Total rows:", len(df))

for drug in ["SOAP", "GUANIDINE", "MEDROXYPROGESTERONE ACETATE"]:
    subset = df[df["drug_key"] == drug]

    print(f"\nDRUG: {drug}")
    print("Total reaction pairs:", len(subset))
    print(
        subset.sort_values("a", ascending=False)
        .head(10)
        .to_string(index=False)
    )
