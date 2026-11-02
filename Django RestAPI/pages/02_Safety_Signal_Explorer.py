
import math
import requests
import pandas as pd
import streamlit as st

API_URL = "http://127.0.0.1:8000/api/signals-v7/"

st.set_page_config(
    page_title="PharmaGuard AI | Signal Explorer",
    page_icon="💊",
    layout="wide",
)

@st.cache_data(ttl=60, show_spinner=False)
def fetch_signals(page_params):
    response = requests.get(
        API_URL,
        params=dict(page_params),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


# -------------------- Styling --------------------
st.markdown("""
<style>
.stApp { background: #F4F7FB; }
.block-container { max-width: 1500px; padding-top: 1.5rem; }
h1, h2, h3 { color: #123B56; }
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #DCE7EE;
    border-radius: 12px;
    padding: 14px;
}
</style>
""", unsafe_allow_html=True)


# -------------------- Session state --------------------
if "search_params" not in st.session_state:
    st.session_state.search_params = {
        "page": 1,
        "page_size": 20,
    }

if "drug_input" not in st.session_state:
    st.session_state.drug_input = ""

if "reaction_input" not in st.session_state:
    st.session_state.reaction_input = ""

if "drug_match_input" not in st.session_state:
    st.session_state.drug_match_input = "Contains"

if "signal_filter_input" not in st.session_state:
    st.session_state.signal_filter_input = "All records"

if "page_size_input" not in st.session_state:
    st.session_state.page_size_input = 20

if "letter_input" not in st.session_state:
    st.session_state.letter_input = "All letters"


def set_page(new_page):
    current = dict(st.session_state.search_params)
    current["page"] = max(1, int(new_page))
    st.session_state.search_params = current


def apply_search():
    params = {
        "page": 1,
        "page_size": st.session_state.page_size_input,
    }

    drug = st.session_state.drug_input.strip()
    reaction = st.session_state.reaction_input.strip()
    letter = st.session_state.letter_input

    if letter != "All letters":
        # Alphabet selection takes priority over the text field.
        params["drug"] = letter
        params["drug_match"] = "prefix"
    elif drug:
        params["drug"] = drug
        params["drug_match"] = {
            "Contains": "contains",
            "Starts with": "prefix",
            "Exact": "exact",
        }[st.session_state.drug_match_input]

    if reaction:
        params["reaction"] = reaction

    if st.session_state.signal_filter_input == "Signals only":
        params["signal_only"] = "true"
    elif st.session_state.signal_filter_input == "Non-signals only":
        params["signal_only"] = "false"

    st.session_state.search_params = params


# -------------------- Header --------------------
st.title("💊 PharmaGuard AI")
st.subheader("Safety Signal Explorer")
st.caption(
    "FDA FAERS 2026 Q1–Q2 | Pipeline V7 | "
    "Drug–Event Disproportionality Analysis"
)
st.info(
    "A potential signal is a statistical screening result, "
    "not proof that a medicine causes harm."
)

# -------------------- Search filters --------------------
st.markdown("### Search and filter")

c1, c2 = st.columns(2)

with c1:
    st.text_input(
        "Drug name",
        key="drug_input",
        placeholder="e.g. ASPIRIN",
    )

with c2:
    st.text_input(
        "Reaction name",
        key="reaction_input",
        placeholder="e.g. NAUSEA",
    )

c3, c4, c5 = st.columns(3)

with c3:
    st.selectbox(
        "Drug matching",
        ["Contains", "Starts with", "Exact"],
        key="drug_match_input",
    )

with c4:
    st.selectbox(
        "Signal status",
        ["All records", "Signals only", "Non-signals only"],
        key="signal_filter_input",
    )

with c5:
    st.selectbox(
        "Records per page",
        [10, 20, 50, 100],
        key="page_size_input",
    )

st.selectbox(
    "Browse drugs alphabetically",
    ["All letters"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    key="letter_input",
    help="Choose a letter to search drug keys starting with that letter.",
)

st.button(
    "🔎 Search signals",
    type="primary",
    on_click=apply_search,
)

# -------------------- Fetch results --------------------
try:
    with st.spinner("Loading safety signal records..."):
        data = fetch_signals(
            tuple(sorted(st.session_state.search_params.items()))
        )

    total_records = int(data.get("total_records", 0))
    current_page = int(data.get("page", 1))
    total_pages = int(data.get("total_pages", 0))
    records = data.get("signals", [])

    st.success("Connected to the PharmaGuard AI API")

    m1, m2, m3 = st.columns(3)
    m1.metric("Matching records", f"{total_records:,}")
    m2.metric(
        "Page",
        f"{current_page} / {max(total_pages, 1)}",
    )
    m3.metric("Records displayed", f"{len(records):,}")

    # -------------------- Pagination --------------------
    st.markdown("### Page navigation")

    prev_col, page_col, next_col = st.columns([1, 2, 1])

    with prev_col:
        st.button(
            "← Previous",
            disabled=(current_page <= 1),
            use_container_width=True,
            on_click=set_page,
            args=(current_page - 1,),
        )

    with page_col:
        page_options = list(range(1, max(total_pages, 1) + 1))
        selected_page = st.selectbox(
            "Go to page",
            page_options,
            index=min(current_page - 1, len(page_options) - 1),
            key="page_selector",
        )

        if selected_page != current_page:
            set_page(selected_page)
            st.rerun()

    with next_col:
        st.button(
            "Next →",
            disabled=(current_page >= total_pages or total_pages == 0),
            use_container_width=True,
            on_click=set_page,
            args=(current_page + 1,),
        )

    if records:
        df = pd.DataFrame(records)

        # Normalise signal flags for reliable markers.
        if "potential_signal" in df.columns:
            signal_bool = (
                df["potential_signal"]
                .astype(str)
                .str.lower()
                .isin(["true", "1", "yes"])
            )

            df["Signal status"] = signal_bool.map({
                True: "🔴 Potential signal",
                False: "⚪ No signal detected",
            })

        st.markdown("### Statistical signal results")

        # Charts use numeric ROR values where available.
        chart1, chart2 = st.columns(2)

        with chart1:
            st.markdown("**Signal distribution — current page**")
            if "potential_signal" in df.columns:
                counts = (
                    df["potential_signal"]
                    .astype(str)
                    .str.lower()
                    .isin(["true", "1", "yes"])
                    .map({
                        True: "Potential signal",
                        False: "No signal detected",
                    })
                    .value_counts()
                )
                st.bar_chart(counts)

        with chart2:
            st.markdown("**Highest ROR values — current page**")
            if {"drug_key", "reaction_key", "ROR"}.issubset(df.columns):
                df["ROR"] = pd.to_numeric(df["ROR"], errors="coerce")
                top = df.nlargest(10, "ROR").dropna(subset=["ROR"]).copy()

                if not top.empty:
                    top["Drug → reaction"] = (
                        top["drug_key"].astype(str).str.slice(0, 24)
                        + " → "
                        + top["reaction_key"].astype(str).str.slice(0, 24)
                    )
                    st.bar_chart(
                        top.set_index("Drug → reaction")["ROR"]
                    )
                else:
                    st.caption("No numeric ROR values on this page.")

        preferred_columns = [
            "drug_key",
            "reaction_key",
            "Signal status",
            "a",
            "drug_reports",
            "reaction_reports",
            "ROR",
            "ROR_CI_lower",
            "ROR_CI_upper",
            "potential_signal",
        ]

        display_columns = [
            c for c in preferred_columns if c in df.columns
        ]

        st.dataframe(
            df[display_columns],
            width="stretch",
            hide_index=True,
            height=520,
        )

        st.download_button(
            "⬇ Download current page as CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"pharmaguard_signals_page_{current_page}.csv",
            mime="text/csv",
        )
    else:
        st.info("No records found for these search criteria.")

    st.warning(
        data.get(
            "disclaimer",
            "Statistical signals do not establish causation or incidence.",
        )
    )

except requests.exceptions.RequestException as error:
    st.error(
        "Cannot connect to the Django API. "
        "Confirm that the Django server is running."
    )
    st.caption(str(error))

except (ValueError, TypeError, KeyError) as error:
    st.error("Could not interpret the API response.")
    st.caption(str(error))