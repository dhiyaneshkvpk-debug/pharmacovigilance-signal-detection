
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="PharmaGuard AI | Methodology",
    page_icon="🛡️",
    layout="wide",
)

# -------------------- Styling --------------------
st.markdown("""
<style>
.stApp { background: #F4F7FB; }
.block-container { max-width: 1450px; padding-top: 1.5rem; }
h1, h2, h3 { color: #123B56; }
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #DCE7EE;
    border-radius: 12px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)


# -------------------- Header --------------------
st.title("🛡️ Methodology & Validation")
st.caption(
    "Scientific methodology | Data quality | Statistical validation | "
    "FAERS Pipeline V7"
)

st.info(
    "This page documents the research workflow and computational "
    "validation of PharmaGuard AI. Validation confirms data-processing "
    "consistency, not clinical safety or causality."
)

st.divider()


# -------------------- Dataset overview --------------------
st.subheader("1. Dataset overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Unique FAERS reports", "792,346")
c2.metric("Drug–event pairs", "2,136,214")
c3.metric("Potential signals", "334,906")
c4.metric("Other pairs", "1,801,308")

st.caption(
    "Source: FDA FAERS 2026 Q1–Q2. Figures represent the validated "
    "V7 pipeline snapshot."
)

st.divider()


# -------------------- Data pipeline --------------------
st.subheader("2. Data processing workflow")

st.markdown("""
The V7 workflow processes the FDA FAERS quarterly ASCII datasets.

**Source tables**

- DEMO — demographic and case information
- DRUG — reported medicinal products
- REAC — reported adverse-event reactions
- OUTC — patient outcomes
- DELETE — deleted case identifiers

**Processing stages**

1. Load quarterly FAERS source files.
2. Resolve case versions and remove deleted cases.
3. Retain the latest eligible report version.
4. Normalize drug and reaction keys.
5. Generate unique drug–event reporting pairs.
6. Calculate reporting counts and disproportionality statistics.
7. Apply the potential-signal screening criteria.
8. Load the resulting records into MySQL.
""")

st.divider()


# -------------------- Statistical methodology --------------------
st.subheader("3. Statistical methodology")

st.markdown("""
For every drug–event pair, a 2 × 2 reporting contingency table is created.
""")

st.code("""
                         Event present    Event absent

Drug of interest               a                b
Other drugs                    c                d
""", language="text")

st.markdown("**Cell definitions**")

definitions = pd.DataFrame({
    "Cell": ["a", "b", "c", "d"],
    "Definition": [
        "Reports containing the drug and event",
        "Reports containing the drug without the event",
        "Reports containing the event without the drug",
        "Reports containing neither the drug nor the event",
    ],
})

st.dataframe(
    definitions,
    hide_index=True,
    width="stretch",
)

st.markdown("**Reporting Odds Ratio (ROR)**")

st.latex(r"ROR = \frac{a \times d}{b \times c}")

st.markdown("**Haldane–Anscombe correction**")

st.write(
    "A correction of 0.5 is added to each contingency-table cell "
    "for ROR and confidence-interval calculations."
)

st.latex(
    r"ROR_{corrected} = "
    r"\frac{(a+0.5)(d+0.5)}{(b+0.5)(c+0.5)}"
)

st.markdown("**Standard error of log ROR**")

st.latex(
    r"SE(\log ROR) = "
    r"\sqrt{\frac{1}{a+0.5}+\frac{1}{b+0.5}"
    r"+\frac{1}{c+0.5}+\frac{1}{d+0.5}}"
)

st.markdown("**95% confidence interval**")

st.latex(
    r"CI_{lower} = "
    r"\exp(\log(ROR)-1.96 \times SE)"
)

st.latex(
    r"CI_{upper} = "
    r"\exp(\log(ROR)+1.96 \times SE)"
)

st.divider()


# -------------------- Signal definition --------------------
st.subheader("4. Potential-signal screening criteria")

st.write(
    "A drug–event pair is marked as a potential statistical signal "
    "when all the following V7 conditions are satisfied:"
)

criteria = pd.DataFrame({
    "Condition": [
        "a ≥ 5",
        "b > 0",
        "c > 0",
        "ROR confidence interval lower bound > 1",
    ],
    "Purpose": [
        "Minimum co-reported report count",
        "Drug has reports without the event",
        "Event also occurs with other drugs",
        "Lower confidence bound exceeds 1",
    ],
})

st.dataframe(criteria, hide_index=True, width="stretch")

st.warning(
    "Potential signal detected means statistical screening criteria "
    "were met. It does not prove that the drug caused the event."
)

st.divider()


# -------------------- Validation results --------------------
st.subheader("5. V7 computational validation")

st.success("Final pipeline audit: PASS")

validation = pd.DataFrame({
    "Validation check": [
        "Database record count",
        "Signal-flag consistency",
        "Drug report count consistency",
        "Reaction report count consistency",
        "Negative contingency cells",
        "Contingency table total consistency",
        "ROR calculation audit",
        "Lower confidence interval audit",
        "Upper confidence interval audit",
        "Drug-key reconciliation",
        "Reaction-key reconciliation",
        "Independent case selection comparison",
    ],
    "Validated result": [
        "2,136,214 records",
        "0 mismatches",
        "0 mismatches",
        "0 mismatches",
        "0 negative cells",
        "0 mismatches",
        "0 mismatches above 1e-6",
        "0 mismatches",
        "0 mismatches",
        "0 mismatches",
        "0 mismatches",
        "0 differences",
    ],
    "Status": ["PASS"] * 12,
})

st.dataframe(
    validation,
    hide_index=True,
    width="stretch",
)

st.caption(
    "The ROR and confidence interval checks were independently "
    "recalculated across the database. Raw-source co-reporting counts "
    "were independently reconciled for the ten highest-frequency pairs."
)

st.divider()


# -------------------- Source reconciliation --------------------
st.subheader("6. Independent raw-source reconciliation")

source_audit = pd.DataFrame({
    "Drug": [
        "DUPILUMAB",
        "MEDROXYPROGESTERONE ACETATE",
        "DUPILUMAB",
        "DUPILUMAB",
        "DUPILUMAB",
        "DUPILUMAB",
        "TIRZEPATIDE",
        "DUPILUMAB",
        "DUPILUMAB",
        "DUPILUMAB",
    ],
    "Reaction": [
        "PRURITUS",
        "MENINGIOMA",
        "DERMATITIS ATOPIC",
        "INJECTION SITE PAIN",
        "PRODUCT USE IN UNAPPROVED INDICATION",
        "RASH",
        "NAUSEA",
        "ECZEMA",
        "PRODUCT DOSE OMISSION ISSUE",
        "DRY SKIN",
    ],
    "Co-reported reports (a)": [
        12141, 9668, 8901, 7296, 6228,
        6209, 5517, 5384, 5035, 5014,
    ],
})

st.dataframe(
    source_audit,
    hide_index=True,
    width="stretch",
)

st.caption(
    "These ten high-frequency pairs were reconciled against the "
    "raw-source data. This is not an exhaustive raw-source "
    "reconciliation of all 2,136,214 pairs."
)

st.divider()


# -------------------- Interpretation --------------------
st.subheader("7. Interpretation and limitations")

st.markdown("""
**What PharmaGuard AI can do**

- Identify drug–event reporting disproportionality.
- Rank potential signals for further investigation.
- Explore reported drug–reaction associations.
- Support pharmacovigilance research and data exploration.

**What PharmaGuard AI cannot establish**

- Whether a drug caused a reported event.
- The true incidence or prevalence of an adverse reaction.
- Whether a drug is clinically safe or unsafe.
- Individual patient risk or treatment recommendations.

**Important FAERS limitations**

- Spontaneous reports may be incomplete or duplicated.
- Reporting is affected by publicity and reporting behaviour.
- Missing information can affect statistical comparisons.
- Confounding and reporting bias may influence associations.
""")

st.divider()


# -------------------- Technical information --------------------
st.subheader("8. Technical architecture")

architecture = pd.DataFrame({
    "Component": [
        "Data source",
        "Processing",
        "Database",
        "Backend API",
        "Frontend",
        "Statistical method",
    ],
    "Technology": [
        "FDA FAERS 2026 Q1–Q2",
        "Python, Pandas, NumPy",
        "MySQL",
        "Django REST Framework",
        "Streamlit",
        "ROR and 95% confidence interval",
    ],
})

st.dataframe(
    architecture,
    hide_index=True,
    width="stretch",
)

st.divider()

st.markdown("### Project validation summary")
st.success(
    "V7 computational validation passed. "
    "Results are suitable for exploratory pharmacovigilance analysis "
    "with the limitations described above."
)

st.caption(
    "PharmaGuard AI | Pipeline V7 | Research and educational use"
)
