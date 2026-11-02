
from django.db import models


class Drugs(models.Model):
    name = models.CharField(max_length=225, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SafetySignal(models.Model):
    drugname_clean = models.CharField(max_length=255, db_index=True)
    side_effect = models.CharField(max_length=255, db_index=True)
    a = models.PositiveIntegerField()
    ROR = models.FloatField()
    ROR_CI_Lower = models.FloatField()
    ROR_CI_Upper = models.FloatField()
    is_safety_signal = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(
                fields=["drugname_clean", "is_safety_signal"],
                name="PharmaGuard_drugnam_6d0ef2_idx",
            ),
        ]

    def __str__(self):
        return f"{self.drugname_clean} - {self.side_effect}"

class FaersSignalV7(models.Model):
    drug_key = models.TextField()
    reaction_key = models.TextField()
    a = models.PositiveIntegerField()
    drug_reports = models.PositiveIntegerField()
    reaction_reports = models.PositiveIntegerField()
    b = models.PositiveIntegerField()
    c = models.PositiveIntegerField()
    d = models.PositiveIntegerField()
    ROR = models.FloatField()
    log_ROR = models.FloatField()
    SE_log_ROR = models.FloatField()
    ROR_CI_lower = models.FloatField()
    ROR_CI_upper = models.FloatField()
    potential_signal = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "faers_signals_v7"

    def __str__(self):
        return f"{self.drug_key} - {self.reaction_key}"


class FaersDrugSummary(models.Model):
    drug_key = models.CharField(max_length=500, unique=True)
    total_pairs = models.PositiveIntegerField(default=0)
    potential_signals = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "faers_drug_summary"
        ordering = ["-potential_signals", "drug_key"]

    def __str__(self):
        return self.drug_key


class FaersReactionSummary(models.Model):
    reaction_key = models.CharField(max_length=97, unique=True)
    total_pairs = models.PositiveIntegerField(default=0)
    potential_signals = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "faers_reaction_summary"
        ordering = ["-potential_signals", "reaction_key"]

    def __str__(self):
        return self.reaction_key

