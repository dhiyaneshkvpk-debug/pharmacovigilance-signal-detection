
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from PharmaGuard_AI.models import (
    FaersDrugSummary,
    FaersReactionSummary,
)


class Command(BaseCommand):
    help = "Refresh precomputed FAERS V7 drug and reaction analytics"

    def handle(self, *args, **options):

        self.stdout.write("Starting FAERS V7 analytics refresh...")

        with transaction.atomic():

            with connection.cursor() as cursor:

                self.stdout.write("Building drug summaries...")

                cursor.execute("""
                    CREATE TEMPORARY TABLE tmp_drug_summary AS
                    SELECT
                        drug_key,
                        COUNT(*) AS total_pairs,
                        SUM(
                            CASE WHEN potential_signal = 1
                            THEN 1 ELSE 0 END
                        ) AS potential_signals
                    FROM faers_signals_v7
                    GROUP BY drug_key
                """)

                cursor.execute("""
                    DELETE FROM faers_drug_summary
                """)

                cursor.execute("""
                    INSERT INTO faers_drug_summary
                    (drug_key, total_pairs, potential_signals)
                    SELECT
                        drug_key,
                        total_pairs,
                        potential_signals
                    FROM tmp_drug_summary
                """)

                cursor.execute("DROP TEMPORARY TABLE tmp_drug_summary")

                self.stdout.write("Building reaction summaries...")

                cursor.execute("""
                    CREATE TEMPORARY TABLE tmp_reaction_summary AS
                    SELECT
                        reaction_key,
                        COUNT(*) AS total_pairs,
                        SUM(
                            CASE WHEN potential_signal = 1
                            THEN 1 ELSE 0 END
                        ) AS potential_signals
                    FROM faers_signals_v7
                    GROUP BY reaction_key
                """)

                cursor.execute("""
                    DELETE FROM faers_reaction_summary
                """)

                cursor.execute("""
                    INSERT INTO faers_reaction_summary
                    (reaction_key, total_pairs, potential_signals)
                    SELECT
                        reaction_key,
                        total_pairs,
                        potential_signals
                    FROM tmp_reaction_summary
                """)

                cursor.execute(
                    "DROP TEMPORARY TABLE tmp_reaction_summary"
                )

        drug_count = FaersDrugSummary.objects.count()
        reaction_count = FaersReactionSummary.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Analytics refresh completed!\n"
                f"Unique drugs: {drug_count:,}\n"
                f"Unique reactions: {reaction_count:,}"
            )
        )
