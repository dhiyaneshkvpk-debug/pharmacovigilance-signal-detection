from django.contrib import admin

from .models import Signal


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ("drug", "reaction", "a", "ROR", "ROR_CI_Lower", "strength")
    list_filter = ("strength",)
    search_fields = ("drug", "reaction")
