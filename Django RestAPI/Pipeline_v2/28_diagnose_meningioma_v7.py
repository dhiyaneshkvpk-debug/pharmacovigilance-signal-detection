from pathlib import Path
from zipfile import ZipFile
import pandas as pd
BASE = Path(r"D:\academics\Data science and AI\End_to_end project\healthcare\Project")
RAW = BASE / "Data" / "Raw"
QUARTERS = [RAW / "faers_ascii_2026q1.zip", RAW / "faers_ascii_2026q2.zip"]
def read_table(zip_path, table):
    quarter = "26Q1" if "q1" in zip_path.name.lower() else "26Q2"
    target = f"{table}{quarter}.TXT"
    with ZipFile(zip_path) as z:
        member = next(n for n in z.namelist() if n.upper().endswith("/" + target))
        with z.open(member) as f:
            df = pd.read_csv(f, sep="$", dtype=str, encoding="latin-1",
                             on_bad_lines="skip", low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    return df
demo_parts, drug_parts, reac_parts = [], [], []
deleted_ids = set()
for zp in QUARTERS:
    print("Reading", zp.name)
    demo_parts.append(read_table(zp, "DEMO"))
    drug_parts.append(read_table(zp, "DRUG"))
    reac_parts.append(read_table(zp, "REAC"))
    with ZipFile(zp) as z:
        members = [n for n in z.namelist()
                   if "DELETE" in Path(n).name.upper() and n.upper().endswith(".TXT")]
        if len(members) > 1:
            raise ValueError(f"Multiple DELETE files: {members}")
        if members:
            with z.open(members[0]) as f:
                d = pd.read_csv(f, sep="$", header=None, dtype=str,
                                encoding="latin-1", on_bad_lines="skip")
            if not d.empty:
                vals = d.iloc[:, 0].dropna().astype(str).str.strip()
                deleted_ids.update(vals[vals.ne("")])
demo = pd.concat(demo_parts, ignore_index=True)
drug = pd.concat(drug_parts, ignore_index=True)
reac = pd.concat(reac_parts, ignore_index=True)
for df in (demo, drug, reac):
    for col in ("primaryid", "caseid"):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip().replace("", pd.NA)
demo = demo.dropna(subset=["primaryid", "caseid"]).copy()
demo["caseversion_num"] = pd.to_numeric(demo["caseversion"], errors="coerce").fillna(-1)
demo = demo.sort_values(["caseid", "caseversion_num", "primaryid"])
latest = demo.drop_duplicates(subset=["caseid"], keep="last").copy()
print("Latest CASEIDs before DELETE:", latest["caseid"].nunique())
print("Matching assumed DELETE CASEIDs:", int(latest["caseid"].isin(deleted_ids).sum()))
latest = latest.loc[~latest["caseid"].isin(deleted_ids)].copy()
valid_ids = set(latest["primaryid"].dropna())
drug = drug.loc[drug["primaryid"].isin(valid_ids)].copy()
reac = reac.loc[reac["primaryid"].isin(valid_ids)].copy()
preferred = drug.get("prod_ai", pd.Series("", index=drug.index)).fillna("").astype(str).str.strip()
fallback = drug["drugname"].fillna("").astype(str).str.strip()
drug["drug_key"] = preferred.where(preferred.ne(""), fallback)
drug["drug_key"] = drug["drug_key"].str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
reac["reaction_key"] = reac["pt"].fillna("").astype(str).str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
rd = drug.loc[drug["primaryid"].notna() & drug["drug_key"].ne(""),
              ["primaryid", "drug_key"]].drop_duplicates()
rr = reac.loc[reac["primaryid"].notna() & reac["reaction_key"].ne(""),
              ["primaryid", "reaction_key"]].drop_duplicates()
drug_reports = rd.groupby("drug_key")["primaryid"].nunique()
reaction_reports = rr.groupby("reaction_key")["primaryid"].nunique()
pairs = rd.merge(rr, on="primaryid", how="inner").drop_duplicates(
    ["primaryid", "drug_key", "reaction_key"])
target_drug = "MEDROXYPROGESTERONE ACETATE"
target_reaction = "MENINGIOMA"
selected = pairs.loc[
    pairs["drug_key"].eq(target_drug) &
    pairs["reaction_key"].eq(target_reaction)
]
print("\n=== V7-MATCHED DIAGNOSTIC ===")
print("Retained report IDs N:", latest["primaryid"].nunique())
print("Drug reports for target:", int(drug_reports.get(target_drug, 0)))
print("Reaction reports for target:", int(reaction_reports.get(target_reaction, 0)))
print("Co-reported target pairs (a):", selected["primaryid"].nunique())
print("Unique drug keys containing MEDROXY:", int(rd["drug_key"].str.contains("MEDROXY", na=False).sum()))
print("Unique target report IDs:", selected["primaryid"].nunique())
