
"use strict";

// PharmaGuard AI - Frontend and Django API connection

const API = {
    summary: "/api/signals/summary/",
    signals: "/api/signals/",
    drugSafety: "/api/drug-safety/"
};

const state = {
    drug: "",
    page: 1,
    pageSize: 10,
    totalPages: 0,
    loading: false
};

const elements = {
    apiStatus: document.getElementById("api-status"),
    statusDot: document.querySelector(".status-dot"),

    totalRecords: document.getElementById("total-records"),
    signalCount: document.getElementById("signal-count"),
    otherCount: document.getElementById("other-count"),

    refreshButton: document.getElementById("refresh-btn"),
    searchForm: document.getElementById("drug-search-form"),
    drugName: document.getElementById("drug-name"),
    searchMessage: document.getElementById("search-message"),

    signalOnly: document.getElementById("signal-only"),
    resultsDescription: document.getElementById("results-description"),
    tableBody: document.getElementById("signals-table-body"),

    previousPage: document.getElementById("previous-page"),
    nextPage: document.getElementById("next-page"),
    pageInfo: document.getElementById("page-info")
};


// Safely display text.
function setText(element, value) {
    if (element) {
        element.textContent = value;
    }
}


// Format numbers using Indian number grouping.
function formatNumber(value) {
    if (value === null || value === undefined || value === "") {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toLocaleString("en-IN", {
        maximumFractionDigits: 2
    });
}


// Validate the drug name before making an API request.
function validateDrugName(drugName) {
    const name = drugName.trim();

    if (!name) {
        return "Please enter a drug name.";
    }

    if (name.length < 2) {
        return "Enter at least 2 characters.";
    }

    if (name.length > 100) {
        return "Drug name is too long.";
    }

    return "";
}


// Make a GET request to the Django API.
async function apiGet(url) {
    const response = await fetch(url, {
        method: "GET",
        headers: {
            "Accept": "application/json"
        }
    });

    if (!response.ok) {
        throw new Error(`API request failed: HTTP ${response.status}`);
    }

    return response.json();
}


// Update the API connection indicator.
function setApiStatus(connected, message) {
    setText(elements.apiStatus, message);

    if (elements.statusDot) {
        elements.statusDot.style.backgroundColor =
            connected ? "#059669" : "#dc2626";
    }
}


// Load summary cards.
async function loadSummary() {
    const data = await apiGet(API.summary);

    setText(elements.totalRecords, formatNumber(data.total_records));
    setText(
        elements.signalCount,
        formatNumber(data.identified_safety_signals)
    );
    setText(elements.otherCount, formatNumber(data.other_records));
}


// Display a message inside the results table.
function showTableMessage(message) {
    if (!elements.tableBody) return;

    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = 6;
    cell.textContent = message;

    row.appendChild(cell);
    elements.tableBody.replaceChildren(row);
}


// Create a safe text-only table cell.
function createCell(value) {
    const cell = document.createElement("td");
    cell.textContent =
        value === null || value === undefined || value === ""
            ? "—"
            : String(value);

    return cell;
}


// Render safety signal records.
function renderSignals(signals) {
    elements.tableBody.replaceChildren();

    if (!Array.isArray(signals) || signals.length === 0) {
        showTableMessage("No matching records found.");
        return;
    }

    const fragment = document.createDocumentFragment();

    signals.forEach((signal) => {
        const row = document.createElement("tr");

        const confidenceInterval =
            `${formatNumber(signal.ROR_CI_Lower)} – ` +
            `${formatNumber(signal.ROR_CI_Upper)}`;

        row.appendChild(createCell(signal.drugname_clean));
        row.appendChild(createCell(signal.side_effect));
        row.appendChild(createCell(formatNumber(signal.a)));
        row.appendChild(createCell(formatNumber(signal.ROR)));
        row.appendChild(createCell(confidenceInterval));

        const statusCell = document.createElement("td");
        const badge = document.createElement("span");

        badge.textContent = signal.is_safety_signal
            ? "Potential signal"
            : "Not flagged";

        badge.style.display = "inline-block";
        badge.style.padding = "4px 8px";
        badge.style.borderRadius = "6px";
        badge.style.fontSize = "11px";
        badge.style.fontWeight = "600";

        if (signal.is_safety_signal) {
            badge.style.backgroundColor = "#d1fae5";
            badge.style.color = "#065f46";
        } else {
            badge.style.backgroundColor = "#e2e8f0";
            badge.style.color = "#475569";
        }

        statusCell.appendChild(badge);
        row.appendChild(statusCell);
        fragment.appendChild(row);
    });

    elements.tableBody.appendChild(fragment);
}


// Update pagination controls.
function updatePagination(data) {
    state.page = Number(data.page) || 1;
    state.pageSize = Number(data.page_size) || state.pageSize;
    state.totalPages = Number(data.total_pages) || 0;

    setText(
        elements.pageInfo,
        `Page ${state.page} of ${state.totalPages}`
    );

    elements.previousPage.disabled =
        state.loading || state.page <= 1;

    elements.nextPage.disabled =
        state.loading ||
        state.totalPages === 0 ||
        state.page >= state.totalPages;
}


// Enable or disable controls during a request.
function setLoading(isLoading) {
    state.loading = isLoading;

    if (elements.searchForm) {
        const submitButton = elements.searchForm.querySelector(
            'button[type="submit"], input[type="submit"]'
        );

        if (submitButton) {
            submitButton.disabled = isLoading;
        }
    }

    if (elements.refreshButton) {
        elements.refreshButton.disabled = isLoading;
    }

    if (elements.previousPage) {
        elements.previousPage.disabled = isLoading || state.page <= 1;
    }

    if (elements.nextPage) {
        elements.nextPage.disabled =
            isLoading ||
            state.totalPages === 0 ||
            state.page >= state.totalPages;
    }

    if (elements.signalOnly) {
        elements.signalOnly.disabled = isLoading;
    }
}


// Load records from the appropriate endpoint.
async function loadResults() {
    setLoading(true);

    showTableMessage("Loading safety records...");
    setText(elements.searchMessage, "Loading safety records...");
    setText(elements.resultsDescription, "Retrieving records from the API.");

    try {
        const endpoint = new URL(
            state.drug ? API.drugSafety : API.signals,
            window.location.origin
        );

        endpoint.searchParams.set("page", String(state.page));
        endpoint.searchParams.set("page_size", String(state.pageSize));

        if (state.drug) {
            endpoint.searchParams.set("drug", state.drug);
        }

        if (elements.signalOnly.checked) {
            endpoint.searchParams.set("signal_only", "true");
        }

        const data = await apiGet(endpoint.pathname + endpoint.search);

        if (!Array.isArray(data.signals)) {
            throw new Error("Unexpected API response: signals list missing.");
        }

        renderSignals(data.signals);
        updatePagination(data);

        if (state.drug) {
            const total = Number(data.total_matches) || 0;

            setText(
                elements.resultsDescription,
                `${formatNumber(total)} matching records for ${state.drug}`
            );

            setText(
                elements.searchMessage,
                total > 0
                    ? `Found ${formatNumber(total)} matching records.`
                    : `No records found for ${state.drug}.`
            );
        } else {
            setText(
                elements.resultsDescription,
                `${formatNumber(data.total_records)} total records`
            );

            setText(
                elements.searchMessage,
                "Showing safety records from the database."
            );
        }
    } catch (error) {
        console.error("Could not load safety records:", error);

        showTableMessage(
            "Could not load records. Please check the API and try again."
        );

        setText(
            elements.searchMessage,
            "Unable to load results. Please try again."
        );

        setText(elements.resultsDescription, "Unable to retrieve results.");

        state.totalPages = 0;

        if (elements.previousPage) {
            elements.previousPage.disabled = true;
        }

        if (elements.nextPage) {
            elements.nextPage.disabled = true;
        }

        setText(elements.pageInfo, "Page unavailable");
    } finally {
        setLoading(false);
        updatePaginationAfterRequest();
    }
}


// Restore pagination button states after loading finishes.
function updatePaginationAfterRequest() {
    if (elements.previousPage) {
        elements.previousPage.disabled =
            state.loading || state.page <= 1;
    }

    if (elements.nextPage) {
        elements.nextPage.disabled =
            state.loading ||
            state.totalPages === 0 ||
            state.page >= state.totalPages;
    }
}


// Refresh summary cards and results.
async function refreshDashboard() {
    if (state.loading) return;

    try {
        await loadSummary();
        setApiStatus(true, "API Connected");
    } catch (error) {
        console.error("Could not load dashboard summary:", error);
        setApiStatus(false, "API Unavailable");

        setText(elements.totalRecords, "—");
        setText(elements.signalCount, "—");
        setText(elements.otherCount, "—");
    }

    await loadResults();
}


// Handle drug search and validation.
elements.searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (state.loading) return;

    const drugName = elements.drugName.value.trim();
    const validationError = validateDrugName(drugName);

    if (validationError) {
        setText(elements.searchMessage, validationError);
        elements.drugName.focus();
        return;
    }

    state.drug = drugName;
    state.page = 1;

    await loadResults();
});


// Filter potential safety signals.
elements.signalOnly.addEventListener("change", async () => {
    if (state.loading) return;

    state.page = 1;
    await loadResults();
});


// Previous page.
elements.previousPage.addEventListener("click", async () => {
    if (state.loading || state.page <= 1) return;

    state.page -= 1;
    await loadResults();
});


// Next page.
elements.nextPage.addEventListener("click", async () => {
    if (state.loading || state.page >= state.totalPages) return;

    state.page += 1;
    await loadResults();
});


// Refresh dashboard.
elements.refreshButton.addEventListener("click", refreshDashboard);


// Initial dashboard load.
refreshDashboard();
