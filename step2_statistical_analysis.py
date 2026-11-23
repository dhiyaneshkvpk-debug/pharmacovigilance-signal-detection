"""
STEP 2 - STATISTICAL ANALYSIS
-----------------------------
Part A - Descriptive statistics: who reports, which drugs and reactions are most common
Part B - Signal detection: which drug-reaction pairs are reported MORE than expected?
         (ROR, PRR, confidence interval, chi-square test, p-value)

Run:  python step2_statistical_analysis.py      (after step 1)
"""
from pathlib import Path

import numpy as np
import pandas as pd

from helpers import make_signal_table

BASE = Path(__file__).parent
PROCESSED = BASE / "data" / "processed"
OUTPUT = BASE / "outputs"
OUTPUT.mkdir(exist_ok=True)

cases = pd.read_csv(PROCESSED / "cases.csv")
drugs = pd.read_csv(PROCESSED / "drugs.csv")
reactions = pd.read_csv(PROCESSED / "reactions.csv")

# ======================= PART A: DESCRIPTIVE STATISTICS =======================
print("PART A - Descriptive statistics\n")

# Age: mean, median, min, max ...
age_summary = cases["age_years"].describe().round(1).reset_index()
age_summary.columns = ["statistic", "value"]
print("Age summary (years):\n", age_summary.to_string(index=False))

# Age histogram data (10 groups of 10 years) - used by the dashboard
age_counts, age_edges = np.histogram(cases["age_years"].dropna(), bins=range(0, 110, 10))
age_bins = pd.DataFrame({"age_group": [f"{a}-{a + 9}" for a in age_edges[:-1]], "cases": age_counts})

sex_counts = cases["sex"].value_counts().reset_index()
sex_counts.columns = ["sex", "cases"]
cases_by_quarter = cases["quarter"].value_counts().sort_index().reset_index()
cases_by_quarter.columns = ["quarter", "cases"]

# Top 50 drugs and top 50 reactions (number of cases)
top_drugs = drugs["drug"].value_counts().head(50).reset_index()
top_drugs.columns = ["drug", "cases"]
top_reactions = reactions["reaction"].value_counts().head(50).reset_index()
top_reactions.columns = ["reaction", "cases"]
print("\nTop 5 drugs:\n", top_drugs.head(5).to_string(index=False))
print("\nTop 5 reactions:\n", top_reactions.head(5).to_string(index=False))

# ======================= PART B: SIGNAL DETECTION =======================
print("\nPART B - Signal detection (ROR) ... this takes about 10 seconds")
signals, N = make_signal_table(drugs, reactions, min_cases=3)

strength_counts = signals["strength"].value_counts()
print(f"\nCases analysed        : {N:,}")
print(f"Drug-reaction pairs   : {len(signals):,}")
print("Pairs by strength:\n", strength_counts.to_string())

# ---- save everything for the dashboard ----
signals.to_csv(OUTPUT / "signals.csv", index=False)
age_summary.to_csv(OUTPUT / "age_summary.csv", index=False)
age_bins.to_csv(OUTPUT / "age_bins.csv", index=False)
sex_counts.to_csv(OUTPUT / "sex_counts.csv", index=False)
cases_by_quarter.to_csv(OUTPUT / "cases_by_quarter.csv", index=False)
top_drugs.to_csv(OUTPUT / "top_drugs.csv", index=False)
top_reactions.to_csv(OUTPUT / "top_reactions.csv", index=False)
summary = pd.DataFrame({
    "metric": ["Cases", "Drugs", "Reaction terms", "Drug-reaction pairs", "Statistical signals", "Strong signals"],
    "value": [N, drugs["drug"].nunique(), reactions["reaction"].nunique(), len(signals),
              int(signals["is_signal"].sum()), int((signals["strength"] == "Strong").sum())]})
summary.to_csv(OUTPUT / "summary.csv", index=False)

# ---- CHECKPOINT ----
print("\nTop 5 STRONG signals (ranked by the lower end of the confidence interval):")
print(signals[signals["strength"] == "Strong"].head(5)[
    ["drug", "reaction", "a", "ROR", "ROR_CI_Lower", "p_value"]].to_string(index=False))
print("\nCHECK - signals must have ROR >= 2 and CI lower > 1:",
      bool(((signals[signals["is_signal"]]["ROR"] >= 2) & (signals[signals["is_signal"]]["ROR_CI_Lower"] > 1)).all()))
strong = signals[signals["strength"] == "Strong"]
print("CHECK - every STRONG signal has a tiny p-value (< 0.05):", bool((strong["p_value"] < 0.05).all()))
print(f"Saved results in {OUTPUT}")
