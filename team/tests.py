from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from factories import DepartmentFactory, SuperAdminAccountFactory, TeamFactory


class TeamModelTests(TestCase):
    def test_str_returns_team_name(self):
        team = TeamFactory(team_name='Platform')
        self.assertEqual(str(team), 'Platform')

    def test_team_name_must_be_unique(self):
        TeamFactory(team_name='Platform')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TeamFactory(team_name='Platform')

    def test_team_belongs_to_department(self):
        department = DepartmentFactory(department_name='Engineering')
        team = TeamFactory(department=department)
        self.assertEqual(team.department, department)

    def test_is_active_defaults_to_true(self):
        team = TeamFactory()
        self.assertTrue(team.is_active)


class TeamViewSmokeTests(TestCase):
    """Confirms the team:* URL namespace resolves and renders end to end."""

    def setUp(self):
        self.client.force_login(SuperAdminAccountFactory())

    def test_superadmin_team_table_returns_200(self):
        response = self.client.get(reverse('team:superadmin_team_table'))
        self.assertEqual(response.status_code, 200)

    def test_display_team_returns_200(self):
        team = TeamFactory()
        response = self.client.get(reverse('team:display_team', args=[team.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('team:superadmin_team_table'))
        self.assertRedirects(
            response,
            f"{reverse('account:login')}?next={reverse('team:superadmin_team_table')}",
            fetch_redirect_response=False,
        )
