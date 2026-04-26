from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from httpcore import request
from .models import Task, OTPCode
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
from django.contrib.auth.models import User
import random

def generate_otp(user=None, email=None):
    code = str(random.randint(100000, 999999))
    
    # If we have a user but no email provided, get it from the user account
    if user and not email:
        email = user.email
        
    OTPCode.objects.filter(user=user, email=email).update(is_used=True) # Invalidate old codes
    OTPCode.objects.create(user=user, email=email, code=code)
    
    subject = "Your ToDo App OTP Code"
    message = f"Your OTP code is: {code}. It is valid for 5 minutes."
    recipient = email if email else user.email
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
    return code

def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Don't save user yet, store data in session
            request.session['signup_data'] = request.POST
            email = form.cleaned_data.get('email')
            generate_otp(email=email)
            messages.info(request, f"An OTP has been sent to {email}. Please verify.")
            return redirect('verify_otp_signup')
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

def verify_otp_signup(request):
    if request.method == "POST":
        otp_code = request.POST.get('otp_code')
        signup_data = request.session.get('signup_data')
        
        if not signup_data:
            return redirect('signup')
            
        email = signup_data.get('email')
        otp_record = OTPCode.objects.filter(email=email, code=otp_code).last()
        
        if otp_record and otp_record.is_valid():
            otp_record.is_used = True
            otp_record.save()
            
            # Create user now
            form = CustomUserCreationForm(signup_data)
            if form.is_valid():
                user = form.save()
                login(request, user)
                del request.session['signup_data']
                messages.success(request, "Account created and verified successfully!")
                return redirect("/")
        else:
            messages.error(request, "Invalid or expired OTP.")
            
    return render(request, "registration/verify_otp.html", {"type": "Signup"})



@api_view(['POST'])
@permission_classes([]) # Publicly accessible for login
def send_otp_api(request):
    username = request.data.get('username')
    try:
        user = User.objects.get(username=username)
        generate_otp(user=user)
        return Response({'status': 'success', 'message': 'OTP sent to your email.'})
    except User.DoesNotExist:
        return Response({'status': 'error', 'message': 'User not found.'}, status=404)

def login_view(request):
    if request.method == "POST":
        method = request.POST.get('login_method')
        
        if method == "password":
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                messages.success(request, f"Welcome back, {request.user.username}!")
                return redirect("/")
        
        elif method == "otp":
            username = request.POST.get('username')
            otp_code = request.POST.get('otp_code')
            try:
                user = User.objects.get(username=username)
                otp_record = OTPCode.objects.filter(user=user, code=otp_code).last()
                
                if otp_record and otp_record.is_valid():
                    otp_record.is_used = True
                    otp_record.save()
                    login(request, user)
                    messages.success(request, f"Logged in via OTP! Welcome, {user.username}!")
                    return redirect("/")
                else:
                    messages.error(request, "Invalid or expired OTP.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                
        form = AuthenticationForm()
    else:
        form = AuthenticationForm()
            
    return render(request, "registration/login.html", {"form": form})

def verify_otp_login(request):
    user_id = request.session.get('pending_login_user_id')
    if not user_id:
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    
    if request.method == "POST":
        otp_code = request.POST.get('otp_code')
        otp_record = OTPCode.objects.filter(user=user, code=otp_code).last()
        
        if otp_record and otp_record.is_valid():
            otp_record.is_used = True
            otp_record.save()
            
            login(request, user)
            del request.session['pending_login_user_id']
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("/")
        else:
            messages.error(request, "Invalid or expired OTP.")
            
    return render(request, "registration/verify_otp.html", {"type": "Login"})

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
