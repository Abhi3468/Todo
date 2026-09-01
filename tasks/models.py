from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    username = models.CharField(max_length=150, default="temp_user")
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    # Nullable only to preserve rows that existed before this field was added.
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['completed', 'due_date', '-created_at']

    def __str__(self):
        return self.title

class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField() # Used for signup before user is created
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # Valid for 5 minutes
        return not self.is_used and (timezone.now() < self.created_at + timedelta(minutes=5))

class AuditLog(models.Model):
    """
    Immutable audit log storing system events, authentication attempts, and task mutations.
    Modifications or deletions of existing records are strictly forbidden at the model level.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {username} - {self.action}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("AuditLog records are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog records are immutable and cannot be deleted.")

    @classmethod
    def log_action(cls, user=None, action="", ip_address=None, details=""):
        return cls.objects.create(
            user=user if (user and hasattr(user, 'is_authenticated') and user.is_authenticated) else None,
            action=action,
            ip_address=ip_address,
            details=details
        )
