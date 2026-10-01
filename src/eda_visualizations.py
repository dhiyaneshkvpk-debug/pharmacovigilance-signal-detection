import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 10})

print("Loading CSV files for visualization...")

# --- 1. LOAD CSV DATA ---
top_drugs_df = pd.read_csv('top_50_reported_drugs.csv')
top_pairs_df = pd.read_csv('top_100_drug_side_effects.csv')


# --- 2. CHART 1: TOP 10 MOST REPORTED DRUGS ---
plt.figure(figsize=(10, 6))

# Take top 10 drugs
top10_drugs = top_drugs_df.head(10)

ax1 = sns.barplot(
    data=top10_drugs,
    x='total_reports',
    y='drugname_clean',
    palette='Blues_r'
)

plt.title('Top 10 Primary Suspect Drugs in Adverse Event Reports (2026)', fontsize=14, fontweight='bold')
plt.xlabel('Total Adverse Event Reports', fontsize=12)
plt.ylabel('Drug Name', fontsize=12)

# Add numeric labels at the end of each bar
for p in ax1.patches:
    width = p.get_width()
    ax1.annotate(f'{int(width):,}',
                 (width, p.get_y() + p.get_height() / 2.),
                 ha='left', va='center',
                 xytext=(5, 0), textcoords='offset points')

plt.tight_layout()
plt.savefig('top_10_reported_drugs.png', dpi=300)
print("Saved Chart 1: top_10_reported_drugs.png")
plt.close()


# --- 3. CHART 2: TOP 10 DRUG & SIDE EFFECT COMBINATIONS ---
plt.figure(figsize=(12, 6))

# Take top 10 drug-reaction pairs
top10_pairs = top_pairs_df.head(10).copy()

# Create a combined label like "ASPIRIN -> HEADACHE"
top10_pairs['pair_label'] = top10_pairs['drugname_clean'] + '  ➜  ' + top10_pairs['side_effect']

ax2 = sns.barplot(
    data=top10_pairs,
    x='report_count',
    y='pair_label',
    palette='Reds_r'
)

plt.title('Top 10 Drug & Side-Effect Combinations', fontsize=14, fontweight='bold')
plt.xlabel('Number of Co-occurrences', fontsize=12)
plt.ylabel('Drug  ➜  Adverse Event', fontsize=12)

# Add numeric labels at the end of each bar
for p in ax2.patches:
    width = p.get_width()
    ax2.annotate(f'{int(width):,}',
                 (width, p.get_y() + p.get_height() / 2.),
                 ha='left', va='center',
                 xytext=(5, 0), textcoords='offset points')

plt.tight_layout()
plt.savefig('top_10_drug_side_effects.png', dpi=300)
print("Saved Chart 2: top_10_drug_side_effects.png")
plt.close()

print("\nVisualization task completed successfully!")