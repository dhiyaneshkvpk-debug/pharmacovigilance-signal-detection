"""
STEP 3 - MACHINE LEARNING
-------------------------
Question: "Using only what we knew in the OLD quarter, can we predict which
           drug-reaction pairs will become safety signals in the NEWEST quarter?"

Why this way? If we used the same data for the features AND for the answer, the model
would just re-learn our own formula (this is called DATA LEAKAGE). Using the old
quarter for features and the new quarter for the answer avoids that.

  Features (X): statistics from the OLD quarter (cases, ROR, PRR ...)
  Answer   (y): 1 = pair is a signal in the NEW quarter, 0 = not

Run:  python step3_machine_learning.py      (after steps 1 and 2)
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from helpers import make_signal_table

BASE = Path(__file__).parent
PROCESSED = BASE / "data" / "processed"
OUTPUT = BASE / "outputs"
OUTPUT.mkdir(exist_ok=True)

cases = pd.read_csv(PROCESSED / "cases.csv")
drugs = pd.read_csv(PROCESSED / "drugs.csv")
reactions = pd.read_csv(PROCESSED / "reactions.csv")

# ---------- 1. Split the data by time ----------
quarters = sorted(cases["quarter"].unique())
if len(quarters) < 2:
    raise SystemExit("Machine learning needs at least 2 quarters of data.")
old_quarters, new_quarter = quarters[:-1], quarters[-1]
print(f"Features from {old_quarters}  ->  answer from {new_quarter}")


def data_for(quarter_list):
    """Drugs and reactions of the cases that belong to these quarters."""
    ids = cases.loc[cases["quarter"].isin(quarter_list), "primaryid"]
    return drugs[drugs["primaryid"].isin(ids)], reactions[reactions["primaryid"].isin(ids)]


old_table, _ = make_signal_table(*data_for(old_quarters), min_cases=3)
new_table, _ = make_signal_table(*data_for([new_quarter]), min_cases=3)

# ---------- 2. Build the dataset ----------
# y = did the pair become a (real) signal in the new quarter?
new_signals = new_table[new_table["is_signal"] & ~new_table["is_non_drug_term"]][["drug", "reaction"]].copy()
new_signals["became_signal"] = 1

data = old_table[~old_table["is_non_drug_term"]].merge(new_signals, on=["drug", "reaction"], how="left")
data["became_signal"] = data["became_signal"].fillna(0).astype(int)
data["signal_before"] = data["is_signal"].astype(int)

# Features. We use log() because these numbers are very skewed (a few are huge).
data["log_cases"] = np.log1p(data["a"])
data["log_drug_total"] = np.log1p(data["drug_total"])
data["log_reaction_total"] = np.log1p(data["reaction_total"])
data["log_ror"] = np.log(data["ROR"].clip(lower=0.01))          # clip: log(0) is not allowed
data["log_ci_lower"] = np.log(data["ROR_CI_Lower"].clip(lower=0.01))
data["log_prr"] = np.log(data["PRR"].clip(lower=0.01))
data["log_chi2"] = np.log1p(data["chi2"])
features = ["log_cases", "log_drug_total", "log_reaction_total", "log_ror", "log_ci_lower", "log_prr", "log_chi2"]

X = data[features]
y = data["became_signal"]
print(f"Pairs: {len(data):,}   |   became a signal: {y.sum():,} ({y.mean():.1%})")

# ---------- 3. Train / test split ----------
# GroupShuffleSplit keeps every drug entirely in train OR test, so the model is tested
# on drugs it has never seen.
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=data["drug"]))
X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
print(f"Train pairs: {len(X_train):,}   Test pairs: {len(X_test):,}")

# ---------- 4. Train three models and compare ----------
models = {
    "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced")),
    "Random Forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=3, class_weight="balanced",
                                            random_state=42, n_jobs=-1),
    "Gradient Boosting": HistGradientBoostingClassifier(random_state=42),
}


def scores(name, true, predicted, probability):
    return {"model": name,
            "accuracy": round(accuracy_score(true, predicted), 3),
            "precision": round(precision_score(true, predicted, zero_division=0), 3),
            "recall": round(recall_score(true, predicted, zero_division=0), 3),
            "f1": round(f1_score(true, predicted, zero_division=0), 3),
            "roc_auc": round(roc_auc_score(true, probability), 3)}


# Baseline = a very simple guess: "if it was a signal before, it will be a signal again".
# A model is only useful if it beats this baseline.
baseline = data.iloc[test_idx]["signal_before"]
results = [scores("Baseline (signal before = signal again)", y_test, baseline, baseline)]

for name, model in models.items():
    model.fit(X_train, y_train)
    predicted = model.predict(X_test)
    probability = model.predict_proba(X_test)[:, 1]
    results.append(scores(name, y_test, predicted, probability))

results = pd.DataFrame(results)
print("\n", results.to_string(index=False))
best_name = results[results["model"].isin(models)].sort_values("roc_auc", ascending=False).iloc[0]["model"]
print(f"\nBest model: {best_name}")

# ---------- 5. Which features matter? (Random Forest) ----------
importance = pd.DataFrame({"feature": features, "importance": models["Random Forest"].feature_importances_.round(4)})
importance = importance.sort_values("importance", ascending=False)
print("\nFeature importance:\n", importance.to_string(index=False))

# ---------- 6. Watchlist: pairs NOT yet signals but likely to become one ----------
# cross_val_predict gives every pair a fair prediction from a model that did NOT train on it.
probability_all = cross_val_predict(models[best_name], X, y, groups=data["drug"],
                                    cv=GroupKFold(n_splits=5), method="predict_proba")[:, 1]
data["predicted_probability"] = probability_all.round(3)
watchlist = (data[data["signal_before"] == 0]
             .sort_values("predicted_probability", ascending=False)
             .head(100)[["drug", "reaction", "a", "ROR", "ROR_CI_Lower", "predicted_probability"]])

results.to_csv(OUTPUT / "model_results.csv", index=False)
importance.to_csv(OUTPUT / "feature_importance.csv", index=False)
watchlist.to_csv(OUTPUT / "watchlist.csv", index=False)

# ---------- CHECKPOINT ----------
baseline_auc = results.iloc[0]["roc_auc"]
best_auc = results[results["model"] == best_name].iloc[0]["roc_auc"]
print(f"\nCHECK - best model ROC-AUC ({best_auc}) should be higher than baseline ({baseline_auc}):",
      best_auc > baseline_auc)
print(f"Saved results in {OUTPUT}")
