
import requests
import pandas as pd
import streamlit as st

# -------------------- API URLs --------------------

API_URL = "http://127.0.0.1:8000/api/signals-v7/"
DRUG_DIRECTORY_URL = "http://127.0.0.1:8000/api/drug-directory/"
DRUG_ANALYTICS_URL = "http://127.0.0.1:8000/api/analytics/drugs/"
DRUG_TOP_REACTIONS_URL = (
    "http://127.0.0.1:8000/api/analytics/drug-top-reactions/"
)

st.set_page_config(
    page_title="PharmaGuard AI | Drug Profile",
    page_icon="💊",
    layout="wide",
)


# -------------------- API Functions --------------------

# -------------------- API Functions --------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_profile(params_tuple):
    response = requests.get(
        API_URL,
        params=dict(params_tuple),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_drug_directory(letter, page):
    response = requests.get(
        DRUG_DIRECTORY_URL,
        params={"letter": letter, "page": page},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_drug_analytics(drug, page=1):
    response = requests.get(
        DRUG_ANALYTICS_URL,
        params={"drug": drug, "page": page},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_drug_top_reactions(drug):
    response = requests.get(
        DRUG_TOP_REACTIONS_URL,
        params={"drug": drug},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()

# -------------------- Styling --------------------

st.markdown("""
<style>
.stApp {
    background: #F4F7FB;
}

.block-container {
    max-width: 1450px;
    padding-top: 1.5rem;
}

h1, h2, h3 {
    color: #123B56;
}

[data-testid="stMetric"] {
    background: white;
    border: 1px solid #DCE7EE;
    border-radius: 12px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)


# -------------------- Header --------------------

st.title("💊 Drug Safety Profile")

st.caption(
    "Drug-specific pharmacovigilance screening | "
    "FDA FAERS 2026 Q1–Q2 | Pipeline V7"
)

st.info(
    "This page examines reported drug–event associations. "
    "A statistical signal is not proof of causation, and "
    "absence of a detected signal does not establish safety."
)

st.divider()


# -------------------- A-Z Drug Directory --------------------

st.subheader("📚 Browse Drug Directory")

st.caption(
    "Browse available FAERS drug names alphabetically "
    "and select one to view its safety profile."
)

letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

letter_col, page_col = st.columns(2)

with letter_col:
    selected_letter = st.selectbox(
        "Choose starting letter",
        letters,
        index=0,
        key="directory_letter",
    )

try:
    directory_data = fetch_drug_directory(selected_letter, 1)

    directory_total_pages = max(
        int(directory_data.get("total_pages", 1)), 1
    )

    with page_col:
        directory_page = st.selectbox(
            "Directory page",
            range(1, directory_total_pages + 1),
            key="directory_page",
        )

    directory_data = fetch_drug_directory(
        selected_letter,
        directory_page,
    )

    drug_names = directory_data.get("drugs", [])

    st.caption(
        f"Found {directory_data.get('total_drugs', 0):,} drugs | "
        f"Page {directory_page} of {directory_total_pages}"
    )

    if drug_names:
        selected_drug = st.selectbox(
            "Select a drug",
            drug_names,
            key="directory_selected_drug",
        )

        if st.button(
            "View selected drug profile",
            type="primary",
        ):
            st.session_state["profile_drug"] = selected_drug
            st.session_state["profile_page"] = 1
            st.session_state["profile_page_size"] = 50
            st.rerun()

    else:
        st.info("No drugs found for this selection.")

except requests.exceptions.RequestException as error:
    st.error("Unable to load the Drug Directory.")
    st.caption(str(error))

st.divider()


# -------------------- Drug Search --------------------

st.subheader("Search for a drug")

with st.form("drug_profile_search"):

    drug_name_input = st.text_input(
        "Drug key",
        placeholder="Enter exact drug key, e.g. DUPILUMAB",
        help="Use the drug_key spelling shown in Safety Signal Explorer.",
    ).strip().upper()

    page_size_input = st.selectbox(
        "Records per page",
        [10, 20, 50, 100],
        index=2,
    )

    submitted = st.form_submit_button(
        "View drug profile",
        type="primary",
    )

if submitted:
    if not drug_name_input:
        st.warning("Enter a drug name first.")

    else:
        st.session_state["profile_drug"] = drug_name_input
        st.session_state["profile_page"] = 1
        st.session_state["profile_page_size"] = page_size_input
        st.rerun()


# -------------------- Check Selected Drug --------------------

if "profile_drug" not in st.session_state:

    st.markdown("### How to use this page")

    st.write(
        "1. Browse the A–Z Drug Directory or enter a drug key.\n"
        "2. Select the number of records per page.\n"
        "3. View the drug profile and its associated reactions."
    )

    st.stop()


# -------------------- Load Profile Settings --------------------

drug_name = st.session_state["profile_drug"]

page = st.session_state.get("profile_page", 1)

page_size = st.session_state.get(
    "profile_page_size", 50
)


# -------------------- Drug-level Safety Summary --------------------

try:

    summary_data = fetch_drug_analytics(
        drug=drug_name,
        page=1,
    )

    summary_records = summary_data.get("results", [])

    drug_summary = next(
        (
            item for item in summary_records
            if item["drug_key"] == drug_name
        ),
        None,
    )

    if drug_summary:

        total_pairs = int(drug_summary["total_pairs"])

        total_signals = int(
            drug_summary["potential_signals"]
        )

        other_pairs = total_pairs - total_signals

        signal_percentage = (
            total_signals / total_pairs * 100
            if total_pairs > 0 else 0
        )

        st.subheader("Drug-level Safety Summary")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Drug–Event Pairs",
            f"{total_pairs:,}",
        )

        c2.metric(
            "Potential Signals",
            f"{total_signals:,}",
        )

        c3.metric(
            "Other Pairs",
            f"{other_pairs:,}",
        )

        c4.metric(
            "Potential Signal Rate",
            f"{signal_percentage:.2f}%",
        )

    else:
        st.warning(
            "Drug-level summary not found for this drug."
        )

except requests.exceptions.RequestException as error:

    st.error("Unable to load drug-level analytics.")

    st.caption(str(error))


# -------------------- Profile API Request --------------------

params = {
    "drug": drug_name,
    "drug_match": "exact",
    "page": page,
    "page_size": page_size,
}


try:

    with st.spinner(
        f"Loading profile for {drug_name}..."
    ):

        data = fetch_profile(
            tuple(sorted(params.items()))
        )

    records = data.get("signals", [])

    total_records = int(
        data.get("total_records", 0)
    )

    total_pages = int(
        data.get("total_pages", 0)
    )

    st.markdown(f"## {drug_name}")

    st.caption(
        "V7 drug–event association profile"
    )

    if not records:

        st.warning(
            "No matching records were returned. "
            "Check the drug key and try again."
        )

        st.stop()


    # -------------------- DataFrame --------------------

    df = pd.DataFrame(records)


    # -------------------- Numeric Data Cleaning --------------------

    numeric_columns = [
        "a",
        "drug_reports",
        "reaction_reports",
        "ROR",
        "ROR_CI_lower",
        "ROR_CI_upper",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )


    # -------------------- Signal Classification --------------------

    if "potential_signal" in df.columns:

        signal_flags = (
            df["potential_signal"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        )

    else:

        signal_flags = pd.Series(
            False,
            index=df.index,
        )


    # -------------------- Profile Overview --------------------

    st.subheader("Profile overview")

    if "drug_reports" in df.columns and not df.empty:

        report_count = pd.to_numeric(
            df["drug_reports"],
            errors="coerce",
        ).max()

        report_label = (
            f"{int(report_count):,}"
            if pd.notna(report_count)
            else "N/A"
        )

    else:

        report_label = "N/A"


    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Matching drug–event pairs",
        f"{total_records:,}",
    )

    k2.metric(
        "Potential signals on this page",
        f"{int(signal_flags.sum()):,}",
    )

    k3.metric(
        "Other pairs on this page",
        f"{int((~signal_flags).sum()):,}",
    )

    k4.metric(
        "Drug report count",
        report_label,
    )

    st.caption(
        "Potential signal and other-pair counts refer only "
        "to records displayed on the current page. "
        "Use the Drug-level Safety Summary above for overall totals."
    )


    # -------------------- Data Interpretation --------------------

    st.divider()

    st.subheader("Important: Data Interpretation")

    st.warning("""
    This dashboard analyzes reports submitted to the FDA Adverse
    Event Reporting System (FAERS).

    A potential safety signal indicates a statistical association
    in reported data. It does not establish that a drug caused
    an adverse event.

    FAERS data cannot determine the incidence of an adverse
    reaction or prove that a drug is safe or unsafe.

    Reporting patterns may be affected by under-reporting,
    duplicate reports, and other biases.

    These results are intended for pharmacovigilance research
    and exploratory analysis, not clinical decision-making.
    """)
    # -------------------- Top 10 Associated Reactions --------------------

    st.divider()
    st.subheader("🏆 Top 10 Associated Reactions")

    st.caption(
        "Ranked by the number of FAERS reports co-reporting "
        "the selected drug and reaction."
    )

    try:
        with st.spinner("Loading top 10 associated reactions..."):
            top_data = fetch_drug_top_reactions(drug_name)

        top_records = top_data.get("results", [])

        if top_records:
            top_df = pd.DataFrame(top_records)

            top_df["a"] = pd.to_numeric(
                top_df["a"], errors="coerce"
            )

            top_df["ROR"] = pd.to_numeric(
                top_df["ROR"], errors="coerce"
            )

            top_df["ROR_CI_lower"] = pd.to_numeric(
                top_df["ROR_CI_lower"], errors="coerce"
            )

            top_df["ROR_CI_upper"] = pd.to_numeric(
                top_df["ROR_CI_upper"], errors="coerce"
            )

            top_df["Screening status"] = (
                top_df["potential_signal"]
                .astype(str)
                .str.lower()
                .isin(["true", "1", "yes"])
                .map({
                    True: "🔴 Potential signal",
                    False: "⚪ No signal detected",
                })
            )

            top_display = top_df.rename(columns={
                "reaction_key": "Reaction",
                "a": "Co-reported cases",
                "ROR": "ROR",
                "ROR_CI_lower": "95% CI Lower",
                "ROR_CI_upper": "95% CI Upper",
            })

            top_display = top_display[
                [
                    "Reaction",
                    "Co-reported cases",
                    "ROR",
                    "95% CI Lower",
                    "95% CI Upper",
                    "Screening status",
                ]
            ]

            st.dataframe(
                top_display,
                width="stretch",
                hide_index=True,
            )

            st.caption(
                f"Showing {len(top_records)} reactions. "
                f"Ranking method: {top_data.get('ranking_method', 'Co-reported case count')}"
            )

            st.download_button(
                "Download Top 10 Reactions CSV",
                data=top_display.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name=f"{drug_name}_top_10_reactions.csv",
                mime="text/csv",
            )

        else:
            st.info(
                "No associated reactions found for this drug."
            )

    except requests.exceptions.RequestException as error:
        st.error("Unable to load Top 10 Associated Reactions.")
        st.caption(str(error))

    # -------------------- Associated Reactions --------------------

    st.subheader("Associated reactions")

    if "reaction_key" in df.columns:

        reaction_filter = st.text_input(
            "Filter reactions on this page",
            placeholder="Type a reaction name...",
        )

        view_df = df.copy()

        if reaction_filter.strip():

            view_df = view_df[
                view_df["reaction_key"]
                .astype(str)
                .str.contains(
                    reaction_filter.strip(),
                    case=False,
                    na=False,
                )
            ]


        # -------------------- ROR Chart --------------------

        if "ROR" in view_df.columns:

            chart_df = (
                view_df.dropna(subset=["ROR"])
                .nlargest(15, "ROR")
                .copy()
            )

            if not chart_df.empty:

                chart_df["Reaction"] = (
                    chart_df["reaction_key"].astype(str)
                )

                st.markdown(
                    "**Highest ROR values on this page**"
                )

                st.bar_chart(
                    chart_df.set_index("Reaction")["ROR"],
                    horizontal=True,
                )


        # -------------------- Status Table --------------------

        display_df = view_df.copy()

        if "potential_signal" in display_df.columns:

            flags = (
                display_df["potential_signal"]
                .astype(str)
                .str.lower()
                .isin(["true", "1", "yes"])
            )

            display_df.insert(
                2 if len(display_df.columns) >= 2 else 0,
                "Screening status",
                flags.map({
                    True: "🔴 Potential signal",
                    False: "⚪ No signal detected",
                }),
            )


        preferred_columns = [
            "drug_key",
            "reaction_key",
            "Screening status",
            "a",
            "drug_reports",
            "reaction_reports",
            "ROR",
            "ROR_CI_lower",
            "ROR_CI_upper",
            "potential_signal",
        ]

        columns = [
            column for column in preferred_columns
            if column in display_df.columns
        ]

        st.dataframe(
            display_df[columns],
            width="stretch",
            hide_index=True,
            height=480,
        )


        # -------------------- CSV Download --------------------

        st.download_button(
            "Download profile page as CSV",

            data=display_df.to_csv(
                index=False
            ).encode("utf-8"),

            file_name=f"{drug_name}_safety_profile.csv",

            mime="text/csv",
        )


    # -------------------- Pagination --------------------

    st.divider()

    st.subheader("Profile navigation")

    prev_col, page_col, next_col = st.columns(
        [1, 2, 1]
    )

    with prev_col:

        if st.button(
            "← Previous",
            disabled=page <= 1,
            use_container_width=True,
        ):

            st.session_state["profile_page"] = page - 1

            st.rerun()


    with page_col:

        st.write(
            f"Page **{page}** of **{max(total_pages, 1)}**"
        )


    with next_col:

        if st.button(
            "Next →",
            disabled=(
                page >= total_pages or total_pages == 0
            ),
            use_container_width=True,
        ):

            st.session_state["profile_page"] = page + 1

            st.rerun()


    st.caption(
        f"Showing {len(records):,} records out of "
        f"{total_records:,} matching drug–event pairs."
    )


    # -------------------- API Disclaimer --------------------

    st.warning(
        data.get(
            "disclaimer",
            "FAERS reporting patterns and statistical signals "
            "do not establish causation or incidence.",
        )
    )


except requests.exceptions.RequestException as error:

    st.error(
        "Unable to connect to the PharmaGuard AI API."
    )

    st.caption(str(error))


except (ValueError, TypeError, KeyError) as error:

    st.error(
        "Unable to interpret the API response."
    )

    st.caption(str(error))