from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'completed', 'priority', 'due_date', 'created_at']
        read_only_fields = ['created_at']

    def validate_title(self, value):
        """Keep task names useful and consistent for both the UI and API."""
        title = value.strip()
        if not title:
            raise serializers.ValidationError("A task title cannot be empty.")
        return title
