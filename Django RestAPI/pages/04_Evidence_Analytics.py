
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Evidence Analytics | PharmaGuard AI",
    page_icon="📊",
    layout="wide"
)

BASE_URL = "http://127.0.0.1:8000/api"

st.title("📊 Evidence Analytics")
st.caption(
    "Full-dataset analytics from FDA FAERS V7 "
    "| Exploratory pharmacovigilance intelligence"
)

# --------------------------------------------------
# API FUNCTIONS
# --------------------------------------------------

@st.cache_data(ttl=300)
def fetch_api(endpoint):
    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        timeout=120
    )
    response.raise_for_status()
    return response.json()


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

try:
    overview = fetch_api("analytics/overview/")
    drug_data = fetch_api("analytics/drugs/")
    reaction_data = fetch_api("analytics/reactions/")

except requests.exceptions.RequestException as error:
    st.error(f"Unable to connect to PharmaGuard API: {error}")
    st.info(
        "Make sure Django is running at "
        "http://127.0.0.1:8000/"
    )
    st.stop()

# --------------------------------------------------
# DATASET OVERVIEW
# --------------------------------------------------

st.subheader("Full Dataset Overview")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Drug–Reaction Pairs",
    f"{overview['total_drug_reaction_pairs']:,}"
)

col2.metric(
    "Potential Signal Pairs",
    f"{overview['potential_signals']:,}"
)

col3.metric(
    "Non-Signal Pairs",
    f"{overview['non_signals']:,}"
)

col4, col5, col6 = st.columns(3)

col4.metric(
    "Unique Drugs",
    f"{overview['unique_drugs']:,}"
)

col5.metric(
    "Unique Reactions",
    f"{overview['unique_reactions']:,}"
)

col6.metric(
    "Potential Signal Rate",
    f"{overview['signal_rate_percent']}%"
)

st.divider()

# --------------------------------------------------
# SIGNAL DISTRIBUTION
# --------------------------------------------------

st.subheader("Potential Signal Distribution")

distribution = pd.DataFrame({
    "Category": ["Potential Signals", "Other Pairs"],
    "Records": [
        overview["potential_signals"],
        overview["non_signals"]
    ]
})

fig_distribution = px.pie(
    distribution,
    names="Category",
    values="Records",
    hole=0.55,
    title="FAERS V7 Drug–Reaction Pair Distribution"
)

st.plotly_chart(
    fig_distribution,
    use_container_width=True
)

st.divider()

# --------------------------------------------------
# GLOBAL DRUG RANKINGS
# --------------------------------------------------

st.subheader("Top Drugs by Potential Signal Pair Count")

st.caption(
    "Rankings cover the full dataset. Counts represent "
    "flagged drug–reaction pairs, not clinical risk."
)

drug_df = pd.DataFrame(drug_data["results"])

if not drug_df.empty:

    top_drugs = drug_df.head(10).sort_values(
        "potential_signals",
        ascending=True
    )

    fig_drugs = px.bar(
        top_drugs,
        x="potential_signals",
        y="drug_key",
        orientation="h",
        text="potential_signals",
        title="Top 10 Drugs — Flagged Pair Counts",
        labels={
            "drug_key": "Drug",
            "potential_signals": "Potential Signal Pairs"
        }
    )

    st.plotly_chart(
        fig_drugs,
        use_container_width=True
    )

    with st.expander("View top 50 drug records"):
        st.dataframe(
            drug_df,
            use_container_width=True,
            hide_index=True
        )

st.divider()

# --------------------------------------------------
# GLOBAL REACTION RANKINGS
# --------------------------------------------------

st.subheader("Top Reactions by Potential Signal Pair Count")

reaction_df = pd.DataFrame(reaction_data["results"])

if not reaction_df.empty:

    top_reactions = reaction_df.head(10).sort_values(
        "potential_signals",
        ascending=True
    )

    fig_reactions = px.bar(
        top_reactions,
        x="potential_signals",
        y="reaction_key",
        orientation="h",
        text="potential_signals",
        title="Top 10 Reactions — Flagged Pair Counts",
        labels={
            "reaction_key": "Adverse Event",
            "potential_signals": "Potential Signal Pairs"
        }
    )

    st.plotly_chart(
        fig_reactions,
        use_container_width=True
    )

    with st.expander("View top 50 reaction records"):
        st.dataframe(
            reaction_df,
            use_container_width=True,
            hide_index=True
        )

st.divider()

# --------------------------------------------------
# A-Z DRUG DIRECTORY
# --------------------------------------------------

st.subheader("A–Z Drug Directory")

letter = st.selectbox(
    "Select starting letter",
    ["All"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
)

directory_page = st.number_input(
    "Directory page",
    min_value=1,
    value=1,
    step=1
)

try:
    params = {"page": int(directory_page)}

    if letter != "All":
        params["letter"] = letter

    directory_response = requests.get(
        f"{BASE_URL}/drug-directory/",
        params=params,
        timeout=120
    )

    directory_response.raise_for_status()
    directory_data = directory_response.json()

    st.write(
        f"**Total matching drugs:** "
        f"{directory_data['total_drugs']:,}"
    )

    st.write(
        f"**Page:** {directory_data['page']} "
        f"of {directory_data['total_pages']}"
    )

    directory_df = pd.DataFrame({
        "Drug Name": directory_data["drugs"]
    })

    st.dataframe(
        directory_df,
        use_container_width=True,
        hide_index=True
    )

except requests.exceptions.RequestException as error:
    st.error(f"Drug directory error: {error}")

# --------------------------------------------------
# DISCLAIMER
# --------------------------------------------------

st.divider()

st.warning(
    "Scientific disclaimer: FAERS is a spontaneous adverse-event "
    "reporting database. Potential statistical signals are exploratory "
    "associations. They do not establish causality, incidence, "
    "or clinical safety."
)

st.caption("PharmaGuard AI | FAERS V7 | Evidence Analytics")
