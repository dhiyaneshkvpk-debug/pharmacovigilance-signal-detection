from math import ceil

from django.db.models import Q, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)

from .models import Drugs, SafetySignal
from .serializers import DrugsSerializer
from django.shortcuts import render
from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from PharmaGuard_AI.models import FaersSignalV7

# --------------------------------------------------
# HOME API
# GET /api/
# --------------------------------------------------

@extend_schema(
    summary="API home",
    description="Returns basic PharmaGuard AI API information.",
    tags=["general"],
    responses={200: dict},
)
@api_view(["GET"])
def home(request):
    return Response({
        "message": "Welcome to PharmaGuard AI API!",
        "status": "success",
        "project": "FDA FAERS Pharmacovigilance",
    })


# --------------------------------------------------
# LIST DRUGS
# GET /api/drugs/
# --------------------------------------------------

@extend_schema(
    summary="List drugs",
    description="Returns the drugs stored in the database.",
    tags=["drugs"],
    responses={200: DrugsSerializer(many=True)},
)
@api_view(["GET"])
def drug_list(request):
    drugs = Drugs.objects.all()
    serializer = DrugsSerializer(drugs, many=True)
    return Response(serializer.data)


# --------------------------------------------------
# CREATE DRUG
# POST /api/drugs/create/
# --------------------------------------------------

@extend_schema(
    summary="Create a drug",
    description="Validates and creates a drug record.",
    tags=["drugs"],
    request=DrugsSerializer,
    responses={
        201: DrugsSerializer,
        400: OpenApiResponse(description="Invalid input."),
    },
)
@api_view(["POST"])
def drug_create(request):
    serializer = DrugsSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)


# --------------------------------------------------
# SAFETY SIGNAL SEARCH + FILTER + PAGINATION
# GET /api/signals/
# --------------------------------------------------

@extend_schema(
    summary="List and filter safety signals",
    description=(
        "Search FAERS drug-reaction records. Supports drug-name filtering, "
        "signal filtering, and pagination. Statistical signals do not "
        "establish that a drug caused an adverse event."
    ),
    tags=["signals"],
    parameters=[
        OpenApiParameter(
            name="drug",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Optional partial drug-name search.",
        ),
        OpenApiParameter(
            name="signal_only",
            type=bool,
            location=OpenApiParameter.QUERY,
            required=False,
            description="true for flagged signals, false for other records.",
        ),
        OpenApiParameter(
            name="page",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Page number; defaults to 1.",
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Records per page; defaults to 50, maximum 100.",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Paginated safety-signal records."),
        400: OpenApiResponse(description="Invalid query parameters."),
    },
)
@api_view(["GET"])
def safety_signals(request):
    queryset = SafetySignal.objects.all().order_by("id")

    drug = request.query_params.get("drug", "").strip()
    if drug:
        queryset = queryset.filter(drugname_clean__icontains=drug)

    signal_only = request.query_params.get(
        "signal_only", ""
    ).strip().lower()

    if signal_only not in ("", "true", "false"):
        return Response(
            {"error": "signal_only must be true or false."},
            status=400,
        )

    if signal_only == "true":
        queryset = queryset.filter(is_safety_signal=True)
    elif signal_only == "false":
        queryset = queryset.filter(is_safety_signal=False)

    try:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))

        if page < 1 or page_size < 1:
            raise ValueError

    except (ValueError, TypeError):
        return Response(
            {"error": "page and page_size must be positive integers."},
            status=400,
        )

    page_size = min(page_size, 100)
    total = queryset.count()
    start = (page - 1) * page_size

    records = list(
        queryset.values(
            "drugname_clean",
            "side_effect",
            "a",
            "ROR",
            "ROR_CI_Lower",
            "ROR_CI_Upper",
            "is_safety_signal",
        )[start:start + page_size]
    )

    return Response({
        "total_records": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "signals": records,
    })


# --------------------------------------------------
# SAFETY SIGNAL SUMMARY
# GET /api/signals/summary/
# --------------------------------------------------

@extend_schema(
    summary="Safety signal summary",
    description=(
        "Returns record counts for the imported FAERS dataset. "
        "These are preliminary statistical signals, not confirmed "
        "causal relationships."
    ),
    tags=["signals"],
    responses={
        200: OpenApiResponse(description="Dataset summary and record counts."),
    },
)
@api_view(["GET"])
def safety_signal_summary(request):
    total_records = SafetySignal.objects.count()

    identified_signals = SafetySignal.objects.filter(
        is_safety_signal=True
    ).count()

    other_records = total_records - identified_signals

    return Response({
        "project": "PharmaGuard AI",
        "total_records": total_records,
        "identified_safety_signals": identified_signals,
        "other_records": other_records,
        "note": (
            "These are preliminary statistical signals from FAERS data, "
            "not confirmed drug side effects."
        ),
    })


