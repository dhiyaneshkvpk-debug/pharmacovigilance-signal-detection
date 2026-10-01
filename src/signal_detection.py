import zipfile
import pandas as pd
import numpy as np

# --- STEP 1: LOAD FAERS DATA ---
print("Loading FAERS datasets...")

path_q1 = r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw\faers_ascii_2026q1.zip"
path_q2 = r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw\faers_ascii_2026q2.zip"

def get_clean_pairs(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        demo_file = [f for f in files if 'DEMO' in f and f.endswith('.txt')][0]
        drug_file = [f for f in files if 'DRUG' in f and f.endswith('.txt')][0]
        reac_file = [f for f in files if 'REAC' in f and f.endswith('.txt')][0]

        demo = pd.read_csv(z.open(demo_file), sep='$', low_memory=False)
        drug = pd.read_csv(z.open(drug_file), sep='$', low_memory=False)
        reac = pd.read_csv(z.open(reac_file), sep='$', low_memory=False)

    # Keep latest case version
    demo_clean = demo.sort_values(by=['caseid', 'caseversion'], ascending=[True, False]).drop_duplicates(subset=['caseid'], keep='first')
    valid_ids = set(demo_clean['primaryid'])

    drug_ps = drug[(drug['primaryid'].isin(valid_ids)) & (drug['role_cod'] == 'PS')].copy()
    drug_ps['drugname_clean'] = drug_ps['drugname'].str.upper().str.strip()

    reac_clean = reac[reac['primaryid'].isin(valid_ids)].copy()

    # Merge drugs and side effects
    pairs = pd.merge(
        drug_ps[['primaryid', 'drugname_clean']],
        reac_clean[['primaryid', 'pt']],
        on='primaryid'
    ).drop_duplicates()

    pairs.rename(columns={'pt': 'side_effect'}, inplace=True)
    return pairs

# Combine Q1 and Q2
pairs_q1 = get_clean_pairs(path_q1)
pairs_q2 = get_clean_pairs(path_q2)
all_pairs = pd.concat([pairs_q1, pairs_q2], ignore_index=True).drop_duplicates()

print(f"Total Unique Pairs Loaded: {len(all_pairs):,}")


# --- STEP 2: CALCULATE AGGREGATE TOTALS FOR CONTINGENCY MATRIX ---
# Count total unique cases
N = len(all_pairs)

# Total counts per drug
drug_counts = all_pairs['drugname_clean'].value_counts().to_dict()

# Total counts per side effect
effect_counts = all_pairs['side_effect'].value_counts().to_dict()

# Count drug-side effect pair frequencies
pair_counts = (
    all_pairs.groupby(['drugname_clean', 'side_effect'])
    .size()
    .reset_index(name='a')
)

# Filter for pairs with at least 5 reports to reduce noise
pair_counts = pair_counts[pair_counts['a'] >= 5].copy()


# --- STEP 3: CALCULATE ROR & CONFIDENCE INTERVALS ---
def calculate_ror_metrics(row):
    a = row['a']
    drug = row['drugname_clean']
    effect = row['side_effect']

    # b = drug count minus a
    b = drug_counts[drug] - a
    # c = side effect count minus a
    c = effect_counts[effect] - a
    # d = remaining overall total
    d = N - (a + b + c)

    if b <= 0 or c <= 0 or d <= 0:
        return pd.Series([np.nan, np.nan, np.nan, False])

    # ROR calculation
    ror = (a * d) / (b * c)

    # Standard Error of natural log of ROR
    se = np.sqrt((1 / a) + (1 / b) + (1 / c) + (1 / d))

    # 95% Confidence Interval Limits
    ci_lower = np.exp(np.log(ror) - 1.96 * se)
    ci_upper = np.exp(np.log(ror) + 1.96 * se)

    # Signal Flag (FDA Standard Criteria)
    is_signal = (a >= 3) and (ror >= 2.0) and (ci_lower > 1.0)

    return pd.Series([round(ror, 2), round(ci_lower, 2), round(ci_upper, 2), is_signal])

print("Calculating statistical signal metrics (ROR & 95% CI)...")
pair_counts[['ROR', 'ROR_CI_Lower', 'ROR_CI_Upper', 'is_safety_signal']] = pair_counts.apply(
    calculate_ror_metrics, axis=1
)

# Sort by highest ROR score
signals_df = pair_counts.sort_values(by='ROR', ascending=False)


# --- STEP 4: SAVE RESULTS ---
# Save full signals dataset
signals_df.to_csv('faers_safety_signals.csv', index=False)

# Save high-priority alerts only
alerts_df = signals_df[signals_df['is_safety_signal'] == True]
alerts_df.to_csv('high_priority_safety_alerts.csv', index=False)

print("\n--- SAFETY SIGNAL DETECTION COMPLETE ---")
print(f"Total Pairs Evaluated: {len(signals_df):,}")
print(f"Total High-Priority Signals Flagged: {len(alerts_df):,}")

print("\nTop 5 Flagged Safety Signals:")
print(alerts_df[['drugname_clean', 'side_effect', 'a', 'ROR', 'ROR_CI_Lower']].head())