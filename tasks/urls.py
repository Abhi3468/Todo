from django.urls import path
from .views import task_list, delete_task, toggle_task, signup_view
from .views import api_task_list, api_toggle_task, api_delete_task, api_download_pdf

urlpatterns = [
    path('', task_list, name='task_list'),
    path('delete/<int:task_id>/', delete_task, name='delete_task'),
    path('toggle/<int:task_id>/', toggle_task, name='toggle_task'),
    path('signup/', signup_view, name='signup'),
    
    # REST API endpoints
    path('api/tasks/', api_task_list, name='api_task_list'),
    path('api/tasks/<int:task_id>/toggle/', api_toggle_task, name='api_toggle_task'),
    path('api/tasks/<int:task_id>/delete/', api_delete_task, name='api_delete_task'),
    path('api/tasks/pdf/', api_download_pdf, name='api_download_pdf'),
]