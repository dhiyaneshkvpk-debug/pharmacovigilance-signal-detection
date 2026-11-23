from django.db import models


class Signal(models.Model):
    """One row = one (drug, reaction) pair with its statistics. Same columns as outputs/signals.csv."""
    drug = models.CharField(max_length=255, db_index=True)
    reaction = models.CharField(max_length=255, db_index=True)
    a = models.IntegerField(help_text="number of cases with this drug AND this reaction")
    drug_total = models.IntegerField(help_text="number of cases with this drug")
    reaction_total = models.IntegerField(help_text="number of cases with this reaction")
    ROR = models.FloatField()
    ROR_CI_Lower = models.FloatField()
    ROR_CI_Upper = models.FloatField()
    PRR = models.FloatField()
    p_value = models.FloatField()
    is_signal = models.BooleanField()
    strength = models.CharField(max_length=20, db_index=True)   # Strong / Moderate / Weak / Excluded / No signal

    class Meta:
        ordering = ["-ROR_CI_Lower"]      # most reliable signals first

    def __str__(self):
        return f"{self.drug} -> {self.reaction}"
