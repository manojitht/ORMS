from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from factories import (
    DEFAULT_PASSWORD,
    AccountFactory,
    CategoryFactory,
    CompanyFactory,
    DepartmentFactory,
    ITAdminAccountFactory,
    ManagerAccountFactory,
    ResourceFactory,
    SuperAdminAccountFactory,
    TeamFactory,
    TicketFactory,
)

from .models import Account


class AccountManagerTests(TestCase):
    """Covers the custom MyManagerAccount methods used by account creation views."""

    def _base_kwargs(self, **overrides):
        company = CompanyFactory()
        kwargs = dict(
            peoplesoft_id='PS000001',
            first_name='Test',
            last_name='User',
            email='test.user@example.com',
            department=DepartmentFactory(company=company),
            team=TeamFactory(company=company),
            ini_pas='Initial@123',
            company=company,
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


class RolePropertyTests(TestCase):
    """role is computed from the is_*/boolean flags, not stored separately --
    covers the fix for a real bug where update_user used to set booleans from
    an unvalidated role string, silently zeroing all permissions on a typo.
    """

    def test_role_property_returns_superadmin(self):
        user = SuperAdminAccountFactory()
        self.assertEqual(user.role, 'Superadmin')

    def test_role_property_returns_it_administrator(self):
        user = ITAdminAccountFactory()
        self.assertEqual(user.role, 'IT Administrator')

    def test_role_property_returns_manager(self):
        user = ManagerAccountFactory()
        self.assertEqual(user.role, 'Manager')

    def test_role_property_returns_empty_string_when_no_flag_set(self):
        user = AccountFactory()
        self.assertEqual(user.role, '')

    def test_role_property_is_read_only(self):
        user = AccountFactory()
        with self.assertRaises(AttributeError):
            user.role = 'Manager'

    def test_update_user_rejects_invalid_role_without_touching_permissions(self):
        superadmin = SuperAdminAccountFactory()
        target = ManagerAccountFactory(company=superadmin.company)
        self.client.force_login(superadmin)

        response = self.client.post(reverse('account:update_user', args=[target.id]), {
            'peoplesoft_id': target.peoplesoft_id,
            'first_name': target.first_name,
            'last_name': target.last_name,
            'email': target.email,
            'department': target.department_id,
            'role': 'Not A Real Role',
            'team': target.team_id,
        })

        target.refresh_from_db()
        self.assertRedirects(response, reverse('account:edit_user', args=[target.id]))
        # The bug: an unvalidated role string used to fall through to setting
        # every boolean to False. Confirm the manager is still a manager.
        self.assertTrue(target.is_manager)
        self.assertFalse(target.is_superadmin)
        self.assertFalse(target.is_it_admin)


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

    def test_superadmin_portal_includes_chart_data(self):
        superadmin = SuperAdminAccountFactory()
        category = CategoryFactory(company=superadmin.company)
        ResourceFactory(company=superadmin.company, resource_category=category, resource_availability='Available')
        TicketFactory(company=superadmin.company, requested_category=category, request_status='Pending')
        self.client.force_login(superadmin)
        response = self.client.get(reverse('account:superadmin_portal'))
        self.assertEqual(response.status_code, 200)
        # Org composition + user growth trend
        self.assertIn('user_growth_labels', response.context)
        self.assertEqual(len(response.context['user_growth_labels']), 6)
        self.assertEqual(len(response.context['user_growth_counts']), 6)
        # Company-wide ticket status rollup
        self.assertEqual(response.context['ticket_status_labels'], ['Pending', 'Processing', 'Completed', 'Cancelled'])
        self.assertEqual(response.context['ticket_status_counts'][0], 1)  # the seeded Pending ticket
        # Company-wide resource breakdown (shared helper also used by it_admin_portal)
        self.assertIn(category.resource_category, response.context['category_list'])

    def test_superadmin_profile_returns_200_without_photo(self):
        # Regression test: superadmin_user_profile.html used to call
        # user.accountprofile.profile_image.url unconditionally, crashing with
        # ValueError for any account with no uploaded photo. Now guarded.
        superadmin = SuperAdminAccountFactory()
        self.client.force_login(superadmin)
        response = self.client.get(reverse('account:superadmin_user_profile'))
        self.assertEqual(response.status_code, 200)


class ExportUsersCsvTests(TestCase):
    def test_returns_csv_with_seeded_user(self):
        superadmin = SuperAdminAccountFactory()
        manager = ManagerAccountFactory(company=superadmin.company, peoplesoft_id='PS900001')
        self.client.force_login(superadmin)

        response = self.client.get(reverse('account:export_users_csv'))

        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.decode()
        self.assertIn('PS Id', body.splitlines()[0])
        self.assertIn(manager.peoplesoft_id, body)

    def test_excludes_other_companies_users(self):
        superadmin = SuperAdminAccountFactory()
        other_company_manager = ManagerAccountFactory(peoplesoft_id='PS900099')
        self.client.force_login(superadmin)

        response = self.client.get(reverse('account:export_users_csv'))

        self.assertNotIn(other_company_manager.peoplesoft_id, response.content.decode())
