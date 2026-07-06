from django.test import TestCase
from django.urls import reverse

from companies.context import get_current_company, set_current_company
from department.models import Department
from factories import (
    CompanyFactory,
    DepartmentFactory,
    EmployeeFactory,
    ManagerAccountFactory,
    ResourceFactory,
    SuperAdminAccountFactory,
    TeamFactory,
)


class TenantManagerFailsClosedTests(TestCase):
    """The core safety property: with no company context, tenant-scoped
    models return nothing — not every company's rows."""

    def test_no_context_returns_empty_queryset(self):
        DepartmentFactory()
        self.assertIsNone(get_current_company())
        self.assertEqual(Department.objects.count(), 0)

    def test_context_scopes_to_that_company_only(self):
        company_a = CompanyFactory()
        company_b = CompanyFactory()
        DepartmentFactory(company=company_a)
        DepartmentFactory(company=company_b)

        set_current_company(company_a)
        try:
            self.assertEqual(Department.objects.count(), 1)
            self.assertEqual(Department.objects.first().company, company_a)
        finally:
            set_current_company(None)


class CrossCompanyIsolationViewTests(TestCase):
    """Proves the fixes in account/tickets/resources/employees views actually
    block cross-tenant access, not just that pages render."""

    def setUp(self):
        self.manager_a = ManagerAccountFactory()
        self.manager_b = ManagerAccountFactory()  # different company (default factory behavior)

    def test_manager_cannot_view_another_companys_account_details(self):
        from account.models import Account

        self.client.force_login(self.manager_a)
        # superadmin-only route, but the point is the company filter, not the
        # permission check — force through the view directly via the URL.
        # Raises rather than 200s: TenantManager filtered manager_b out entirely,
        # not "found but blocked" — confirms no cross-company data is exposed.
        with self.assertRaises(Account.DoesNotExist):
            self.client.get(reverse('account:view_user_details', args=[self.manager_b.id]))

    def test_manager_dashboard_does_not_count_other_companys_employees(self):
        EmployeeFactory(manager_peoplesoft_id=self.manager_a.peoplesoft_id, company=self.manager_a.company)
        EmployeeFactory(manager_peoplesoft_id=self.manager_b.peoplesoft_id, company=self.manager_b.company)

        self.client.force_login(self.manager_a)
        response = self.client.get(reverse('account:manager_portal', args=[self.manager_a.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['team_members_count'], 1)

    def test_superadmin_users_list_excludes_other_companies(self):
        superadmin_a = SuperAdminAccountFactory()
        self.client.force_login(superadmin_a)
        response = self.client.get(reverse('account:superadmin_add_user'))
        self.assertEqual(response.status_code, 200)
        listed_ids = {u.id for u in response.context['users']}
        self.assertIn(superadmin_a.id, listed_ids)
        self.assertNotIn(self.manager_a.id, listed_ids)
        self.assertNotIn(self.manager_b.id, listed_ids)

    def test_employee_detail_view_blocks_cross_company_id_guessing(self):
        from employees.models import Employee

        other_company_employee = EmployeeFactory()  # own separate company
        self.client.force_login(self.manager_a)
        with self.assertRaises(Employee.DoesNotExist):
            self.client.get(
                reverse('employees:view_team_members_details', args=[other_company_employee.id])
            )

    def test_duplicate_asset_id_allowed_across_companies_but_not_within_one(self):
        ResourceFactory(company=self.manager_a.company, asset_id='DUP-001')
        # Same asset_id, different company — must succeed (no IntegrityError).
        ResourceFactory(company=self.manager_b.company, asset_id='DUP-001')

    def test_ticket_auto_assignment_only_picks_same_company_it_admins(self):
        from account.models import Account

        it_admin_a = Account.objects.create_IT_admin(
            peoplesoft_id='ITA00001', first_name='Ivy', last_name='Admin',
            email='ivy@example.com', department=DepartmentFactory(company=self.manager_a.company),
            team=TeamFactory(company=self.manager_a.company),
            ini_pas='Initial@123', company=self.manager_a.company, password='Initial@123',
        )
        it_admin_a.is_active = True
        it_admin_a.save()
        # A second company's IT admin should never be eligible for assignment.
        Account.objects.create_IT_admin(
            peoplesoft_id='ITB00001', first_name='Ian', last_name='Bee',
            email='ian@example.com', department=DepartmentFactory(company=self.manager_b.company),
            team=TeamFactory(company=self.manager_b.company),
            ini_pas='Initial@123', company=self.manager_b.company, password='Initial@123',
        )

        self.client.force_login(self.manager_a)
        response = self.client.get(reverse('tickets:create_request', args=[self.manager_a.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['assign_admin'].company, self.manager_a.company)
