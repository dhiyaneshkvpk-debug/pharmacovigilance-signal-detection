from pathlib import Path
source = Path("Pipeline_v2/24_audit_meningioma_signal.py")
code = source.read_text(encoding="utf-8-sig")
marker = 'print("\\n=== RAW FAERS AUDIT'
if marker not in code:
    raise ValueError("Expected marker not found in original audit script.")
exec(code.split(marker)[0])
exact = reac.loc[
    reac["PT"].str.strip().str.casefold().eq("meningioma")
].copy()
exact_ids = set(exact["PRIMARYID"])
all_drug_ids = set(med["PRIMARYID"])
ps_drug_ids = set(med.loc[med["ROLE_COD"] == "PS", "PRIMARYID"])
print("\n=== EXACT MENINGIOMA COUNTS ===")
print("Meningioma reaction rows:", len(exact))
print("Unique PRIMARYIDs with exact Meningioma:", len(exact_ids))
print("Unique CASEIDs with exact Meningioma:", exact["CASEID"].nunique())
print("Drug + exact Meningioma, all roles:", len(all_drug_ids & exact_ids))
print("Drug + exact Meningioma, PS only:", len(ps_drug_ids & exact_ids))
