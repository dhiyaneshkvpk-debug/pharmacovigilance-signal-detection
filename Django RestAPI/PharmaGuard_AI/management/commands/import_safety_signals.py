
import pandas as pd
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from PharmaGuard_AI.models import SafetySignal


class Command(BaseCommand):
    help = "Import FAERS saSUMMARY VIEW EXECUTION: 145.32 ms
[30/Oct/2026 18:15:00] "GET /api/signals/summary/ HTTP/1.1" 200 ...fety signals from CSV into the database"

    def handle(self, *args, **options):
        csv_path = (
            Path(settings.BASE_DIR)
            / "PharmaGuard_AI"
            / "faers_safety_signals.csv"
        )

        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        required_columns = [
            "drugname_clean",
            "side_effect",
            "a",
            "ROR",
            "ROR_CI_Lower",
            "ROR_CI_Upper",
            "is_safety_signal",
        ]

        df = pd.read_csv(csv_path)

        missing = set(required_columns) - set(df.columns)
        if missing:
            raise CommandError(
                f"CSV is missing columns: {sorted(missing)}"
            )

        df = df[required_columns].copy()

        for column in ["a", "ROR", "ROR_CI_Lower", "ROR_CI_Upper"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        df["is_safety_signal"] = (
            df["is_safety_signal"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "true": True,
                "1": True,
                "false": False,
                "0": False,
            })
        )

        df = df.dropna(subset=required_columns)

        df = df[
            (df["a"] >= 0)
            & (df["a"] % 1 == 0)
        ]

        if df.empty:
            raise CommandError("No valid records found in the CSV.")

        records = [
            SafetySignal(
                drugname_clean=str(row.drugname_clean),
                side_effect=str(row.side_effect),
                a=int(row.a),
                ROR=float(row.ROR),
                ROR_CI_Lower=float(row.ROR_CI_Lower),
                ROR_CI_Upper=float(row.ROR_CI_Upper),
                is_safety_signal=bool(row.is_safety_signal),
            )
            for row in df.itertuples(index=False)
        ]

        batch_size = 1000

        # Replace existing imported data in this development database.
        with transaction.atomic():
            SafetySignal.objects.all().delete()

            for start in range(0, len(records), batch_size):
                SafetySignal.objects.bulk_create(
                    records[start:start + batch_size],
                    batch_size=batch_size,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(records)} safety-signal records."
            )
        )
