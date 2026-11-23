"""
The API views. Each function answers one URL and returns JSON.
"""
from django.db.models import Count, Max
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Signal
from .serializers import SignalSerializer

STRENGTHS = ["Strong", "Moderate", "Weak", "Excluded", "No signal"]
NOTE = ("Signals are statistical associations from FAERS reports. "
        "They are hypotheses to investigate, not proof that a drug causes a reaction.")


@api_view(["GET"])
def home(request):
    """GET /api/  - a welcome message listing the endpoints."""
    return Response({
        "project": "PharmaGuard AI",
        "endpoints": ["/api/summary/", "/api/signals/", "/api/drugs/<drug name>/"],
        "note": NOTE,
    })


@api_view(["GET"])
def summary(request):
    """GET /api/summary/  - how many rows, and how many of each strength."""
    counts = Signal.objects.values("strength").annotate(n=Count("id"))
    return Response({
        "total_pairs": Signal.objects.count(),
        "statistical_signals": Signal.objects.filter(is_signal=True).count(),
        "pairs_by_strength": {row["strength"]: row["n"] for row in counts},
        "note": NOTE,
    })


@api_view(["GET"])
def signal_list(request):
    """
    GET /api/signals/   - search the signals.
    Optional filters in the URL:
        ?drug=DUPIXENT   ?reaction=MENINGIOMA   ?strength=Strong   ?min_cases=50
        ?page=2          ?page_size=20 (maximum 100)
    """
    signals = Signal.objects.all()

    # --- filters ---
    drug = request.query_params.get("drug", "").strip()
    if drug:
        signals = signals.filter(drug__icontains=drug)

    reaction = request.query_params.get("reaction", "").strip()
    if reaction:
        signals = signals.filter(reaction__icontains=reaction)

    strength = request.query_params.get("strength", "").strip()
    if strength:
        match = [s for s in STRENGTHS if s.lower() == strength.lower()]
        if not match:
            return Response({"error": f"strength must be one of {STRENGTHS}"}, status=400)
        signals = signals.filter(strength=match[0])

    # --- numbers from the URL must be whole numbers ---
    try:
        min_cases = int(request.query_params.get("min_cases", 0))
        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 20)), 100)
        if page < 1 or page_size < 1:
            raise ValueError
    except ValueError:
        return Response({"error": "min_cases, page and page_size must be positive whole numbers"}, status=400)
    signals = signals.filter(a__gte=min_cases)

    # --- pagination: return only one page of results ---
    total = signals.count()
    start = (page - 1) * page_size
    rows = signals[start:start + page_size]

    return Response({
        "total_results": total,
        "page": page,
        "page_size": page_size,
        "results": SignalSerializer(rows, many=True).data,
    })


@api_view(["GET"])
def drug_profile(request, name):
    """GET /api/drugs/DEPO-PROVERA/  - everything about one drug."""
    signals = Signal.objects.filter(drug__iexact=name)
    if not signals.exists():
        return Response({"error": f"drug '{name}' not found"}, status=404)

    strong = signals.filter(strength="Strong")
    return Response({
        "drug": signals.first().drug,
        "total_cases": signals.aggregate(Max("drug_total"))["drug_total__max"],
        "reactions_analysed": signals.count(),
        "strong_signals": strong.count(),
        "top_strong_signals": SignalSerializer(strong[:10], many=True).data,
        "most_reported_reactions": SignalSerializer(signals.order_by("-a")[:5], many=True).data,
        "note": NOTE,
    })
