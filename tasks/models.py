from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    username = models.CharField(max_length=150, default="temp_user")
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    