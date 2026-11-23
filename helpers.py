"""
helpers.py - ONE function shared by step2 and step3.

It turns two simple tables (drugs and reactions) into a "signal table":
for every (drug, reaction) pair it calculates the statistics that tell us
whether the reaction is reported MORE OFTEN with that drug than with other drugs.
"""
import numpy as np
import pandas as pd
from scipy.stats import chi2 as chi2_distribution

# Reaction terms that describe a product / dosing / device problem,
# NOT a real side effect of the drug. We keep them but label them "Excluded".
IGNORE_WORDS = ["PRODUCT", "DEVICE", "OFF LABEL", "WRONG", "INCORRECT", "MEDICATION ERROR",
                "EXPOSURE", "DRUG INEFFECTIVE", "OVERDOSE", "SCAN", "DIAGNOSTIC",
                "INVESTIGATION", "PREGNANCY AFTER", "DISEASE PROGRESSION"]


def make_signal_table(drugs, reactions, min_cases=3):
    """
    drugs     : table with columns  primaryid, drug       (one row per case per drug)
    reactions : table with columns  primaryid, reaction   (one row per case per reaction)

    For each (drug, reaction) pair we build a 2x2 table of CASES:

                         has the reaction    does not
        has the drug            a                b
        other drugs             c                d

    ROR (Reporting Odds Ratio) = (a * d) / (b * c)
      ROR = 1 -> no link.   ROR = 5 -> the reaction is 5x more likely to be reported with this drug.
    """
    # 1. Only use cases that have at least one drug AND at least one reaction
    ids_with_both = set(drugs["primaryid"]) & set(reactions["primaryid"])
    drugs = drugs[drugs["primaryid"].isin(ids_with_both)]
    reactions = reactions[reactions["primaryid"].isin(ids_with_both)]
    N = len(ids_with_both)                      # total number of cases

    # 2. How many cases per drug, and per reaction
    drug_total = drugs["drug"].value_counts()
    reaction_total = reactions["reaction"].value_counts()

    # 3. 'a' = how many cases have BOTH the drug and the reaction
    pairs = drugs.merge(reactions, on="primaryid")           # all drug-reaction combinations
    table = pairs.groupby(["drug", "reaction"]).size().reset_index(name="a")
    table = table[table["a"] >= min_cases].copy()            # ignore very rare pairs

    # 4. Fill the 2x2 table
    table["drug_total"] = table["drug"].map(drug_total)
    table["reaction_total"] = table["reaction"].map(reaction_total)
    # We use decimal numbers (float) because the numbers below get VERY big and
    # whole-number columns (int64) can overflow and silently give wrong answers.
    a = table["a"].astype(float)
    b = table["drug_total"].astype(float) - a
    c = table["reaction_total"].astype(float) - a
    d = N - a - b - c
    table["b"], table["c"], table["d"] = b, c, d

    # 5. ROR and its 95% confidence interval
    #    If any cell is 0 we add 0.5 to all cells (standard fix to avoid dividing by zero)
    add = np.where((b == 0) | (c == 0) | (d == 0), 0.5, 0.0)
    a2, b2, c2, d2 = a + add, b + add, c + add, d + add
    ror = (a2 * d2) / (b2 * c2)
    std_error = np.sqrt(1 / a2 + 1 / b2 + 1 / c2 + 1 / d2)
    table["ROR"] = ror.round(2)
    table["ROR_CI_Lower"] = np.exp(np.log(ror) - 1.96 * std_error).round(2)
    table["ROR_CI_Upper"] = np.exp(np.log(ror) + 1.96 * std_error).round(2)

    # 6. PRR (Proportional Reporting Ratio) - a second, similar measure
    table["PRR"] = (((a2 / (a2 + b2)) / (c2 / (c2 + d2)))).round(2)

    # 7. Chi-square test and p-value (is the link likely to be just chance?)
    denominator = ((a + b) * (c + d) * (a + c) * (b + d)).replace(0, np.nan)
    chi2_value = (N * (a * d - b * c) ** 2 / denominator).fillna(0)
    table["chi2"] = chi2_value.round(2)
    table["p_value"] = chi2_distribution.sf(chi2_value, df=1)

    # 8. The signal rule used in pharmacovigilance:
    #    ROR >= 2  AND  the lower end of the confidence interval is above 1
    table["is_signal"] = (table["ROR"] >= 2) & (table["ROR_CI_Lower"] > 1)
    table["is_non_drug_term"] = table["reaction"].str.contains("|".join(IGNORE_WORDS))

    # 9. Label how strong each signal is
    table["strength"] = np.select(
        [~table["is_signal"],
         table["is_non_drug_term"],
         (table["a"] >= 20) & (table["ROR_CI_Lower"] >= 5),
         table["a"] >= 10],
        ["No signal", "Excluded", "Strong", "Moderate"],
        default="Weak")

    table = table.sort_values("ROR_CI_Lower", ascending=False).reset_index(drop=True)
    return table, N
