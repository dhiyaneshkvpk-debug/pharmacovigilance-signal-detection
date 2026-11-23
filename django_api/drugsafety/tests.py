from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APITestCase

from .models import Signal


def add(drug, reaction, a, ror, low, strength):
    Signal.objects.create(drug=drug, reaction=reaction, a=a, drug_total=a * 10, reaction_total=a * 5,
                          ROR=ror, ROR_CI_Lower=low, ROR_CI_Upper=ror * 2, PRR=ror, p_value=0.0,
                          is_signal=strength != "No signal", strength=strength)


class ApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        add("DEPO-PROVERA", "MENINGIOMA", 9660, 107366.0, 89029.0, "Strong")
        add("DUPIXENT", "PRURITUS", 11933, 3.1, 2.9, "Moderate")
        add("DUPIXENT", "HEADACHE", 40, 0.8, 0.6, "No signal")

    def test_summary(self):
        data = self.client.get("/api/summary/").json()
        self.assertEqual(data["total_pairs"], 3)
        self.assertEqual(data["statistical_signals"], 2)
        self.assertEqual(data["pairs_by_strength"]["Strong"], 1)

    def test_filter_by_drug_and_strength(self):
        data = self.client.get("/api/signals/?drug=dupix&strength=moderate").json()
        self.assertEqual(data["total_results"], 1)
        self.assertEqual(data["results"][0]["reaction"], "PRURITUS")

    def test_results_sorted_best_first(self):
        data = self.client.get("/api/signals/").json()
        self.assertEqual(data["results"][0]["drug"], "DEPO-PROVERA")

    def test_pagination(self):
        data = self.client.get("/api/signals/?page_size=2&page=2").json()
        self.assertEqual(len(data["results"]), 1)

    def test_bad_input_gives_400(self):
        self.assertEqual(self.client.get("/api/signals/?strength=huge").status_code, 400)
        self.assertEqual(self.client.get("/api/signals/?page=abc").status_code, 400)

    def test_drug_profile(self):
        data = self.client.get("/api/drugs/depo-provera/").json()
        self.assertEqual(data["strong_signals"], 1)
        self.assertEqual(self.client.get("/api/drugs/UNKNOWN-DRUG/").status_code, 404)


class LoadCommandTests(APITestCase):
    def test_load_signals(self):
        import tempfile, pathlib
        csv = pathlib.Path(tempfile.mkdtemp()) / "signals.csv"
        csv.write_text("drug,reaction,a,b,c,d,drug_total,reaction_total,ROR,ROR_CI_Lower,ROR_CI_Upper,PRR,chi2,"
                       "p_value,is_signal,is_non_drug_term,strength\n"
                       "X,Y,5,5,5,85,10,10,17.0,3.5,82.0,9.0,12.0,0.0005,True,False,Weak\n")
        call_command("load_signals", csv=str(csv))
        self.assertEqual(Signal.objects.count(), 1)

    def test_missing_file(self):
        with self.assertRaises(CommandError):
            call_command("load_signals", csv="/does/not/exist.csv")
