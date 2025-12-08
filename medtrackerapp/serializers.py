from rest_framework import serializers
from .models import Medication, DoseLog, Note


class MedicationSerializer(serializers.ModelSerializer):
    adherence = serializers.SerializerMethodField()

    class Meta:
        model = Medication
        fields = ["id", "name", "dosage_mg", "prescribed_per_day", "adherence"]

    def get_adherence(self, obj):
        return obj.adherence_rate()


class DoseLogSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(
        source='medication.name',
        read_only=True
    )

    class Meta:
        model = DoseLog
        fields = ["id", "medication", "medication_name", "taken_at", "was_taken"]


class NoteSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(
        source='medication.name',
        read_only=True
    )
    medication_id = serializers.PrimaryKeyRelatedField(
        queryset=Medication.objects.all(),
        source='medication',
        write_only=True
    )

    class Meta:
        model = Note
        fields = ['id', 'medication_id', 'medication_name', 'text', 'date']
        read_only_fields = ['id', 'date']

    def validate_text(self, value):
        """Validate note text."""
        if not value or not value.strip():
            raise serializers.ValidationError("Note text cannot be empty")
        if len(value) > 1000:
            raise serializers.ValidationError("Note text is too long (max 1000 characters)")
        return value.strip()