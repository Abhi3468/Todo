from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from httpcore import request
from .models import Task
from .forms import CustomUserCreationForm
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import TaskSerializer
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            # SEND ACKNOWLEDGEMENT EMAIL
            send_mail(
                subject="Welcome to ToDo App 🎉",
                message=f"""
Hi {user.username},

Your ToDo account has been successfully created.

You can now login and manage your tasks.

Thanks,
ToDo App Team
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, "Account created successfully! Email sent.")

            login(request, user)
            return redirect("/")

    else:
        form = CustomUserCreationForm()

    return render(request, "registration/signup.html", {"form": form})

@login_required
def task_list(request):
    if request.method == "POST":
        title = request.POST.get('title')

        if title:
            Task.objects.create(
                title=title,
                user=request.user,
                username=request.user.username  
            )

            messages.success(request, "Task added successfully!")
        return redirect('/')

    tasks = Task.objects.filter(user=request.user).order_by('completed', '-id')
    return render(request, 'tasks/index.html', {'tasks': tasks})

@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()
    return redirect('/')

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('/')

# --- REST API VIEWS ---

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_task_list(request):
    if request.method == 'GET':
        tasks = Task.objects.filter(user=request.user).order_by('completed', '-id')
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, username=request.user.username)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()
    serializer = TaskSerializer(task)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return Response({'status': 'deleted'}, status=204)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_download_pdf(request):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, height - 50, f"To-Do List for {request.user.username}")
    
    # Task List
    p.setFont("Helvetica", 14)
    tasks = Task.objects.filter(user=request.user).order_by('completed', '-id')
    
    y = height - 100
    for task in tasks:
        status = "[x]" if task.completed else "[ ]"
        p.drawString(50, y, f"{status} {task.title}")
        y -= 25
        
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 14)
            y = height - 50
            
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{request.user.username}_todo_list.pdf")
