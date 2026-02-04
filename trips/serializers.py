from __future__ import annotations

from typing import Any, Dict, List

from rest_framework import serializers

from .models import ProjectPlace, TravelProject
from .services.artic_api import ArticAPIError, PlaceNotFoundError, validate_place_exists


class ProjectPlaceReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPlace
        fields = [
            "id",
            "external_id",
            "title",
            "notes",
            "visited",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ProjectPlaceInputSerializer(serializers.Serializer):
    external_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)


class ProjectPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPlace
        fields = [
            "id",
            "project",
            "external_id",
            "title",
            "notes",
            "visited",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "project", "external_id", "title", "created_at", "updated_at"]

    def create(self, validated_data: Dict[str, Any]) -> ProjectPlace:
        project: TravelProject = self.context["project"]

        if project.places.count() >= 10:
            raise serializers.ValidationError(
                "A project cannot have more than 10 places (maximum is 10)."
            )

        external_id = validated_data["external_id"]

        if ProjectPlace.objects.filter(project=project, external_id=external_id).exists():
            raise serializers.ValidationError(
                "This external place is already added to this project."
            )

        notes = validated_data.get("notes", "")

        try:
            artwork = validate_place_exists(external_id)
        except PlaceNotFoundError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        except ArticAPIError as exc:
            raise serializers.ValidationError(
                f"Error validating place with Art Institute API: {exc}"
            ) from exc

        title = artwork.get("title") or ""

        place = ProjectPlace.objects.create(
            project=project,
            external_id=external_id,
            title=title,
            notes=notes,
        )

        project.recalculate_completion()
        return place

    def update(self, instance: ProjectPlace, validated_data: Dict[str, Any]) -> ProjectPlace:
        # Only allow updating notes and visited
        if "notes" in validated_data:
            instance.notes = validated_data["notes"]
        if "visited" in validated_data:
            instance.visited = validated_data["visited"]
        instance.save()
        instance.project.recalculate_completion()
        return instance


class TravelProjectSerializer(serializers.ModelSerializer):
    places = ProjectPlaceReadSerializer(many=True, read_only=True)
    places_input = ProjectPlaceInputSerializer(
        many=True, write_only=True, required=False
    )

    class Meta:
        model = TravelProject
        fields = [
            "id",
            "name",
            "description",
            "start_date",
            "is_completed",
            "created_at",
            "updated_at",
            "places",
            "places_input",
        ]
        read_only_fields = [
            "id",
            "is_completed",
            "created_at",
            "updated_at",
            "places",
        ]

    def validate_places_input(self, value: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(value) > 10:
            raise serializers.ValidationError(
                "A project cannot have more than 10 places (maximum is 10)."
            )

        seen_ids = set()
        for item in value:
            external_id = item["external_id"]
            if external_id in seen_ids:
                raise serializers.ValidationError(
                    "Duplicate external_id detected in places_input."
                )
            seen_ids.add(external_id)

        return value

    def _create_places(
        self, project: TravelProject, places_input: List[Dict[str, Any]]
    ) -> None:
        places_to_create: list[ProjectPlace] = []

        for place_data in places_input:
            external_id = place_data["external_id"]
            notes = place_data.get("notes", "")

            try:
                artwork = validate_place_exists(external_id)
            except PlaceNotFoundError as exc:
                raise serializers.ValidationError(str(exc)) from exc
            except ArticAPIError as exc:
                raise serializers.ValidationError(
                    f"Error validating place with Art Institute API: {exc}"
                ) from exc

            title = artwork.get("title") or ""
            places_to_create.append(
                ProjectPlace(
                    project=project,
                    external_id=external_id,
                    title=title,
                    notes=notes,
                )
            )

        if places_to_create:
            ProjectPlace.objects.bulk_create(places_to_create)
            project.recalculate_completion()

    def create(self, validated_data: Dict[str, Any]) -> TravelProject:
        places_input = validated_data.pop("places_input", [])
        project = TravelProject.objects.create(**validated_data)
        self._create_places(project, places_input)
        return project

    def update(self, instance: TravelProject, validated_data: Dict[str, Any]) -> TravelProject:
        # Only allow updating basic project fields; completion is derived.
        for field in ["name", "description", "start_date"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
