
from pathlib import Path
import pandas as pd

base_dir = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project"
)

csv_path = base_dir / "pipeline_v2" / "output" / "faers_ror_signals_v2.csv"
df = pd.read_csv(csv_path)

print("Total signal rows:", len(df))

print("\nDrug report count distribution:")
print(df["drug_reports"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.99]))

print("\nReaction report count distribution:")
print(df["reaction_reports"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.99]))

print("\nRows by support count (a):")
print(
    df["a"]
    .value_counts()
    .sort_index()
    .head(15)
    .to_string()
)

print("\nRows with drug_reports <= a:")
print(int((df["drug_reports"] <= df["a"]).sum()))

print("\nRows with reaction_reports < a:")
print(int((df["reaction_reports"] < df["a"]).sum()))

print("\nCheck complete.")
