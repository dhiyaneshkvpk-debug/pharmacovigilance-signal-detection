from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("drugsafety.urls")),     # everything under /api/ goes to our app
]
