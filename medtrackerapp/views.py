from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from datetime import date
from .models import Medication, DoseLog, Note
from .serializers import MedicationSerializer, DoseLogSerializer, NoteSerializer


class MedicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing medications.
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    @action(detail=True, methods=["get"], url_path="info")
    def get_external_info(self, request, pk=None):
        """Fetch external drug information for a medication."""
        medication = self.get_object()
        data = medication.fetch_external_info()
        if isinstance(data, dict) and data.get("error"):
            return Response(data, status=status.HTTP_502_BAD_GATEWAY)
        return Response(data)

    @action(detail=True, methods=["get"], url_path="expected-doses")
    def expected_doses(self, request, pk=None):
        """
        Calculate expected doses for given days.

        GET /api/medications/<id>/expected-doses/?days=X
        Returns: {medication_id, days, expected_doses}

        Validates:
        - 'days' parameter is required
        - 'days' must be a positive integer
        """
        medication = self.get_object()
        days_param = request.query_params.get("days")

        # Validate days parameter
        if not days_param:
            return Response(
                {"error": "Missing required parameter: days"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            days = int(days_param)
            if days <= 0:
                return Response(
                    {"error": "days must be a positive integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "days must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate expected doses
        try:
            expected = medication.expected_doses(days)
            return Response({
                "medication_id": medication.id,
                "days": days,
                "expected_doses": expected
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DoseLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing dose logs.
    """
    queryset = DoseLog.objects.all()
    serializer_class = DoseLogSerializer

    @action(detail=False, methods=["get"], url_path="filter")
    def filter_by_date(self, request):
        """Filter dose logs by date range."""
        start_date_str = request.query_params.get("start")
        end_date_str = request.query_params.get("end")

        if not start_date_str or not end_date_str:
            return Response(
                {"error": "Both 'start' and 'end' parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_date > end_date:
            return Response(
                {"error": "start_date must be before or equal to end_date"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logs = self.get_queryset().filter(
            taken_at__date__gte=start_date,
            taken_at__date__lte=end_date
        ).order_by("taken_at")

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class NoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing doctor's notes.

    Notes are associated with medications and can be used to track
    observations, side effects, or treatment adjustments.

    Allowed operations:
    - GET /api/notes/ - list all notes
    - GET /api/notes/<id>/ - retrieve specific note
    - POST /api/notes/ - create new note
    - DELETE /api/notes/<id>/ - delete note

    Update operations (PUT, PATCH) are intentionally disabled.
    """
    queryset = Note.objects.all().select_related('medication')
    serializer_class = NoteSerializer

    # 🔹 Added SearchFilter for searching by medication name
    filter_backends = (SearchFilter,)
    search_fields = ['medication__name']

    def get_queryset(self):
        """Optionally filter notes by medication."""
        queryset = super().get_queryset()
        medication_id = self.request.query_params.get('medication')

        if medication_id:
            try:
                medication_id = int(medication_id)
                queryset = queryset.filter(medication_id=medication_id)
            except ValueError:
                # Invalid medication ID, return empty queryset
                queryset = queryset.none()

        return queryset

    def update(self, request, *args, **kwargs):
        """Disable update operations."""
        return Response(
            {
                "detail": "Method 'PUT' not allowed.",
                "error": "Notes cannot be updated once created."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        """Disable partial update operations."""
        return Response(
            {
                "detail": "Method 'PATCH' not allowed.",
                "error": "Notes cannot be updated once created."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