# --------------------------------------------------
# DRUG SAFETY DETAILS
# GET /api/drug-safety/?drug=DEXYCU
# --------------------------------------------------

@extend_schema(
    summary="Search drug safety signals",
    description=(
        "Search imported FAERS drug-reaction records by partial drug name. "
        "Supports signal filtering and pagination. Results are statistical "
        "associations and do not prove causality."
    ),
    tags=["drug-safety"],
    parameters=[
        OpenApiParameter(
            name="drug",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Drug name or partial name, e.g. DEXYCU.",
        ),
        OpenApiParameter(
            name="signal_only",
            type=bool,
            location=OpenApiParameter.QUERY,
            required=False,
            description="true for records flagged as safety signals; defaults to false.",
        ),
        OpenApiParameter(
            name="page",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Page number; defaults to 1.",
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Records per page; defaults to 10, maximum 100.",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Drug safety results."),
        400: OpenApiResponse(description="Drug name or query parameter is invalid."),
    },
)
@api_view(["GET"])
def drug_safety_details(request):
    drug_name = request.query_params.get("drug", "").strip()

    if not drug_name:
        return Response(
            {"error": "Please provide a drug name using ?drug=..."},
            status=400,
        )

    queryset = SafetySignal.objects.filter(
        drugname_clean__icontains=drug_name
    ).order_by("id")

    signal_only = request.query_params.get(
        "signal_only", "false"
    ).strip().lower()

    if signal_only not in ("true", "false"):
        return Response(
            {"error": "signal_only must be true or false."},
            status=400,
        )

    if signal_only == "true":
        queryset = queryset.filter(is_safety_signal=True)

    try:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        if page < 1 or page_size < 1:
            raise ValueError

    except (ValueError, TypeError):
        return Response(
            {"error": "page and page_size must be positive integers."},
            status=400,
        )

    page_size = min(page_size, 100)
    total = queryset.count()
    start = (page - 1) * page_size

    records = list(
        queryset.values(
            "drugname_clean",
            "side_effect",
            "a",
            "ROR",
            "ROR_CI_Lower",
            "ROR_CI_Upper",
            "is_safety_signal",
        )[start:start + page_size]
    )

    return Response({
        "drug_searched": drug_name,
        "total_matches": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "signals": records,
    })
def dashboard(request):
    return render(request, "dashboard.html")

import csv
from pathlib import Path
from django.core.paginator import Paginator
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from PharmaGuard_AI.models import (
    FaersSignalV7,
    FaersDrugSummary,
    FaersReactionSummary,
)



@api_view(["GET"])
def safety_signals_v7(request):
    queryset = FaersSignalV7.objects.all().order_by("id")

    # Read query parameters
    drug = request.query_params.get("drug", "").strip()
    reaction = request.query_params.get("reaction", "").strip()
    signal_only = request.query_params.get(
        "signal_only", ""
    ).strip().lower()

    drug_match = request.query_params.get(
        "drug_match", "contains"
    ).strip().lower()

    # Filter by drug name
    if drug:
        if drug_match == "prefix":
            queryset = queryset.filter(
                drug_key__istartswith=drug
            )
        elif drug_match == "exact":
            queryset = queryset.filter(
                drug_key__iexact=drug
            )
        else:
            queryset = queryset.filter(
                drug_key__icontains=drug
            )

    # Filter by reaction name
    if reaction:
        queryset = queryset.filter(
            reaction_key__icontains=reaction
        )

    # Filter by potential signal
    if signal_only in {"true", "1", "yes"}:
        queryset = queryset.filter(potential_signal=True)
    elif signal_only in {"false", "0", "no"}:
        queryset = queryset.filter(potential_signal=False)

    # Pagination
    page_number = request.query_params.get("page", "1")

    try:
        page_size = int(
            request.query_params.get("page_size", "20")
        )
    except (TypeError, ValueError):
        page_size = 20

    page_size = max(1, min(page_size, 100))

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)

    # Prepare response data
    signals = [
        {
            "drug_key": row.drug_key,
            "reaction_key": row.reaction_key,
            "a": row.a,
            "drug_reports": row.drug_reports,
            "reaction_reports": row.reaction_reports,
            "b": row.b,
            "c": row.c,
            "d": row.d,
            "ROR": row.ROR,
            "log_ROR": row.log_ROR,
            "SE_log_ROR": row.SE_log_ROR,
            "ROR_CI_lower": row.ROR_CI_lower,
            "ROR_CI_upper": row.ROR_CI_upper,
            "potential_signal": row.potential_signal,
        }
        for row in page_obj.object_list
    ]

    # Return API response
    return Response({
        "dataset": "FAERS V7",
        "total_records": paginator.count,
        "page": page_obj.number,
        "page_size": page_size,
        "total_pages": paginator.num_pages,
        "signals": signals,
        "disclaimer": (
            "These are exploratory statistical signals, "
            "not proof of causation or incidence."
        ),
    })

