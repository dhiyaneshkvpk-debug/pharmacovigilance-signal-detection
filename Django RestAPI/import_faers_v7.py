
import csv
import os
import django
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from PharmaGuard_AI.models import FaersSignalV7

CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "pipeline_v2"
    / "output"
    / "faers_ror_signals_v7.csv"
)

BATCH_SIZE = 5000
FaersSignalV7.objects.all().delete()

if not CSV_PATH.exists():
    raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

required_columns = [
    "drug_key", "reaction_key", "a", "drug_reports",
    "reaction_reports", "b", "c", "d", "ROR",
    "log_ROR", "SE_log_ROR", "ROR_CI_lower",
    "ROR_CI_upper", "potential_signal",
]

batch = []
total = 0

print(f"Importing from: {CSV_PATH}")

with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    missing = set(required_columns) - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")

    for row in reader:
        signal_text = row["potential_signal"].strip().lower()
        is_signal = signal_text in {"true", "1", "yes"}

        batch.append(
            FaersSignalV7(
                drug_key=row["drug_key"],
                reaction_key=row["reaction_key"],
                a=int(row["a"]),
                drug_reports=int(row["drug_reports"]),
                reaction_reports=int(row["reaction_reports"]),
                b=int(row["b"]),
                c=int(row["c"]),
                d=int(row["d"]),
                ROR=float(row["ROR"]),
                log_ROR=float(row["log_ROR"]),
                SE_log_ROR=float(row["SE_log_ROR"]),
                ROR_CI_lower=float(row["ROR_CI_lower"]),
                ROR_CI_upper=float(row["ROR_CI_upper"]),
                potential_signal=is_signal,
            )
        )

        if len(batch) >= BATCH_SIZE:
            FaersSignalV7.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            total += len(batch)
            batch.clear()
            print(f"Imported {total:,} rows")

    if batch:
        FaersSignalV7.objects.bulk_create(batch, batch_size=BATCH_SIZE)
        total += len(batch)

print(f"Import complete! Total rows imported: {total:,}")
