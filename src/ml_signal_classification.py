import os
import zipfile
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report
)

# Robust XGBoost import check
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("[INFO] xgboost is not installed. To include XGBoost, run 'pip install xgboost'")


# ==============================================================================
# STEP 1: RESOLVE FILE PATHS
# ==============================================================================
# Get directory containing src/ and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Default raw data ZIP locations
zip_q1 = r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw\faers_ascii_2026q1.zip"
zip_q2 = r"D:\academics\Data science and AI\End_to_end project\healthcare\Project\Data\Raw\faers_ascii_2026q2.zip"

# Locate generated safety signals CSV
signals_csv_path = os.path.join(PROJECT_ROOT, "faers_safety_signals.csv")

if not os.path.exists(signals_csv_path):
    if os.path.exists("faers_safety_signals.csv"):
        signals_csv_path = "faers_safety_signals.csv"
    else:
        raise FileNotFoundError(
            f"\n\n[ERROR] Could not find 'faers_safety_signals.csv'.\n"
            f"Please run 'python signal_detection.py' first to generate this file!"
        )


# ==============================================================================
# STEP 2: FEATURE EXTRACTION FROM FAERS ZIP FILES
# ==============================================================================
print("Extracting features from raw FAERS datasets...")

def extract_merged_features(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        demo_f = [f for f in files if 'DEMO' in f and f.endswith('.txt')][0]
        drug_f = [f for f in files if 'DRUG' in f and f.endswith('.txt')][0]
        reac_f = [f for f in files if 'REAC' in f and f.endswith('.txt')][0]

        demo = pd.read_csv(z.open(demo_f), sep='$', low_memory=False)
        drug = pd.read_csv(z.open(drug_f), sep='$', low_memory=False)
        reac = pd.read_csv(z.open(reac_f), sep='$', low_memory=False)

    # Deduplicate demographic reports by latest case version
    demo_clean = (
        demo.sort_values(by=['caseid', 'caseversion'], ascending=[True, False])
        .drop_duplicates(subset=['caseid'], keep='first')
    )
    demo_clean['age_num'] = pd.to_numeric(demo_clean['age'], errors='coerce')
    demo_clean['is_female'] = (demo_clean['sex'] == 'F').astype(int)

    # Clean Primary Suspect (PS) drug names
    drug_ps = drug[drug['role_cod'] == 'PS'].copy()
    drug_ps['drugname_clean'] = drug_ps['drugname'].str.upper().str.strip()

    # Join tables on primaryid
    merged = pd.merge(drug_ps[['primaryid', 'drugname_clean']], reac[['primaryid', 'pt']], on='primaryid')
    merged = pd.merge(merged, demo_clean[['primaryid', 'age_num', 'is_female']], on='primaryid')
    merged.rename(columns={'pt': 'side_effect'}, inplace=True)

    return merged

df_q1 = extract_merged_features(zip_q1)
df_q2 = extract_merged_features(zip_q2)
df = pd.concat([df_q1, df_q2], ignore_index=True)


# ==============================================================================
# STEP 3: AGGREGATE FEATURE MATRIX & TARGET LABELS
# ==============================================================================
print("Building pair-level feature matrix...")

pair_features = df.groupby(['drugname_clean', 'side_effect']).agg(
    report_count=('primaryid', 'count'),
    avg_age=('age_num', 'mean'),
    female_ratio=('is_female', 'mean')
).reset_index()

# Impute missing average age with dataset median
pair_features['avg_age'] = pair_features['avg_age'].fillna(pair_features['avg_age'].median())

# Load target labels generated during signal detection
signals_df = pd.read_csv(signals_csv_path)

# Handle potential column naming differences ('is_safety_signal' or 'is_signal')
target_col = 'is_safety_signal' if 'is_safety_signal' in signals_df.columns else 'is_signal'

ml_data = pd.merge(
    pair_features,
    signals_df[['drugname_clean', 'side_effect', target_col]],
    on=['drugname_clean', 'side_effect']
)

# Convert signal indicator to integer (1 = Signal Flag, 0 = Non-Signal)
ml_data['target'] = ml_data[target_col].astype(int)

X = ml_data[['report_count', 'avg_age', 'female_ratio']]
y = ml_data['target']

# Calculate class imbalance weight for XGBoost
neg_count = (y == 0).sum()
pos_count = (y == 1).sum()
scale_pos_weight_val = neg_count / max(1, pos_count)

print(f"Dataset Size: {len(ml_data):,} rows")
print(f"Target Distribution: Non-Signals (0) = {neg_count}, Signals (1) = {pos_count}")


# ==============================================================================
# STEP 4: TRAIN-TEST SPLIT & FEATURE SCALING
# ==============================================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Standard Scaling required for SVC distance calculations
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


from sklearn.linear_model import LogisticRegression
# or from sklearn.ensemble import HistGradientBoostingClassifier

from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

# ==============================================================================
# STEP 5: INITIALIZE MODELS (FAST LINEAR SVM)
# ==============================================================================
models = {
    "Support Vector Classifier (Linear)": (
        CalibratedClassifierCV(LinearSVC(dual=False, random_state=42)),
        True  # Needs scaled input
    ),
    "Random Forest Classifier": (
        RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        False
    )
}

# ==============================================================================
# STEP 6: EVALUATE & COMPARISON BENCHMARK
# ==============================================================================
results = []
print("\nTraining and evaluating models...")

for name, (model, requires_scaling) in models.items():
    X_tr = X_train_scaled if requires_scaling else X_train
    X_te = X_test_scaled if requires_scaling else X_test

    model.fit(X_tr, y_train)
    preds = model.predict(X_te)
    probs = model.predict_proba(X_te)[:, 1]

    results.append({
        "Model": name,
        "Accuracy": round(accuracy_score(y_test, preds), 4),
        "Precision": round(precision_score(y_test, preds, zero_division=0), 4),
        "Recall": round(recall_score(y_test, preds, zero_division=0), 4),
        "F1-Score": round(f1_score(y_test, preds, zero_division=0), 4),
        "ROC-AUC": round(roc_auc_score(y_test, probs), 4)
    })

comparison_df = pd.DataFrame(results).sort_values(by="ROC-AUC", ascending=False)

print("\n==========================================================")
print("             MODEL BENCHMARK SUMMARY TABLE                ")
print("==========================================================")
print(comparison_df.to_string(index=False))


# ==============================================================================
# STEP 7: DETAILED REPORT FOR TOP MODEL
# ==============================================================================
best_model_name = comparison_df.iloc[0]["Model"]
best_model_tuple = models[best_model_name]
best_model = best_model_tuple[0]
uses_scaled = best_model_tuple[1]

X_te_final = X_test_scaled if uses_scaled else X_test
final_preds = best_model.predict(X_te_final)

print(f"\nDetailed Classification Report for Top Model ({best_model_name}):")
print(classification_report(y_test, final_preds))