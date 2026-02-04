from django.db import models


class TravelProject(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def recalculate_completion(self) -> None:
        """
        Mark project as completed when it has at least one place
        and all related places are visited. Otherwise mark it as not completed.
        """
        places = self.places.all()
        if not places.exists():
            completed = False
        else:
            completed = all(place.visited for place in places)

        if self.is_completed != completed:
            self.is_completed = completed
            self.save(update_fields=["is_completed"])


class ProjectPlace(models.Model):
    project = models.ForeignKey(
        TravelProject,
        on_delete=models.CASCADE,
        related_name="places",
    )
    external_id = models.IntegerField()
    title = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    visited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "external_id"],
                name="unique_place_per_project",
            )
        ]

    def __str__(self) -> str:
        return f"{self.project.name} - {self.external_id}"
