from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from factories import CompanyFactory, DepartmentFactory, SuperAdminAccountFactory


class DepartmentModelTests(TestCase):
    def test_str_returns_department_name(self):
        department = DepartmentFactory(department_name='Engineering')
        self.assertEqual(str(department), 'Engineering')

    def test_department_name_must_be_unique_within_a_company(self):
        company = CompanyFactory()
        DepartmentFactory(company=company, department_name='Engineering')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DepartmentFactory(company=company, department_name='Engineering')

    def test_department_name_can_repeat_across_companies(self):
        # Two different companies both naming a department "Engineering" is
        # fine — uniqueness is per-company, not global.
        DepartmentFactory(department_name='Engineering')
        DepartmentFactory(department_name='Engineering')

    def test_is_active_defaults_to_true(self):
        department = DepartmentFactory()
        self.assertTrue(department.is_active)


class DepartmentViewSmokeTests(TestCase):
    """Confirms the department:* URL namespace resolves and renders end to end."""

    def setUp(self):
        self.superadmin = SuperAdminAccountFactory()
        self.client.force_login(self.superadmin)

    def test_superadmin_department_table_returns_200(self):
        response = self.client.get(reverse('department:superadmin_department_table'))
        self.assertEqual(response.status_code, 200)

    def test_display_departments_returns_200(self):
        department = DepartmentFactory(company=self.superadmin.company)
        response = self.client.get(reverse('department:display_departments', args=[department.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('department:superadmin_department_table'))
        self.assertRedirects(
            response,
            f"{reverse('account:login')}?next={reverse('department:superadmin_department_table')}",
            fetch_redirect_response=False,
        )
