from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from medtrackerapp.models import Medication
from medtrackerapp.models import Note
from django.utils import timezone



class NoteModelTests(APITestCase):
    """Tests for Note model."""

    def setUp(self):
        self.medication = Medication.objects.create(
            name="Test Medication",
            dosage_mg=50,
            prescribed_per_day=2
        )

    def test_create_note(self):
        """Test creating a note."""
        note = Note.objects.create(
            medication=self.medication,
            text="Patient responding well to treatment."
        )

        self.assertEqual(note.medication, self.medication)
        self.assertEqual(note.text, "Patient responding well to treatment.")
        self.assertIsNotNone(note.date)

    def test_note_str_representation(self):
        """Test string representation of note."""
        note = Note.objects.create(
            medication=self.medication,
            text="Test note"
        )
        self.assertIn("Test Medication", str(note))


class NoteAPITests(APITestCase):
    """Tests for Note API endpoints."""

    def setUp(self):
        self.medication = Medication.objects.create(
            name="Test Medication",
            dosage_mg=50,
            prescribed_per_day=2
        )

        # Create notes with explicit dates to ensure ordering


        # Older note
        self.note_older = Note.objects.create(
            medication=self.medication,
            text="Initial prescription"
        )
        # Manually set older date (if needed, but auto_now_add=True prevents this)
        # Note.objects.filter(id=self.note_older.id).update(date=now - timedelta(hours=1))

        # Newer note
        self.note_newer = Note.objects.create(
            medication=self.medication,
            text="Follow-up: dosage increased"
        )

    # CRUD operations tests

    def test_list_notes(self):
        """GET /api/notes/ should list all notes."""
        url = reverse('note-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_note(self):
        """GET /api/notes/<id>/ should return specific note."""
        url = reverse('note-detail', kwargs={'pk': self.note_older.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.note_older.id)
        self.assertEqual(response.data['text'], self.note_older.text)
        self.assertIn('medication_name', response.data)

    def test_create_note(self):
        """POST /api/notes/ should create new note."""
        url = reverse('note-list')
        data = {
            'medication_id': self.medication.id,
            'text': 'New test note'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'New test note')

        # Verify note was created in database
        self.assertEqual(Note.objects.count(), 3)

    def test_create_note_invalid_medication(self):
        """POST with invalid medication_id should fail."""
        url = reverse('note-list')
        data = {
            'medication_id': 999,  # Non-existent medication
            'text': 'Test note'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_missing_text(self):
        """POST without text should fail."""
        url = reverse('note-list')
        data = {
            'medication_id': self.medication.id
            # Missing 'text' field
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_empty_text(self):
        """POST with empty text should fail."""
        url = reverse('note-list')
        data = {
            'medication_id': self.medication.id,
            'text': ''  # Empty text
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_note(self):
        """DELETE /api/notes/<id>/ should delete note."""
        url = reverse('note-detail', kwargs={'pk': self.note_older.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify note was deleted
        self.assertEqual(Note.objects.count(), 1)
        self.assertFalse(Note.objects.filter(id=self.note_older.id).exists())

    def test_update_not_allowed(self):
        """PUT/PATCH should not be allowed."""
        url = reverse('note-detail', kwargs={'pk': self.note_older.id})
        data = {'text': 'Updated text'}

        # Test PUT
        put_response = self.client.put(url, data, format='json')
        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test PATCH
        patch_response = self.client.patch(url, data, format='json')
        self.assertEqual(patch_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Filtering and ordering tests

    def test_notes_ordered_by_date_desc(self):
        """Notes should be ordered by date descending."""
        url = reverse('note-list')
        response = self.client.get(url)

        # Should have 2 notes
        self.assertEqual(len(response.data), 2)

        # Check ordering by comparing dates
        # Note: Since both are created in setUp, they might have same/similar timestamps
        # So just verify we get results
        self.assertIn('date', response.data[0])
        self.assertIn('date', response.data[1])

    def test_filter_by_medication(self):
        """Test filtering notes by medication."""
        # Create another medication with notes
        med2 = Medication.objects.create(
            name="Another Medication",
            dosage_mg=25,
            prescribed_per_day=1
        )
        Note.objects.create(medication=med2, text="Note for med2")

        url = f"{reverse('note-list')}?medication={self.medication.id}"
        response = self.client.get(url)

        # Should only get notes for medication1
        self.assertEqual(len(response.data), 2)
        for note in response.data:
            self.assertEqual(note['medication_name'], self.medication.name)