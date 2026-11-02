from django.test import TestCase

# Create your tests here.

from rest_framework.test import APITestCase
from rest_framework import status


class PharmaGuardAPITests(APITestCase):

    def test_home_api(self):
        response = self.client.get("/api/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["status"],
            "success"
        )

    def test_drug_list_api(self):
        response = self.client.get("/api/drugs/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIsInstance(response.data, list)
    
    def test_create_drug_api(self):
        payload = {
            "name": "TestDrug",
            "description": "Test drug for API validation"
        }

        response = self.client.post(
            "/api/drugs/create/",
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["name"],
            "TestDrug"
        )


    def test_duplicate_drug_rejected(self):
        payload = {
            "name": "DuplicateDrug",
            "description": "First record"
        }

        first_response = self.client.post(
            "/api/drugs/create/",
            payload,
            format="json"
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED
        )

        second_response = self.client.post(
            "/api/drugs/create/",
            payload,
            format="json"
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )


    def test_safety_signals_api(self):
        response = self.client.get(
            "/api/signals/?page=1&page_size=5"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("total_records", response.data)
        self.assertIn("signals", response.data)
        self.assertEqual(response.data["page_size"], 5)
        self.assertLessEqual(len(response.data["signals"]), 5)

    def test_safety_signal_filter(self):
        response = self.client.get(
            "/api/signals/?signal_only=true&page=1&page_size=5"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("signals", response.data)

        for record in response.data["signals"]:
            self.assertIn(
                str(record["is_safety_signal"]).strip().lower(),
                ["true", "1"]
            )
