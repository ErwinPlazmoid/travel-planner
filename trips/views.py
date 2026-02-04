from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import TravelProject
from .serializers import TravelProjectSerializer


class TravelProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing travel projects.

    Supports:
    - Create project (optionally with places via places_input).
    - List projects with optional filtering.
    - Retrieve a single project.
    - Update project fields (name, description, start_date).
    - Delete project when none of its places are marked as visited.
    """

    queryset = TravelProject.objects.all().prefetch_related("places")
    serializer_class = TravelProjectSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        is_completed = params.get("is_completed")
        if is_completed is not None:
            is_completed_normalized = is_completed.lower()
            if is_completed_normalized in {"true", "1"}:
                qs = qs.filter(is_completed=True)
            elif is_completed_normalized in {"false", "0"}:
                qs = qs.filter(is_completed=False)

        name = params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)

        return qs

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.places.filter(visited=True).exists():
            raise ValidationError(
                "Cannot delete project because it has places marked as visited."
            )
        return super().destroy(request, *args, **kwargs)
