
from django.urls import path

from .views import (
    home,
    drug_list,
    drug_create,
    safety_signals,
    safety_signal_summary,
    drug_safety_details,
    dashboard,
    safety_signals_v7,
    analytics_overview,
    analytics_drugs,
    analytics_reactions,
    drug_directory,
    drug_top_reactions,
)

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", dashboard, name="dashboard"),

    path("drugs/", drug_list, name="drug-list"),
    path("drugs/create/", drug_create, name="drug-create"),

    path("signals/", safety_signals, name="safety-signals"),
    path("signals/summary/", safety_signal_summary, name="safety-signal-summary"),
    path("drug-safety/", drug_safety_details, name="drug-safety-details"),
    path("signals-v7/", safety_signals_v7, name="safety-signals-v7"),

    # Full dataset analytics
    path("analytics/overview/", analytics_overview, name="analytics-overview"),
    path("analytics/drugs/", analytics_drugs, name="analytics-drugs"),
    path("analytics/reactions/", analytics_reactions, name="analytics-reactions"),
    path("drug-directory/", drug_directory, name="drug-directory"),

    # Drug-specific top reactions
    path("analytics/drug-top-reactions/", drug_top_reactions, name="drug-top-reactions"),
]
