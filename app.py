"""
PharmaGuard AI - Streamlit dashboard
Run:  streamlit run app.py
(first run steps 1, 2 and 3 so the files in outputs/ exist)
"""
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="PharmaGuard AI", page_icon="💊", layout="wide")
OUTPUT = Path(__file__).parent / "outputs"


@st.cache_data                       # read each file only once (makes the app fast)
def load(file_name):
    return pd.read_csv(OUTPUT / file_name)


# ---------- stop with a friendly message if the steps were not run ----------
if not (OUTPUT / "signals.csv").exists():
    st.error("Results not found. Please run these commands first:")
    st.code("python step1_data_processing.py\npython step2_statistical_analysis.py\n"
            "python step3_machine_learning.py")
    st.stop()

signals = load("signals.csv")
signals["p_value"] = signals["p_value"].apply(lambda p: "< 0.001" if p < 0.001 else f"{p:.3f}")

# ---------- sidebar menu ----------
st.sidebar.title("💊 PharmaGuard AI")
page = st.sidebar.radio("Go to", ["📊 Overview", "🏆 Top drugs & reactions", "🔎 Signal explorer",
                                  "💊 Drug profile", "🤖 Machine learning", "ℹ️ About"])

# =====================================================================
if page == "📊 Overview":
    st.title("FDA FAERS Drug Safety Dashboard")
    st.write("Adverse-event reports sent to the US FDA, analysed to find drug-side effect pairs "
             "that are reported **more often than expected**.")

    summary = load("summary.csv").set_index("metric")["value"]
    cols = st.columns(len(summary))
    for col, (name, value) in zip(cols, summary.items()):
        col.metric(name, f"{int(value):,}")

    left, middle, right = st.columns(3)
    with left:
        st.subheader("Cases per quarter")
        st.bar_chart(load("cases_by_quarter.csv").set_index("quarter"))
    with middle:
        st.subheader("Patient sex")
        st.bar_chart(load("sex_counts.csv").set_index("sex"))
    with right:
        st.subheader("Patient age")
        st.bar_chart(load("age_bins.csv").set_index("age_group"))

    st.subheader("Signals by strength")
    st.bar_chart(signals["strength"].value_counts())

# =====================================================================
elif page == "🏆 Top drugs & reactions":
    st.title("Most reported drugs and reactions")
    how_many = st.slider("How many to show?", 5, 50, 15)
    left, right = st.columns(2)
    with left:
        st.subheader("Top drugs (cases)")
        st.bar_chart(load("top_drugs.csv").head(how_many).set_index("drug"), horizontal=True)
    with right:
        st.subheader("Top reactions (cases)")
        st.bar_chart(load("top_reactions.csv").head(how_many).set_index("reaction"), horizontal=True)
    st.info("A drug with many reports is not necessarily more dangerous - it may simply be "
            "used by more people.")

# =====================================================================
elif page == "🔎 Signal explorer":
    st.title("Signal explorer")
    st.write("Filter the drug-reaction pairs. Results are sorted by the **lower end of the "
             "confidence interval** (the most reliable way to rank).")

    c1, c2, c3, c4 = st.columns(4)
    drug_text = c1.text_input("Drug contains", placeholder="e.g. DUPIXENT").upper()
    reaction_text = c2.text_input("Reaction contains", placeholder="e.g. MENINGIOMA").upper()
    strengths = c3.multiselect("Strength", ["Strong", "Moderate", "Weak", "Excluded", "No signal"],
                               default=["Strong"])
    min_cases = c4.slider("Minimum cases", 3, 500, 10)

    result = signals[signals["strength"].isin(strengths) & (signals["a"] >= min_cases)]
    if drug_text:
        result = result[result["drug"].str.contains(drug_text, regex=False)]
    if reaction_text:
        result = result[result["reaction"].str.contains(reaction_text, regex=False)]

    st.write(f"**{len(result):,}** pairs found (showing the first 500)")
    show = ["drug", "reaction", "a", "ROR", "ROR_CI_Lower", "ROR_CI_Upper", "PRR", "p_value", "strength"]
    st.dataframe(result[show].head(500), hide_index=True)
    st.download_button("⬇️ Download these results (CSV)", result[show].to_csv(index=False),
                       file_name="filtered_signals.csv")

# =====================================================================
elif page == "💊 Drug profile":
    st.title("Drug profile")
    drug_list = sorted(signals["drug"].unique())
    start = drug_list.index("DEPO-PROVERA") if "DEPO-PROVERA" in drug_list else 0
    drug = st.selectbox("Choose a drug (you can type to search)", drug_list, index=start)

    one = signals[signals["drug"] == drug]
    c1, c2, c3 = st.columns(3)
    c1.metric("Cases with this drug", f"{int(one['drug_total'].max()):,}")
    c2.metric("Reactions analysed", f"{len(one):,}")
    c3.metric("Strong signals", f"{(one['strength'] == 'Strong').sum():,}")

    st.subheader("Most reported reactions")
    st.bar_chart(one.sort_values("a", ascending=False).head(10).set_index("reaction")["a"], horizontal=True)

    st.subheader("Strongest signals for this drug")
    top = one[one["is_signal"]].head(15)
    st.dataframe(top[["reaction", "a", "ROR", "ROR_CI_Lower", "ROR_CI_Upper", "p_value", "strength"]],
                 hide_index=True)
    if top.empty:
        st.info("No statistical signals for this drug.")

# =====================================================================
elif page == "🤖 Machine learning":
    st.title("Machine learning: predicting next-quarter signals")
    st.write("**Question:** using only the OLD quarter, can we predict which pairs become safety "
             "signals in the NEWEST quarter?")

    results = load("model_results.csv")
    st.subheader("Model comparison")
    st.dataframe(results, hide_index=True)
    st.bar_chart(results.set_index("model")["roc_auc"])
    st.info("**ROC-AUC** (0.5 = guessing, 1.0 = perfect). A model is only useful if it beats the "
            "baseline in the first row.")

    left, right = st.columns(2)
    with left:
        st.subheader("Which features matter?")
        st.bar_chart(load("feature_importance.csv").set_index("feature"), horizontal=True)
    with right:
        st.subheader("Watchlist")
        st.write("Pairs that are **not** signals yet but the model thinks are likely to become one.")
        st.dataframe(load("watchlist.csv").head(20), hide_index=True)

# =====================================================================
else:
    st.title("About this project")
    st.markdown("""
**Data:** FDA Adverse Event Reporting System (FAERS), 2026 Q1 and Q2.

**Pipeline**
1. **Data processing** - clean, remove duplicates and deleted cases, keep the primary suspect drug
2. **Statistical analysis** - Reporting Odds Ratio (ROR), PRR, 95% confidence interval, chi-square test
3. **Machine learning** - predict which pairs become signals next quarter
4. **Dashboard** - this app

**How to read a signal**
- **ROR = 1** means no link. **ROR = 10** means the reaction is reported 10x more often with this drug.
- **Signal rule:** ROR >= 2 and the lower end of the 95% confidence interval above 1.
- **Strong** = signal with at least 20 cases and a lower CI of at least 5.
- **Excluded** = product/dosing/device terms (not real side effects).

**Important limits**
- FAERS is voluntary reporting: under-reporting, media/lawsuit-driven reporting, and no
  count of how many people took the drug.
- A signal is a **hypothesis to investigate**, not proof that the drug causes the reaction.
""")
