from pathlib import Path
import pandas as pd

base = Path(
    r"D:\academics\Data science and AI\End_to_end project"
    r"\healthcare\Project"
)

source = base / "pipeline_v2" / "output" / "faers_ror_signals_v4.csv"
output = base / "pipeline_v2" / "output" / "faers_interpretable_shortlist_v1.csv"

if output.exists():
    raise FileExistsError(f"Output already exists: {output}")

df = pd.read_csv(source, low_memory=False)

# Broad exploratory screening criteria
screened = df[
    (df["a"] >= 20)
    & (df["b"] > 0)
    & (df["c"] > 0)
    & (df["ROR_CI_lower"] > 1)
].copy()

# Separate obvious product-use / medication-process terms.
# This is a preliminary text-based filter, not a validated MedDRA classification.
process_terms = [
    "OFF LABEL",
    "UNAPPROVED INDICATION",
    "INCORRECT DOSE",
    "ACCIDENTAL EXPOSURE",
    "EXPOSURE VIA",
    "PRODUCT USE",
    "MEDICATION ERROR",
    "WRONG DRUG",
    "WRONG ROUTE",
    "OVERDOSE",
    "UNDERDOSE",
]

reaction_text = screened["reaction_key"].fillna("").str.upper()
process_mask = reaction_text.apply(
    lambda term: any(keyword in term for keyword in process_terms)
)

process_events = screened[process_mask].copy()
clinical_shortlist = screened[~process_mask].copy()

clinical_shortlist = clinical_shortlist.sort_values(
    ["a", "ROR_CI_lower"],
    ascending=[False, False],
)

process_events.to_csv(
    base / "pipeline_v2" / "output" / "faers_process_terms_v1.csv",
    index=False,
)
clinical_shortlist.to_csv(output, index=False)

print("Pairs after initial screening:", len(screened))
print("Product-use / process terms separated:", len(process_events))
print("Exploratory clinical-event shortlist:", len(clinical_shortlist))

print("\nTop 30 shortlist pairs:")
print(
    clinical_shortlist[
        ["drug_key", "reaction_key", "a", "ROR",
         "ROR_CI_lower", "ROR_CI_upper"]
    ].head(30).to_string(index=False)
)

print("\nSaved shortlist:", output)