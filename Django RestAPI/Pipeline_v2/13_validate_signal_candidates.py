from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

source = base / "pipeline_v2" / "output" / "faers_ror_signals_v4.csv"
output = base / "pipeline_v2" / "output" / "faers_signal_candidates_v2.csv"

if output.exists():
    raise FileExistsError(f"Output already exists: {output}")

df = pd.read_csv(source, low_memory=False)

# Approximate two-sided Wald test for log(ROR).
z = df["log_ROR"] / df["SE_log_ROR"]
df["p_value_approx"] = 2 * norm.sf(np.abs(z))

# Benjamini-Hochberg FDR adjustment over all tested drug-reaction pairs.
p = df["p_value_approx"].to_numpy()
n = len(p)
order = np.argsort(p)
ranked_p = p[order]
adjusted = ranked_p * n / np.arange(1, n + 1)
adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
adjusted = np.clip(adjusted, 0, 1)

df["q_value_BH_approx"] = np.empty(n)
df.loc[df.index[order], "q_value_BH_approx"] = adjusted

# Exploratory shortlist; not a clinical diagnosis or causal finding.
candidates = df[
    (df["a"] >= 5)
    & (df["b"] > 0)
    & (df["c"] > 0)
    & (df["ROR_CI_lower"] > 1)
    & (df["q_value_BH_approx"] < 0.05)
].copy()

candidates = candidates.sort_values(
    ["q_value_BH_approx", "a"],
    ascending=[True, False],
)

candidates.to_csv(output, index=False)

print("All pairs tested:", len(df))
print("Pairs with approximate BH q < 0.05:",
      int((df["q_value_BH_approx"] < 0.05).sum()))
print("Candidates after count, cell and CI filters:", len(candidates))
print("\nTop 20 candidates:")
print(candidates[
    ["drug_key", "reaction_key", "a", "ROR",
     "ROR_CI_lower", "ROR_CI_upper",
     "p_value_approx", "q_value_BH_approx"]
].head(20).to_string(index=False))

print("\nSaved:", output)