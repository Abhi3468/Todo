from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

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

class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField() # Used for signup before user is created
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # Valid for 5 minutes
        return not self.is_used and (timezone.now() < self.created_at + timedelta(minutes=5))
    