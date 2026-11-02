
import requests
import pandas as pd
import streamlit as st

API_URL = "http://127.0.0.1:8000/api/signals-v7/"

st.set_page_config(
    page_title="PharmaGuard AI",
    page_icon="💊",
    layout="wide",
)

st.title("💊 PharmaGuard AI")
st.subheader("FAERS Drug Safety Signal Detection")
st.caption(
    "Explore drug–reaction statistical associations "
    "from the FAERS V7 dataset."
)

# Search controls
col1, col2 = st.columns(2)

with col1:
    drug = st.text_input("Drug name", placeholder="e.g. ASPIRIN")

with col2:
    reaction = st.text_input(
        "Reaction name", placeholder="e.g. NAUSEA"
    )

col3, col4, col5 = st.columns(3)

with col3:
    drug_match = st.selectbox(
        "Drug matching",
        ["Contains", "Starts with", "Exact"],
    )

with col4:
    signal_filter = st.selectbox(
        "Potential signal",
        ["All records", "Signals only", "Non-signals only"],
    )

with col5:
    page_size = st.selectbox(
        "Records per page", [10, 20, 50, 100]
    )

page = st.number_input(
    "Page number", min_value=1, value=1, step=1
)

# Build API parameters
params = {
    "page": int(page),
    "page_size": page_size,
}

if drug.strip():
    params["drug"] = drug.strip()
    params["drug_match"] = {
        "Contains": "contains",
        "Starts with": "prefix",
        "Exact": "exact",
    }[drug_match]

if reaction.strip():
    params["reaction"] = reaction.strip()

if signal_filter == "Signals only":
    params["signal_only"] = "true"
elif signal_filter == "Non-signals only":
    params["signal_only"] = "false"

# Fetch data from Django API
if st.button("Search signals", type="primary"):
    st.session_state["search_params"] = params

active_params = st.session_state.get("search_params", params)

try:
    with st.spinner("Loading FAERS records..."):
        response = requests.get(
            API_URL,
            params=active_params,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

    st.success("Connected to PharmaGuard AI API")

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Matching records",
        f"{data.get('total_records', 0):,}",
    )
    metric2.metric(
        "Current page",
        f"{data.get('page', 1)} / {data.get('total_pages', 0)}",
    )
    metric3.metric(
        "Records displayed",
        len(data.get("signals", [])),
    )

    records = data.get("signals", [])

    if records:
        df = pd.DataFrame(records)

        st.subheader("Drug Safety Signals")

        preferred_columns = [
            "drug_key",
            "reaction_key",
            "a",
            "drug_reports",
            "reaction_reports",
            "ROR",
            "ROR_CI_lower",
            "ROR_CI_upper",
            "potential_signal",
        ]

        display_columns = [
            column for column in preferred_columns
            if column in df.columns
        ]
        # Dashboard charts
        st.subheader("📊 Signal Analysis")

        chart1, chart2 = st.columns(2)

        with chart1:
            st.write("Potential Signal Distribution")

            signal_counts = (
                df["potential_signal"]
                .map({True: "Potential Signal", False: "Non-Signal"})
                .value_counts()
            )

            st.bar_chart(signal_counts)

        with chart2:
            st.write("Top ROR Values — Current Page")

            top_ror = (
                df.nlargest(10, "ROR")[
                    ["drug_key", "reaction_key", "ROR"]
                ]
                .copy()
            )

            top_ror["association"] = (
                top_ror["drug_key"].str.slice(0, 25)
                + " → "
                + top_ror["reaction_key"].str.slice(0, 25)
            )

            st.bar_chart(
                top_ror.set_index("association")["ROR"]
            )
        st.dataframe(
            df[display_columns],
            width="stretch",
            hide_index=True,
        )

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download current page as CSV",
            data=csv_data,
            file_name="pharmaguard_signals.csv",
            mime="text/csv",
        )
    else:
        st.info("No records found for these search criteria.")

    st.warning(
        data.get(
            "disclaimer",
            "Statistical signals do not establish causation."
        )
    )

except requests.exceptions.RequestException as error:
    st.error(
        "Cannot connect to the Django API. "
        "Check that the Django server is running."
    )
    st.caption(str(error))
except ValueError:
    st.error("The API returned a response that could not be read as JSON.")
