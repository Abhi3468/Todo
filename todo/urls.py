from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from tasks.forms import CustomPasswordResetForm

from tasks.views import login_view, verify_otp_signup, verify_otp_login, send_otp_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('api/send-otp/', send_otp_api, name='send_otp_api'),
    path('verify-otp-signup/', verify_otp_signup, name='verify_otp_signup'),
    path('verify-otp-login/', verify_otp_login, name='verify_otp_login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             form_class=CustomPasswordResetForm
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    path('', include('tasks.urls')),
]