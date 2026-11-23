"""
Loads outputs/signals.csv (made by step 2) into the database.

Run:  python manage.py load_signals
"""
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from drugsafety.models import Signal


class Command(BaseCommand):
    help = "Load signals.csv into the database (replaces old data)"

    def add_arguments(self, parser):
        parser.add_argument("--csv", help="path to signals.csv (default: ../outputs/signals.csv)")

    def handle(self, *args, **options):
        path = options["csv"] or settings.SIGNALS_CSV
        try:
            table = pd.read_csv(path)
        except FileNotFoundError:
            raise CommandError(f"File not found: {path}. Run step 2 first (python step2_statistical_analysis.py)")

        rows = [
            Signal(drug=r.drug, reaction=r.reaction, a=r.a, drug_total=r.drug_total,
                   reaction_total=r.reaction_total, ROR=r.ROR, ROR_CI_Lower=r.ROR_CI_Lower,
                   ROR_CI_Upper=r.ROR_CI_Upper, PRR=r.PRR, p_value=r.p_value,
                   is_signal=bool(r.is_signal), strength=r.strength)
            for r in table.itertuples(index=False)
        ]

        with transaction.atomic():                  # all-or-nothing, so we never leave half the data
            Signal.objects.all().delete()           # remove the old rows
            Signal.objects.bulk_create(rows, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(rows):,} rows into the database"))
