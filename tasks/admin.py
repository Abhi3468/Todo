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


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'username', 'completed')
    list_filter = ('user', 'completed')
    search_fields = ('title', 'username', 'user__username')


from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'action', 'ip_address', 'details')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'details', 'ip_address')
    readonly_fields = ('user', 'action', 'ip_address', 'details', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False