
import requests
import streamlit as st
import pandas as pd

# --------------------------------------------------
# PharmaGuard AI | Command Center
# --------------------------------------------------
st.set_page_config(
    page_title="PharmaGuard AI | Command Center",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://127.0.0.1:8000/api/signals-v7/"

# Validated V7 dataset snapshot
TOTAL_REPORTS = 792_346
TOTAL_PAIRS = 2_136_214
POTENTIAL_SIGNALS = 334_906
NON_SIGNALS = 1_801_308

SIGNAL_RATE = POTENTIAL_SIGNALS / TOTAL_PAIRS * 100

# --------------------------------------------------
# Premium healthcare styling
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F7FB;
    }

    [data-testid="stSidebar"] {
        background-color: #10243A;
    }

    [data-testid="stSidebar"] * {
        color: #F3F7FC;
    }

    .hero {
        background: linear-gradient(120deg, #10243A, #174B61);
        padding: 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 22px;
    }

    .hero h1 {
        color: white;
        font-size: 34px;
        margin-bottom: 8px;
    }

    .hero p {
        color: #DCEAF1;
        font-size: 15px;
        margin-bottom: 0;
    }

    .section-title {
        color: #16364D;
        font-size: 22px;
        font-weight: 700;
        margin-top: 12px;
        margin-bottom: 8px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #E1E8F0;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(16, 36, 58, 0.04);
    }

    .status-card {
        background: white;
        border: 1px solid #E1E8F0;
        border-radius: 14px;
        padding: 18px;
        min-height: 120px;
    }

    .status-card h4 {
        color: #16364D;
        margin-top: 0;
    }

    .muted {
        color: #627487;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.markdown("## 💊 PharmaGuard AI")
    st.caption("PHARMACOVIGILANCE INTELLIGENCE")
    st.divider()

    st.markdown("### Navigation")
    st.markdown("🏠 **Command Center**")
    st.markdown("🔎 Safety Signal Explorer")
    st.markdown("🧬 Drug Safety Profile")
    st.markdown("📊 Evidence & Analytics")
    st.markdown("🛡️ Methodology & Validation")

    st.divider()
    st.caption("Data source: FDA FAERS")
    st.caption("Pipeline: V7")
    st.caption("Coverage: 2026 Q1–Q2")

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>💊 PharmaGuard AI</h1>
        <p>Pharmacovigilance Intelligence Command Center</p>
        <p>Explore drug–event reporting patterns and statistical safety signals.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# API status
# --------------------------------------------------
api_online = False
api_message = "API status could not be verified."

try:
    response = requests.get(
        API_URL,
        params={"page": 1, "page_size": 1},
        timeout=5,
    )
    response.raise_for_status()
    api_online = True
    api_message = "Django REST API responded successfully."
except requests.RequestException:
    api_message = (
        "Django REST API is not reachable. "
        "Start your Django server to enable live page access."
    )

if api_online:
    st.success(f"● API Connected — {api_message}")
else:
    st.warning(f"● API Offline — {api_message}")

# --------------------------------------------------
# Dataset snapshot
# --------------------------------------------------
st.markdown(
    '<div class="section-title">Safety Intelligence Overview</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Validated V7 dataset snapshot. These totals describe the "
    "validated pipeline dataset, not the current API page."
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Unique Reports", f"{TOTAL_REPORTS:,}")

with c2:
    st.metric("Drug–Event Pairs", f"{TOTAL_PAIRS:,}")

with c3:
    st.metric("Potential Signals", f"{POTENTIAL_SIGNALS:,}")

with c4:
    st.metric("No Signal Detected", f"{NON_SIGNALS:,}")

st.divider()

# --------------------------------------------------
# Signal distribution
# --------------------------------------------------
left, right = st.columns([1.2, 1])

with left:
    st.markdown(
        '<div class="section-title">Signal Screening Distribution</div>',
        unsafe_allow_html=True,
    )

    distribution = pd.DataFrame(
        {
            "Screening outcome": [
                "Potential signal detected",
                "No signal detected by this screen",
            ],
            "Drug–event pairs": [
                POTENTIAL_SIGNALS,
                NON_SIGNALS,
            ],
        }
    ).set_index("Screening outcome")

    st.bar_chart(distribution, horizontal=True)

    st.caption(
        f"{SIGNAL_RATE:.2f}% of screened drug–event pairs met "
        "the V7 statistical signal criteria."
    )

with right:
    st.markdown(
        '<div class="section-title">Signal Status Guide</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="status-card">
            <h4>🔴 Potential signal detected</h4>
            <p class="muted">
            A pair met the configured statistical screening criteria.
            It requires scientific assessment; it is not proof of harm.
            </p>
        </div>
        <br>
        <div class="status-card">
            <h4>⚪ No signal detected by this screen</h4>
            <p class="muted">
            The pair did not meet the configured screening criteria.
            This does not establish that the drug is safe.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# --------------------------------------------------
# Navigation guidance
# --------------------------------------------------
st.markdown(
    '<div class="section-title">Explore PharmaGuard AI</div>',
    unsafe_allow_html=True,
)

p1, p2 = st.columns(2)

with p1:
    st.markdown("### 🔎 Safety Signal Explorer")
    st.write(
        "Search drug names and reactions, review reporting counts, "
        "and explore ROR-based potential signals."
    )
    st.page_link(
        "pages/02_Safety_Signal_Explorer.py",
        label="Open Signal Explorer",
        icon="🔎",
    )

    st.markdown("### 🧬 Drug Safety Profile")
    st.write(
        "Review drug-specific reporting patterns and associated "
        "reactions as the profile page is developed."
    )
    st.page_link(
        "pages/03_Drug_Safety_Profile.py",
        label="Open Drug Profile",
        icon="🧬",
    )

with p2:
    st.markdown("### 📊 Evidence & Analytics")
    st.write(
        "Explore statistical evidence and reporting distributions."
    )
    st.page_link(
        "pages/04_Evidence_Analytics.py",
        label="Open Evidence Analytics",
        icon="📊",
    )

    st.markdown("### 🛡️ Methodology & Validation")
    st.write(
        "Review the screening rules, validation checks, "
        "and interpretation limitations."
    )
    st.page_link(
        "pages/05_Methodology_Validation.py",
        label="Open Methodology",
        icon="🛡️",
    )

st.divider()

st.info(
    "**Important research disclaimer:** FDA FAERS contains spontaneous "
    "reports and has reporting limitations. Reporting counts and "
    "disproportionality statistics do not establish causality, incidence, "
    "or whether a drug is safe or unsafe. Clinical review is required."
)

st.caption(
    "PharmaGuard AI • FAERS 2026 Q1–Q2 • V7 pipeline snapshot"
)
