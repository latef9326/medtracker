from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from medtrackerapp.models import Medication
from unittest.mock import patch


class ExpectedDosesEndpointTests(APITestCase):

    def setUp(self):
        # Tworzymy przykładową lek
        self.med = Medication.objects.create(
            name="TestMed",
            prescribed_per_day=2,  # ilość dawek na dzień
            dosage_mg=50  # ilość mg na dawkę
        )
        self.url = lambda days=None: reverse(
            'medication-expected-doses', kwargs={'pk': self.med.id}
        ) + (f'?days={days}' if days is not None else '')

    def test_valid_days_returns_200_and_expected_structure(self):
        """Poprawny request powinien zwrócić HTTP 200 i dane"""
        response = self.client.get(self.url(days=3))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('medication_id', response.data)
        self.assertIn('days', response.data)
        self.assertIn('expected_doses', response.data)
        # Dodatkowa weryfikacja wartości
        self.assertEqual(response.data['expected_doses'], 6)  # 3 dni × 2 dawki/dzień

    def test_missing_days_parameter_returns_400(self):
        """Brak parametru days → HTTP 400"""
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_negative_days_returns_400(self):
        """Ujemna wartość days → HTTP 400"""
        response = self.client.get(self.url(days=-5))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_zero_days_returns_400(self):
        """0 jako days → HTTP 400"""
        response = self.client.get(self.url(days=0))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_valueerror_from_expected_doses_returns_400(self):
        """Jeśli expected_doses rzuci ValueError → HTTP 400"""

        # Opcja 1: Użyj mock aby podmienić metodę expected_doses
        with patch.object(Medication, 'expected_doses') as mock_method:
            mock_method.side_effect = ValueError("Invalid value from model")

            response = self.client.get(self.url(days=3))
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)

    def test_invalid_days_format_returns_400(self):
        """Niepoprawny format days (nie liczba) → HTTP 400"""
        url = reverse('medication-expected-doses', kwargs={'pk': self.med.id})
        response = self.client.get(f"{url}?days=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_medication_not_found_returns_404(self):
        """Nieistniejący lek → HTTP 404"""
        url = reverse('medication-expected-doses', kwargs={'pk': 999})
        response = self.client.get(f"{url}?days=3")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)