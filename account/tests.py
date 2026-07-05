from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from factories import (
    DEFAULT_PASSWORD,
    AccountFactory,
    DepartmentFactory,
    ITAdminAccountFactory,
    ManagerAccountFactory,
    SuperAdminAccountFactory,
    TeamFactory,
)

from .models import Account


class AccountManagerTests(TestCase):
    """Covers the custom MyManagerAccount methods used by account creation views."""

    def _base_kwargs(self, **overrides):
        kwargs = dict(
            peoplesoft_id='PS000001',
            first_name='Test',
            last_name='User',
            email='test.user@example.com',
            department=DepartmentFactory(),
            team=TeamFactory(),
            role='Manager',
            ini_pas='Initial@123',
            password='SecretPass1!',
        )
        kwargs.update(overrides)
        return kwargs

    def test_create_user_defaults_to_active_with_no_role_flags(self):
        user = Account.objects.create_user(**self._base_kwargs())
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_manager)
        self.assertFalse(user.is_it_admin)
        self.assertFalse(user.is_superadmin)
        self.assertTrue(user.check_password('SecretPass1!'))

    def test_create_manager_is_inactive_until_activated(self):
        user = Account.objects.create_manager(
            **self._base_kwargs(peoplesoft_id='PS000002', email='m@example.com')
        )
        self.assertTrue(user.is_manager)
        self.assertFalse(user.is_active)

    def test_create_it_admin_is_inactive_until_activated(self):
        user = Account.objects.create_IT_admin(
            **self._base_kwargs(peoplesoft_id='PS000003', email='it@example.com')
        )
        self.assertTrue(user.is_it_admin)
        self.assertFalse(user.is_active)

    def test_create_superuser_is_active_staff_and_superadmin(self):
        user = Account.objects.create_superuser(
            **self._base_kwargs(peoplesoft_id='PS000004', email='super@example.com')
        )
        self.assertTrue(user.is_superadmin)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_account_str_is_peoplesoft_id(self):
        user = Account.objects.create_user(**self._base_kwargs())
        self.assertEqual(str(user), user.peoplesoft_id)


class LoginFlowTests(TestCase):
    def setUp(self):
        self.manager = ManagerAccountFactory()
        self.it_admin = ITAdminAccountFactory()
        self.superadmin = SuperAdminAccountFactory()

    def test_valid_manager_login_redirects_to_manager_portal(self):
        response = self.client.post(reverse('account:login'), {
            'peoplesoft_id': self.manager.peoplesoft_id,
            'password': DEFAULT_PASSWORD,
        })
        self.assertRedirects(
            response, reverse('account:manager_portal', args=[self.manager.id]), fetch_redirect_response=False
        )

    def test_valid_it_admin_login_redirects_to_it_admin_portal(self):
        response = self.client.post(reverse('account:login'), {
            'peoplesoft_id': self.it_admin.peoplesoft_id,
            'password': DEFAULT_PASSWORD,
        })
        self.assertRedirects(
            response, reverse('account:it_admin_portal', args=[self.it_admin.id]), fetch_redirect_response=False
        )

    def test_valid_superadmin_login_redirects_to_superadmin_portal(self):
        response = self.client.post(reverse('account:login'), {
            'peoplesoft_id': self.superadmin.peoplesoft_id,
            'password': DEFAULT_PASSWORD,
        })
        self.assertRedirects(response, reverse('account:superadmin_portal'), fetch_redirect_response=False)

    def test_invalid_password_shows_error_and_does_not_redirect(self):
        response = self.client.post(reverse('account:login'), {
            'peoplesoft_id': self.manager.peoplesoft_id,
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials please check!')

    def test_inactive_manager_cannot_log_in(self):
        inactive_manager = ManagerAccountFactory(is_active=False)
        response = self.client.post(reverse('account:login'), {
            'peoplesoft_id': inactive_manager.peoplesoft_id,
            'password': DEFAULT_PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials please check!')

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('account:logout'))
        self.assertRedirects(response, reverse('account:login'), fetch_redirect_response=False)


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = AccountFactory()

    def test_forgot_password_sends_email_for_known_address(self):
        response = self.client.post(reverse('account:forgot_password'), {'email': self.user.email})
        self.assertRedirects(response, reverse('account:login'), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_forgot_password_rejects_unknown_address(self):
        response = self.client.post(reverse('account:forgot_password'), {'email': 'nobody@example.com'})
        self.assertRedirects(response, reverse('account:forgot_password'), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_password_flow_with_valid_token_updates_password(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.get(reverse('account:reset_password', args=[uidb64, token]))
        self.assertRedirects(response, reverse('account:reset_password_activity'), fetch_redirect_response=False)

        response = self.client.post(reverse('account:reset_password_activity'), {
            'password': 'NewSecurePass1!',
            'confirm_password': 'NewSecurePass1!',
        })
        self.assertRedirects(response, reverse('account:login'), fetch_redirect_response=False)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass1!'))

    def test_reset_password_rejects_invalid_token(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(reverse('account:reset_password', args=[uidb64, 'bad-token']))
        self.assertRedirects(response, reverse('account:login'), fetch_redirect_response=False)

    def test_activate_with_valid_token_marks_account_active(self):
        inactive_user = ManagerAccountFactory(is_active=False)
        uidb64 = urlsafe_base64_encode(force_bytes(inactive_user.pk))
        token = default_token_generator.make_token(inactive_user)

        response = self.client.get(reverse('account:activate', args=[uidb64, token]))
        self.assertRedirects(response, reverse('account:login'), fetch_redirect_response=False)

        inactive_user.refresh_from_db()
        self.assertTrue(inactive_user.is_active)


class PortalSmokeTests(TestCase):
    """These are exactly what URL namespacing (Phase 4) is most likely to break first."""

    def test_manager_portal_returns_200(self):
        manager = ManagerAccountFactory()
        self.client.force_login(manager)
        response = self.client.get(reverse('account:manager_portal', args=[manager.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('team_members_count', response.context)

    def test_it_admin_portal_returns_200(self):
        it_admin = ITAdminAccountFactory()
        self.client.force_login(it_admin)
        response = self.client.get(reverse('account:it_admin_portal', args=[it_admin.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('get_categories_count', response.context)

    def test_superadmin_portal_returns_200(self):
        superadmin = SuperAdminAccountFactory()
        self.client.force_login(superadmin)
        response = self.client.get(reverse('account:superadmin_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('get_total_managers_count', response.context)

    def test_superadmin_profile_returns_200_without_photo(self):
        # Regression test: superadmin_user_profile.html used to call
        # user.accountprofile.profile_image.url unconditionally, crashing with
        # ValueError for any account with no uploaded photo. Now guarded.
        superadmin = SuperAdminAccountFactory()
        self.client.force_login(superadmin)
        response = self.client.get(reverse('account:superadmin_user_profile'))
        self.assertEqual(response.status_code, 200)
