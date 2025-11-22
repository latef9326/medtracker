from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta

from medtrackerapp.models import Medication, DoseLog


class MedicationViewSetTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )
        self.list_url = reverse("medication-list")   # /api/medications/
        self.detail_url = reverse("medication-detail", kwargs={"pk": self.med.id})
        self.info_url = reverse("medication-get-external-info", kwargs={"pk": self.med.id})

    # --- LIST & CREATE ---

    def test_get_medications_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_medication_valid(self):
        data = {
            "name": "Ibuprofen",
            "dosage_mg": 200,
            "prescribed_per_day": 3
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Ibuprofen")

    def test_create_medication_invalid(self):
        data = {
            "name": "",
            "dosage_mg": -10,
            "prescribed_per_day": 0
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- RETRIEVE / UPDATE / DELETE ---

    def test_get_medication_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Aspirin")

    def test_get_medication_detail_not_found(self):
        url = reverse("medication-detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_medication_valid(self):
        data = {"name": "NewName", "dosage_mg": 150, "prescribed_per_day": 1}
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "NewName")

    def test_update_medication_invalid(self):
        data = {"name": "", "dosage_mg": -1, "prescribed_per_day": 0}
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_medication(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_medication_not_found(self):
        url = reverse("medication-detail", kwargs={"pk": 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- EXTERNAL API (MOCK) ---

    @patch("medtrackerapp.services.DrugInfoService.get_drug_info")
    def test_get_external_info_success(self, mock_api):
        mock_api.return_value = {"info": "Mocked info"}

        response = self.client.get(self.info_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["info"], "Mocked info")

    @patch("medtrackerapp.services.DrugInfoService.get_drug_info")
    def test_get_external_info_error(self, mock_api):
        mock_api.return_value = {"error": "API unavailable"}

        response = self.client.get(self.info_url)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("error", response.data)


class DoseLogViewSetTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="Paracetamol",
            dosage_mg=500,
            prescribed_per_day=2
        )
        self.list_url = reverse("doselog-list")
        self.now = timezone.now()

    # --- LIST & CREATE ---

    def test_get_logs_list(self):
        DoseLog.objects.create(medication=self.med, taken_at=self.now, was_taken=True)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_log_valid(self):
        data = {
            "medication": self.med.id,
            "taken_at": self.now.isoformat(),
            "was_taken": True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_log_invalid(self):
        data = {
            "medication": 9999,  # Nieistniejące ID
            "taken_at": "invalid-date-format",  # Nieprawidłowy format daty
            "was_taken": True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- DETAIL ---

    def test_get_log_detail(self):
        log = DoseLog.objects.create(medication=self.med, taken_at=self.now, was_taken=True)
        url = reverse("doselog-detail", kwargs={"pk": log.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_log_detail_not_found(self):
        url = reverse("doselog-detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- UPDATE ---

    def test_update_log_valid(self):
        log = DoseLog.objects.create(medication=self.med, taken_at=self.now, was_taken=True)
        url = reverse("doselog-detail", kwargs={"pk": log.id})
        data = {
            "medication": self.med.id,
            "taken_at": (self.now - timedelta(hours=1)).isoformat(),
            "was_taken": False
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["was_taken"], False)

    def test_update_log_invalid(self):
        log = DoseLog.objects.create(medication=self.med, taken_at=self.now, was_taken=True)
        url = reverse("doselog-detail", kwargs={"pk": log.id})
        data = {
            "medication": 9999,  # Nieistniejące ID
            "taken_at": "invalid-date-format",  # Nieprawidłowy format daty
            "was_taken": True
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- DELETE ---

    def test_delete_log_valid(self):
        log = DoseLog.objects.create(medication=self.med, taken_at=self.now, was_taken=True)
        url = reverse("doselog-detail", kwargs={"pk": log.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_log_not_found(self):
        url = reverse("doselog-detail", kwargs={"pk": 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- FILTER BY DATE ---

    def test_filter_logs_valid_range(self):
        log = DoseLog.objects.create(medication=self.med, taken_at=self.now, was_taken=True)

        url = reverse("doselog-filter-by-date")
        url += f"?start={self.now.date()}&end={self.now.date()}"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_filter_logs_missing_params(self):
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url)  # no params
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_logs_invalid_date(self):
        url = reverse("doselog-filter-by-date") + "?start=AAAA&end=BBBB"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)