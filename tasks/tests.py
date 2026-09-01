import json
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Task, AuditLog, OTPCode


class HealthCheckTests(TestCase):
    def test_health_check_endpoint_returns_healthy_status(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('database'), 'connected')


class AuditLogImmutabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='auditor', password='safe-password-123')

    def test_audit_log_creation_and_logging(self):
        log = AuditLog.log_action(
            user=self.user,
            action="TEST_ACTION",
            ip_address="127.0.0.1",
            details="Audit log test entry"
        )
        self.assertIsNotNone(log.id)
        self.assertEqual(log.action, "TEST_ACTION")
        self.assertEqual(log.user, self.user)

    def test_audit_log_update_raises_permission_error(self):
        log = AuditLog.log_action(user=self.user, action="INITIAL_ACTION")
        log.action = "MUTATED_ACTION"
        with self.assertRaises(PermissionError):
            log.save()

    def test_audit_log_deletion_raises_permission_error(self):
        log = AuditLog.log_action(user=self.user, action="PERMANENT_ACTION")
        with self.assertRaises(PermissionError):
            log.delete()


class TaskApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='safe-password-123')
        self.other_user = User.objects.create_user(username='bob', password='safe-password-123')
        self.client.force_login(self.user)

    def test_creating_a_task_trims_its_title(self):
        response = self.client.post(
            reverse('api_task_list'),
            data=json.dumps({'title': '  Write tests  '}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.get(user=self.user).title, 'Write tests')
        # Verify audit log recorded
        self.assertTrue(AuditLog.objects.filter(action="API_TASK_CREATED").exists())

    def test_task_list_only_includes_the_current_users_tasks(self):
        own_task = Task.objects.create(user=self.user, username=self.user.username, title='Mine')
        Task.objects.create(user=self.other_user, username=self.other_user.username, title='Not mine')

        response = self.client.get(reverse('api_task_list'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], own_task.id)
        self.assertEqual(data[0]['title'], 'Mine')

    def test_api_toggle_task(self):
        task = Task.objects.create(user=self.user, username=self.user.username, title='Toggle me')
        response = self.client.post(reverse('api_toggle_task', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertTrue(task.completed)
        self.assertTrue(AuditLog.objects.filter(action="API_TASK_TOGGLED").exists())

    def test_api_delete_task(self):
        task = Task.objects.create(user=self.user, username=self.user.username, title='Delete me')
        response = self.client.delete(reverse('api_delete_task', args=[task.id]))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.filter(id=task.id).exists())
        self.assertTrue(AuditLog.objects.filter(action="API_TASK_DELETED").exists())

    def test_api_download_pdf(self):
        Task.objects.create(user=self.user, username=self.user.username, title='Export to PDF')
        response = self.client.get(reverse('api_download_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')


class TaskWebViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='webuser', password='safe-password-123')
        self.client.force_login(self.user)

    def test_web_create_task(self):
        response = self.client.post(reverse('task_list'), {'title': 'Web Task'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title='Web Task', user=self.user).exists())
        self.assertTrue(AuditLog.objects.filter(action="TASK_CREATED").exists())

    def test_web_toggle_task(self):
        task = Task.objects.create(user=self.user, username=self.user.username, title='Web Toggle')
        response = self.client.post(reverse('toggle_task', args=[task.id]))
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertTrue(task.completed)

    def test_web_delete_task(self):
        task = Task.objects.create(user=self.user, username=self.user.username, title='Web Delete')
        response = self.client.post(reverse('delete_task', args=[task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_legacy_task_toggle_requires_post(self):
        task = Task.objects.create(user=self.user, username=self.user.username, title='Protect method')
        response = self.client.get(reverse('toggle_task', args=[task.id]))
        self.assertEqual(response.status_code, 405)


class SignupFlowTests(TestCase):
    def test_signup_post_generates_otp_and_redirects(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('verify_otp_signup'))
        self.assertTrue(OTPCode.objects.filter(email='newuser@example.com').exists())

    def test_verify_otp_signup_creates_user(self):
        self.client.post(reverse('signup'), {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        otp_code = OTPCode.objects.get(email='newuser2@example.com').code
        response = self.client.post(reverse('verify_otp_signup'), {
            'otp_code': otp_code
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser2').exists())

