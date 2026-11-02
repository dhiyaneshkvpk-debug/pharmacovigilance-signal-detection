from pathlib import Path
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project\healthcare\Project"
)
csv_path = base / "pipeline_v2" / "output" / "faers_ror_signals_v4.csv"

df = pd.read_csv(csv_path, low_memory=False)

print("Rows:", len(df))
print("\nActual column names:")
print(df.columns.tolist())

required = [
    "drug_key", "reaction_key", "a", "b", "c", "d",
    "ROR", "log_ROR", "SE_log_ROR",
    "ROR_CI_lower", "ROR_CI_upper", "potential_signal"
]
missing = [c for c in required if c not in df.columns]
print("\nMissing expected columns:", missing)

if not missing:
    print("\nDuplicate drug-reaction pairs:",
          df.duplicated(["drug_key", "reaction_key"]).sum())
    print("Invalid or infinite ROR values:",
          (~df["ROR"].map(lambda x: pd.notna(x) and x > 0 and x < float("inf"))).sum())
    print("Potential signals:", int(df["potential_signal"].astype(bool).sum()))
    print("Signals with b=0 or c=0:",
          int((df["potential_signal"].astype(bool) &
               ((df["b"] == 0) | (df["c"] == 0))).sum()))

    print("\nTop 10 by co-report count:")
    print(
        df.sort_values(["a", "drug_reports"], ascending=False)
          [["drug_key", "reaction_key", "a", "b", "c", "d",
            "ROR", "ROR_CI_lower", "ROR_CI_upper"]]
          .head(10).to_string(index=False)
    )