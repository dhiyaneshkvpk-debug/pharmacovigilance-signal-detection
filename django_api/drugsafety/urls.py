from django.urls import path

from . import views

urlpatterns = [
    path("", views.home),                              # /api/
    path("summary/", views.summary),                   # /api/summary/
    path("signals/", views.signal_list),               # /api/signals/?drug=...
    path("drugs/<path:name>/", views.drug_profile),    # /api/drugs/DEPO-PROVERA/
]
