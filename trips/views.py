from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError

from .models import ProjectPlace, TravelProject
from .serializers import ProjectPlaceSerializer, TravelProjectSerializer


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


class ProjectPlaceListCreateView(generics.ListCreateAPIView):
    """
    List all places for a project, or add a new place to the project.
    """

    serializer_class = ProjectPlaceSerializer

    def get_project(self) -> TravelProject:
        return get_object_or_404(TravelProject, pk=self.kwargs["project_id"])

    def get_queryset(self):
        project = self.get_project()
        qs = ProjectPlace.objects.filter(project=project)

        visited = self.request.query_params.get("visited")
        if visited is not None:
            visited_normalized = visited.lower()
            if visited_normalized in {"true", "1"}:
                qs = qs.filter(visited=True)
            elif visited_normalized in {"false", "0"}:
                qs = qs.filter(visited=False)

        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["project"] = self.get_project()
        return context


class ProjectPlaceDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a single place within a project.
    """

    serializer_class = ProjectPlaceSerializer
    lookup_url_kwarg = "place_id"

    def get_project(self) -> TravelProject:
        return get_object_or_404(TravelProject, pk=self.kwargs["project_id"])

    def get_queryset(self):
        project = self.get_project()
        return ProjectPlace.objects.filter(project=project)
