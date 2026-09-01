from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.http import FileResponse, JsonResponse
from django.db import connection
from .models import Task, OTPCode, AuditLog
from .forms import CustomUserCreationForm
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import TaskSerializer
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib.auth.models import User
import secrets

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def health_check(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    status = "healthy" if db_ok else "unhealthy"
    status_code = 200 if db_ok else 503
    return JsonResponse({
        "status": status,
        "database": "connected" if db_ok else "disconnected"
    }, status=status_code)

def generate_otp(user=None, email=None):
    code = str(secrets.randbelow(900000) + 100000)
    email = (email or (user.email if user else "") or "").strip()

    if user:
        OTPCode.objects.filter(user=user).update(is_used=True)
    if email:
        OTPCode.objects.filter(email=email).update(is_used=True)

    OTPCode.objects.create(user=user, email=email, code=code)

    subject = "Your ToDo App OTP Code"
    message = f"Your OTP code is: {code}. It is valid for 5 minutes."
    recipient = email

    print(f"[OTP DEBUG] Generated code '{code}' for recipient '{recipient}'")

    if recipient and getattr(settings, 'EMAIL_HOST_USER', None):
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True)
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
    return code

def signup_view(request):
    if request.method == "POST":
        try:
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                # Don't save user yet, store data in session
                request.session['signup_data'] = {
                    key: form.cleaned_data[key]
                    for key in ('username', 'email', 'password1', 'password2')
                }
                email = form.cleaned_data.get('email')
                code = generate_otp(email=email)
                if not getattr(settings, 'EMAIL_HOST_USER', None):
                    messages.info(request, f"An OTP code has been generated: {code} (SMTP credentials not set in environment).")
                else:
                    messages.info(request, f"An OTP code has been sent to {email}. (Code: {code})")
                return redirect('verify_otp_signup')
        except Exception as e:
            print(f"[SIGNUP ERROR] {e}")
            messages.error(request, f"An unexpected error occurred during signup: {e}")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@require_POST
def resend_signup_otp(request):
    signup_data = request.session.get('signup_data')
    if not signup_data:
        messages.info(request, "Start account creation again to receive a verification code.")
        return redirect('signup')

    code = generate_otp(email=signup_data['email'])
    if not getattr(settings, 'EMAIL_HOST_USER', None):
        messages.success(request, f"A new OTP code has been generated: {code}")
    else:
        messages.success(request, f"A new verification code has been sent. (Code: {code})")
    return redirect('verify_otp_signup')

def verify_otp_signup(request):
    if request.method == "POST":
        try:
            otp_code = (request.POST.get('otp_code') or '').strip()
            signup_data = request.session.get('signup_data')
            
            if not signup_data:
                messages.warning(request, "Session expired. Please fill out the registration form again.")
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
                    if 'signup_data' in request.session:
                        del request.session['signup_data']
                    messages.success(request, "Account created and verified successfully!")
                    return redirect("/")
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
            else:
                messages.error(request, "Invalid or expired OTP.")
        except Exception as e:
            print(f"[VERIFY OTP ERROR] {e}")
            messages.error(request, f"An error occurred during verification: {e}")
            
    return render(request, "registration/verify_otp.html", {"type": "Signup"})

@api_view(['POST'])
@permission_classes([]) # Publicly accessible for login
def send_otp_api(request):
    username = (request.data.get('username') or '').strip()
    try:
        user = User.objects.get(username=username)
        generate_otp(user=user)
        return Response({'status': 'success', 'message': 'If the account exists, a code has been sent.'})
    except User.DoesNotExist:
        return Response({'status': 'success', 'message': 'If the account exists, a code has been sent.'})

def login_view(request):
    if request.method == "POST":
        method = request.POST.get('login_method')
        
        if method == "password":
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                messages.success(request, f"Welcome back, {request.user.username}!")
                return redirect("/")
            messages.error(request, "Enter a valid username and password.")
        
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
                    AuditLog.log_action(
                        user=user,
                        action="USER_LOGIN_OTP",
                        ip_address=get_client_ip(request),
                        details=f"User {user.username} logged in via OTP"
                    )
                    messages.success(request, f"Logged in via OTP! Welcome, {user.username}!")
                    return redirect("/")
                else:
                    messages.error(request, "Invalid or expired OTP.")
            except User.DoesNotExist:
                messages.error(request, "Invalid or expired OTP.")
                
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
        title = request.POST.get('title', '').strip()

        if title:
            task = Task.objects.create(
                title=title,
                user=request.user,
                username=request.user.username  
            )
            AuditLog.log_action(
                user=request.user,
                action="TASK_CREATED",
                ip_address=get_client_ip(request),
                details=f"Created task '{task.title}' (ID: {task.id})"
            )

            messages.success(request, "Task added successfully!")
        return redirect('/')

    tasks = Task.objects.filter(user=request.user)
    return render(request, 'tasks/index.html', {'tasks': tasks})

@login_required
@require_POST
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()
    AuditLog.log_action(
        user=request.user,
        action="TASK_TOGGLED",
        ip_address=get_client_ip(request),
        details=f"Toggled task '{task.title}' (ID: {task.id}) completed={task.completed}"
    )
    return redirect('/')

@login_required
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    title = task.title
    task.delete()
    AuditLog.log_action(
        user=request.user,
        action="TASK_DELETED",
        ip_address=get_client_ip(request),
        details=f"Deleted task '{title}' (ID: {task_id})"
    )
    return redirect('/')

# --- REST API VIEWS ---

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_task_list(request):
    if request.method == 'GET':
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save(user=request.user, username=request.user.username)
            AuditLog.log_action(
                user=request.user,
                action="API_TASK_CREATED",
                ip_address=get_client_ip(request),
                details=f"API Created task '{task.title}' (ID: {task.id})"
            )
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()
    AuditLog.log_action(
        user=request.user,
        action="API_TASK_TOGGLED",
        ip_address=get_client_ip(request),
        details=f"API Toggled task '{task.title}' (ID: {task.id}) completed={task.completed}"
    )
    serializer = TaskSerializer(task)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    title = task.title
    task.delete()
    AuditLog.log_action(
        user=request.user,
        action="API_TASK_DELETED",
        ip_address=get_client_ip(request),
        details=f"API Deleted task '{title}' (ID: {task_id})"
    )
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
    tasks = Task.objects.filter(user=request.user)
    
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