# ==================================================
# PHARMAGUARD AI - FULL DATASET ANALYTICS
# ==================================================


from django.db.models import Sum
from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def analytics_overview(request):

    drug_stats = FaersDrugSummary.objects.aggregate(
        total_pairs=Sum("total_pairs"),
        potential_signals=Sum("potential_signals"),
    )

    reaction_stats = FaersReactionSummary.objects.aggregate(
        total_pairs=Sum("total_pairs"),
        potential_signals=Sum("potential_signals"),
    )

    total_pairs = drug_stats["total_pairs"] or 0
    potential_signals = drug_stats["potential_signals"] or 0
    non_signals = total_pairs - potential_signals

    total_drugs = FaersDrugSummary.objects.count()
    total_reactions = FaersReactionSummary.objects.count()

    signal_rate = (
        round((potential_signals / total_pairs) * 100, 2)
        if total_pairs else 0
    )

    return Response({
        "dataset": "FAERS V7",
        "total_drug_reaction_pairs": total_pairs,
        "potential_signals": potential_signals,
        "non_signals": non_signals,
        "unique_drugs": total_drugs,
        "unique_reactions": total_reactions,
        "signal_rate_percent": signal_rate,
        "disclaimer": (
            "Potential statistical signals are exploratory "
            "associations and do not establish causality."
        )
    })


@api_view(["GET"])
def analytics_drugs(request):

    results = FaersDrugSummary.objects.all()

    drug_name = request.query_params.get("drug", "").strip().upper()

    if drug_name:
        results = results.filter(drug_key=drug_name)

    results = results.values(
        "drug_key",
        "total_pairs",
        "potential_signals"
    ).order_by(
        "-potential_signals",
        "drug_key"
    )

    paginator = Paginator(results, 50)
    page_obj = paginator.get_page(
        request.query_params.get("page", 1)
    )

    return Response({
        "total_drugs": paginator.count,
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
        "results": list(page_obj.object_list)
    })


@api_view(["GET"])
def analytics_reactions(request):

    results = FaersReactionSummary.objects.values(
        "reaction_key",
        "total_pairs",
        "potential_signals"
    ).order_by(
        "-potential_signals",
        "reaction_key"
    )

    paginator = Paginator(results, 50)
    page_obj = paginator.get_page(
        request.query_params.get("page", 1)
    )

    return Response({
        "total_reactions": paginator.count,
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
        "results": list(page_obj.object_list)
    })

@api_view(["GET"])
def drug_top_reactions(request):

    drug_name = request.query_params.get(
        "drug", ""
    ).strip().upper()

    if not drug_name:
        return Response(
            {"error": "Please provide a drug name."},
            status=400,
        )

    results = (
        FaersSignalV7.objects
        .filter(drug_key=drug_name)
        .values(
            "reaction_key",
            "a",
            "drug_reports",
            "reaction_reports",
            "ROR",
            "ROR_CI_lower",
            "ROR_CI_upper",
            "potential_signal",
        )
        .order_by("-a", "reaction_key")[:10]
    )

    return Response({
        "drug": drug_name,
        "ranking_method": "Co-reported case count (a), descending",
        "total_results": len(results),
        "results": list(results),
    })



@api_view(["GET"])
def drug_directory(request):
    try:
        # Get all unique drugs from the summary table
        drugs = FaersDrugSummary.objects.values_list(
            "drug_key", flat=True
        ).order_by("drug_key")

        # Read letter filter
        letter = request.query_params.get("letter", "").strip()

        if letter:
            if len(letter) != 1 or not letter.isalpha():
                return Response(
                    {"error": "letter must be a single alphabet character."},
                    status=400
                )

            drugs = drugs.filter(
                drug_key__istartswith=letter
            )

        # Pagination
        paginator = Paginator(drugs, 100)

        page_obj = paginator.get_page(
            request.query_params.get("page", 1)
        )

        # Prepare response
        result = {
            "total_drugs": paginator.count,
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "drugs": list(page_obj.object_list)
        }

        # Debug information
        print("LETTER RECEIVED:", repr(letter))
        print("TOTAL SUMMARY ROWS:", FaersDrugSummary.objects.count())
        print("MATCHING DRUGS:", paginator.count)
        print("FIRST 10:", result["drugs"][:10])

        # IMPORTANT: Return the API response
        return Response(result)

    except Exception as e:
        print("DRUG DIRECTORY ERROR:", str(e))

        return Response(
            {"error": str(e)},
            status=500
        )
