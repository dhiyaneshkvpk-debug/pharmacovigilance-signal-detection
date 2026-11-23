from rest_framework import serializers

from .models import Signal


class SignalSerializer(serializers.ModelSerializer):
    """Turns a Signal database row into JSON."""

    class Meta:
        model = Signal
        fields = ["drug", "reaction", "a", "ROR", "ROR_CI_Lower", "ROR_CI_Upper", "PRR", "p_value", "strength"]
