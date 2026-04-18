from django.contrib import admin
from django.contrib.auth.models import User
from .models import Task


# 🔹 Task Inline under User
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0


# 🔹 Custom User Admin
class CustomUserAdmin(admin.ModelAdmin):
    inlines = [TaskInline]


# Unregister default user
admin.site.unregister(User)

# Register with custom view
admin.site.register(User, CustomUserAdmin)


# 🔹 Task Admin (normal)
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'username', 'completed')
    list_filter = ('user', 'completed')
    search_fields = ('title', 'username', 'user__username')