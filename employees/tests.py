from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from factories import CompanyFactory, ManagerAccountFactory, EmployeeFactory

# A 1x1 transparent GIF, the smallest valid image payload Pillow will accept.
TINY_GIF = SimpleUploadedFile(
    'member.gif', b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,'
    b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;', content_type='image/gif',
)


class EmployeeModelTests(TestCase):
    def test_str_returns_peoplesoft_id(self):
        employee = EmployeeFactory(peoplesoft_id='PM000001')
        self.assertEqual(str(employee), 'PM000001')

    def test_peoplesoft_id_must_be_unique_within_a_company(self):
        company = CompanyFactory()
        EmployeeFactory(company=company, peoplesoft_id='PM000001')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmployeeFactory(company=company, peoplesoft_id='PM000001')

    def test_peoplesoft_id_can_repeat_across_companies(self):
        EmployeeFactory(peoplesoft_id='PM000001')
        EmployeeFactory(peoplesoft_id='PM000001')

    def test_email_must_be_unique_within_a_company(self):
        company = CompanyFactory()
        EmployeeFactory(company=company, email='duplicate@example.com')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmployeeFactory(company=company, email='duplicate@example.com')

    def test_is_active_defaults_to_true(self):
        employee = EmployeeFactory()
        self.assertTrue(employee.is_active)


class EmployeeViewSmokeTests(TestCase):
    """Confirms the employees:* URL namespace resolves and renders end to end."""

    def setUp(self):
        self.manager = ManagerAccountFactory()
        self.client.force_login(self.manager)

    def test_view_team_members_returns_200(self):
        response = self.client.get(reverse('employees:view_team_members', args=[self.manager.id]))
        self.assertEqual(response.status_code, 200)

    def test_view_team_members_details_returns_200_with_photo(self):
        employee = EmployeeFactory(
            company=self.manager.company, manager_peoplesoft_id=self.manager.peoplesoft_id, member_image=TINY_GIF
        )
        response = self.client.get(reverse('employees:view_team_members_details', args=[employee.id]))
        self.assertEqual(response.status_code, 200)

    def test_view_team_members_details_returns_200_without_photo(self):
        # Regression test: view_team_member_details.html used to call
        # .member_image.url unconditionally, crashing with ValueError for any
        # employee with no uploaded photo. Now guarded with a placeholder image.
        employee = EmployeeFactory(company=self.manager.company, manager_peoplesoft_id=self.manager.peoplesoft_id)
        response = self.client.get(reverse('employees:view_team_members_details', args=[employee.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        target = reverse('employees:view_team_members', args=[self.manager.id])
        response = self.client.get(target)
        self.assertRedirects(
            response, f"{reverse('account:login')}?next={target}", fetch_redirect_response=False
        )


class ExportTeamMembersCsvTests(TestCase):
    def test_returns_csv_with_seeded_team_member(self):
        manager = ManagerAccountFactory()
        employee = EmployeeFactory(company=manager.company, manager_peoplesoft_id=manager.peoplesoft_id, peoplesoft_id='PM880001')
        self.client.force_login(manager)

        response = self.client.get(reverse('employees:export_team_members_csv', args=[manager.id]))

        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.decode()
        self.assertIn('PS Id', body.splitlines()[0])
        self.assertIn(employee.peoplesoft_id, body)

    def test_excludes_other_managers_team_members(self):
        manager = ManagerAccountFactory()
        other_manager = ManagerAccountFactory(company=manager.company)
        EmployeeFactory(company=manager.company, manager_peoplesoft_id=other_manager.peoplesoft_id, peoplesoft_id='PM880099')
        self.client.force_login(manager)

        response = self.client.get(reverse('employees:export_team_members_csv', args=[manager.id]))

        self.assertNotIn('PM880099', response.content.decode())
