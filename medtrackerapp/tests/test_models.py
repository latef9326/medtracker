from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta

from medtrackerapp.models import Medication, DoseLog


class TestMedicationModel(TestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )

    # --- BASIC TESTS ---

    def test_str_representation(self):
        self.assertEqual(str(self.med), "Aspirin (100mg)")

    def test_adherence_no_logs(self):
        """If medication has no logs, adherence is 0."""
        self.assertEqual(self.med.adherence_rate(), 0.0)

    def test_adherence_with_logs(self):
        """Adherence is calculated correctly."""
        now = timezone.now()
        DoseLog.objects.create(medication=self.med, taken_at=now, was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=now, was_taken=False)

        # 1/2 taken = 50%
        self.assertEqual(self.med.adherence_rate(), 50.0)

    # --- EXPECTED DOSES ---

    def test_expected_doses_positive(self):
        self.assertEqual(self.med.expected_doses(3), 6)

    def test_expected_doses_negative_days(self):
        with self.assertRaises(ValueError):
            self.med.expected_doses(-1)

    def test_expected_doses_invalid_schedule(self):
        med2 = Medication.objects.create(
            name="Bad",
            dosage_mg=10,
            prescribed_per_day=0
        )
        with self.assertRaises(ValueError):
            med2.expected_doses(5)

    # --- ADHERENCE OVER PERIOD ---

    def test_adherence_rate_over_period_valid(self):
        start = date.today()
        end = start + timedelta(days=2)

        # expected doses = (3 days * 2 doses/day) = 6
        # logs: 4 taken, 2 missed
        dt = timezone.now()

        DoseLog.objects.create(medication=self.med, taken_at=dt, was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=dt, was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=dt, was_taken=False)
        DoseLog.objects.create(medication=self.med, taken_at=dt, was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=dt, was_taken=False)
        DoseLog.objects.create(medication=self.med, taken_at=dt, was_taken=True)

        # 4/6 = 66.67%
        self.assertEqual(self.med.adherence_rate_over_period(start, end), 66.67)

    def test_adherence_rate_over_period_invalid_range(self):
        start = date.today()
        end = start - timedelta(days=1)

        with self.assertRaises(ValueError):
            self.med.adherence_rate_over_period(start, end)

    # --- EXTERNAL INFO MOCKED IN VIEW TESTS, NOT HERE ---


class TestDoseLogModel(TestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="Ibuprofen",
            dosage_mg=200,
            prescribed_per_day=3
        )

    def test_str_representation(self):
        dt = timezone.now()
        log = DoseLog.objects.create(medication=self.med, taken_at=dt, was_taken=True)
        rep = str(log)

        self.assertIn("Ibuprofen", rep)
        self.assertIn("Taken", rep)

    def test_doselog_future_date(self):
        """Future timestamps may or may not be allowed depending on business rules,
        but here we at least check the model accepts it."""
        future = timezone.now() + timedelta(days=5)
        log = DoseLog.objects.create(medication=self.med, taken_at=future, was_taken=True)
        self.assertEqual(log.medication, self.med)

    def test_doselog_invalid_medication(self):
        """Missing medication should raise an error."""
        now = timezone.now()
        with self.assertRaises(Exception):
            DoseLog.objects.create(medication=None, taken_at=now, was_taken=True)

    def test_doselog_missing_taken_at(self):
        with self.assertRaises(Exception):
            DoseLog.objects.create(medication=self.med, taken_at=None, was_taken=True)
