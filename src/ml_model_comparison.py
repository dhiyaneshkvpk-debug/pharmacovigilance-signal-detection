import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Classifier Imports
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier


# --- 1. PREPARE DUMMY / PROCESSED DATASET ---
# Assuming 'ml_data' DataFrame loaded from previous step
# X = ml_data[['report_count', 'avg_age', 'female_ratio']]
# y = ml_data['target']

np.random.seed(42)
n_samples = 1000
X = pd.DataFrame({
    'report_count': np.random.randint(1, 500, n_samples),
    'avg_age': np.random.uniform(18, 85, n_samples),
    'female_ratio': np.random.uniform(0, 1, n_samples)
})
y = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# --- 2. DEFINE MODEL DICTIONARY ---
models = {
    "Logistic Regression": (LogisticRegression(random_state=42), True),
    "Random Forest": (RandomForestClassifier(n_estimators=100, random_state=42), False),
    "Extra Trees": (ExtraTreesClassifier(n_estimators=100, random_state=42), False),
    "XGBoost": (XGBClassifier(n_estimators=100, eval_metric='logloss', random_state=42), False),
}


# --- 3. BENCHMARK MODELS ---
results = []

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
print("\n=======================================================")
print("             MODEL BENCHMARK RESULTS                   ")
print("=======================================================")
print(comparison_df.to_string(index=False))