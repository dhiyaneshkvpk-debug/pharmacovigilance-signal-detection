
from pathlib import Path
import pandas as pd

base_dir = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project"
)
csv_path = base_dir / "pipeline_v2" / "output" / "faers_ror_signals_v2.csv"

df = pd.read_csv(csv_path)

print("Rows:", len(df))
print("\nNegative count checks:")
for col in ["a", "b", "c", "d"]:
    print(f"{col} < 0:", int((df[col] < 0).sum()))

print("\nZero-cell counts:")
for col in ["a", "b", "c", "d"]:
    print(f"{col} == 0:", int((df[col] == 0).sum()))

print("\nRows with a >= 3 and b == 0:")
print(
    df.loc[
        (df["a"] >= 3) & (df["b"] == 0),
        ["drug_key", "reaction_key", "a", "drug_reports",
         "reaction_reports", "b", "c", "d", "ROR"]
    ].head(10).to_string(index=False)
)

print("\nValidation complete.")
