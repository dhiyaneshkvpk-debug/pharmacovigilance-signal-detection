import zipfile
import pandas as pd

#Loading Zip file

zip_q1 = r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw\faers_ascii_2026q1.zip"
zip_q2 = r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw\faers_ascii_2026q2.zip"

def load_faers_quarter(zip_path):
    with zipfile.ZipFile(zip_path,'r') as z:
        files=z.namelist()
        demo_file = [f for f in files if 'DEMO' in f and f.endswith('.txt')][0]
        drug_file = [f for f in files if 'DRUG' in f and f.endswith('.txt')][0]
        reac_file = [f for f in files if 'REAC' in f and f.endswith('.txt')][0]
        
        print(f"Loading files from {zip_path}...")
        demo_df=pd.read_csv(z.open(demo_file),sep='$', low_memory=False)
        drug_df=pd.read_csv(z.open(drug_file),sep='$', low_memory=False)
        reac_df=pd.read_csv(z.open(reac_file),sep='$', low_memory=False)

    return demo_df, drug_df, reac_df
print("load_faers_quarter loaded successfully")

demo_q1, drug_q1, reac_q1 = load_faers_quarter(zip_q1)
demo_q2, drug_q2, reac_q2 = load_faers_quarter(zip_q2)

demo_all = pd.concat([demo_q1, demo_q2], ignore_index=True)
drug_all = pd.concat([drug_q1, drug_q2], ignore_index=True)
reac_all = pd.concat([reac_q1, reac_q2], ignore_index=True)

print(f"Total Demo Rows Loaded: {len(demo_all): ,}")

#Data Cleaning

demo_clean = (
    demo_all.sort_values(by=['caseid', 'caseversion'], ascending=[True,False]).drop_duplicates(subset=['caseid'], keep='first')
)

#Extract valid primary IDs after deduplication
valid_ids = set(demo_clean['primaryid'])

#filter DRUG and REAC tables to match only deduplicated reports

drug_clean = drug_all[drug_all['primaryid'].isin(valid_ids)].copy()
reac_clean = reac_all[reac_all['primaryid'].isin(valid_ids)].copy()

#4. Standardize drug names to UPPERCASE and Keep Primary Suspect drugs
drug_ps = drug_clean[drug_clean['role_cod']=='PS'].copy()
drug_ps['drugname_clean'] = drug_ps['drugname'].str.upper().str.strip()

print(f"Clean Unique Cases: {len(demo_clean): ,}")

#Drugs with Side effects (Reactions)

drug_reaction_pairs = pd.merge(
    drug_ps[['primaryid', 'drugname_clean']],
    reac_clean[['primaryid', 'pt']],
    on='primaryid'
).drop_duplicates()

drug_reaction_pairs.rename(columns={'pt': 'side_effect'}, inplace=True)

top_drug_side_effects = (
    drug_reaction_pairs
    .groupby(['drugname_clean', 'side_effect'])
    .size()
    .reset_index(name='report_count')
    .sort_values(by='report_count', ascending=False)
)

top_drugs = drug_ps['drugname_clean'].value_counts().head(50).reset_index(name='total_reports')

top_drugs.to_csv('top_50_reported_drugs.csv', index=False)
top_drug_side_effects.head(100).to_csv('top_100_drug_side_effects.csv', index=False)

print("\nProcessing complete! Outputs saved successfully:")
print("1. top_50_reported_drugs.csv")
print("2. top_100_drug_side_effects.csv")

