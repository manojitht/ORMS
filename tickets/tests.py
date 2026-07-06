from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from factories import (
    CategoryFactory,
    CompanyFactory,
    ITAdminAccountFactory,
    ManagerAccountFactory,
    EmployeeFactory,
    ResourceFactory,
    ResourceTakenFactory,
    SupportTicketFactory,
    TicketFactory,
)

from resources.models import Resource, ResourceTaken
from tickets.models import Ticket


class TicketModelTests(TestCase):
    def test_str_returns_request_id(self):
        ticket = TicketFactory(request_id='REQ000001')
        self.assertEqual(str(ticket), 'REQ000001')

    def test_request_id_must_be_unique_within_a_company(self):
        company = CompanyFactory()
        TicketFactory(company=company, request_id='REQ000001')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TicketFactory(company=company, request_id='REQ000001')

    def test_request_id_can_repeat_across_companies(self):
        TicketFactory(request_id='REQ000001')
        TicketFactory(request_id='REQ000001')

    def test_is_active_defaults_to_true(self):
        ticket = TicketFactory()
        self.assertTrue(ticket.is_active)

    def test_created_for_links_to_member(self):
        company = CompanyFactory()
        member = EmployeeFactory(company=company)
        ticket = TicketFactory(company=company, created_for=member)
        self.assertEqual(ticket.created_for, member)

    def test_requested_category_links_to_category(self):
        company = CompanyFactory()
        category = CategoryFactory(company=company, resource_category='Laptops')
        ticket = TicketFactory(company=company, requested_category=category)
        self.assertEqual(ticket.requested_category, category)

    def test_support_ticket_has_null_requested_category(self):
        ticket = SupportTicketFactory()
        self.assertIsNone(ticket.requested_category)
        self.assertIsNotNone(ticket.regarding_resource_taken)

    def test_resource_label_uses_requested_category_for_provisioning_ticket(self):
        company = CompanyFactory()
        category = CategoryFactory(company=company, resource_category='Laptops')
        ticket = TicketFactory(company=company, requested_category=category)
        self.assertEqual(ticket.resource_label, 'Laptops')

    def test_resource_label_uses_assigned_resource_for_support_ticket(self):
        company = CompanyFactory()
        category = CategoryFactory(company=company, resource_category='Phones')
        resource = ResourceFactory(company=company, resource_category=category)
        resource_taken = ResourceTakenFactory(company=company, asset_id=resource)
        ticket = SupportTicketFactory(company=company, regarding_resource_taken=resource_taken)
        self.assertEqual(ticket.resource_label, 'Phones')


class TicketViewSmokeTests(TestCase):
    """Confirms the tickets:* URL namespace resolves and renders end to end."""

    def test_list_requests_manager_returns_200(self):
        manager = ManagerAccountFactory()
        self.client.force_login(manager)
        response = self.client.get(reverse('tickets:list_requests_manager', args=[manager.id]))
        self.assertEqual(response.status_code, 200)

    def test_list_pending_requests_it_admin_returns_200(self):
        it_admin = ITAdminAccountFactory()
        self.client.force_login(it_admin)
        response = self.client.get(
            reverse('tickets:list_pending_requests_it_admin', args=[it_admin.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected_to_login(self):
        manager = ManagerAccountFactory()
        target = reverse('tickets:list_requests_manager', args=[manager.id])
        response = self.client.get(target)
        self.assertRedirects(
            response, f"{reverse('account:login')}?next={target}", fetch_redirect_response=False
        )

    def test_complete_processing_request_bitlocker_url_removed(self):
        # Regression guard: the dedicated Bitlocker completion view/url was
        # fully redundant with complete_processing_request's own branch and
        # was deleted outright as part of generalizing away from it.
        with self.assertRaises(NoReverseMatch):
            reverse('tickets:complete_processing_request_bitlocker', args=[1, 1])


class CompleteProcessingRequestTests(TestCase):
    def setUp(self):
        self.it_admin = ITAdminAccountFactory()
        self.client.force_login(self.it_admin)

    def test_completing_a_new_request_ticket_allocates_resource(self):
        category = CategoryFactory(company=self.it_admin.company)
        resource = ResourceFactory(company=self.it_admin.company, resource_category=category, resource_availability='Available')
        ticket = TicketFactory(
            company=self.it_admin.company, requested_category=category, request_category='Request new',
            request_status='Processing', assigned_to=self.it_admin.peoplesoft_id,
        )
        self.client.post(
            reverse('tickets:complete_processing_request', args=[ticket.id, self.it_admin.id]),
            {'asset_id': resource.asset_id, 'request_response': 'Here you go'},
        )
        ticket.refresh_from_db()
        resource.refresh_from_db()
        self.assertEqual(ticket.request_status, 'Completed')
        self.assertEqual(resource.resource_availability, 'Taken')
        self.assertTrue(ResourceTaken.all_objects.filter(asset_id=resource, peoplesoft_id=ticket.created_for).exists())

    def test_completing_a_support_ticket_does_not_allocate_a_new_resource(self):
        category = CategoryFactory(
            company=self.it_admin.company,
            attribute_schema=[{'key': 'bitlocker_key', 'label': 'BitLocker Key'}],
        )
        resource = ResourceFactory(
            company=self.it_admin.company, resource_category=category,
            attribute_values={'bitlocker_key': '483-XXXX-XXXX'},
        )
        resource_taken = ResourceTakenFactory(company=self.it_admin.company, asset_id=resource)
        ticket = SupportTicketFactory(
            company=self.it_admin.company, regarding_resource_taken=resource_taken,
            request_status='Processing', assigned_to=self.it_admin.peoplesoft_id,
        )
        resource_taken_count_before = ResourceTaken.all_objects.count()

        self.client.post(
            reverse('tickets:complete_processing_request', args=[ticket.id, self.it_admin.id]),
            {'request_response': 'Here is your key'},
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.request_status, 'Completed')
        self.assertEqual(ticket.asset_id, resource.asset_id)
        # No new ResourceTaken row should be created for a Support completion.
        self.assertEqual(ResourceTaken.all_objects.count(), resource_taken_count_before)
        self.assertIn('483-XXXX-XXXX', mail.outbox[-1].body)


class AjaxLoadEmployeeResourcesTests(TestCase):
    def setUp(self):
        self.manager = ManagerAccountFactory()
        self.client.force_login(self.manager)

    def test_only_returns_the_given_employees_taken_resources(self):
        employee = EmployeeFactory(company=self.manager.company)
        other_employee = EmployeeFactory(company=self.manager.company)
        mine = ResourceTakenFactory(company=self.manager.company, peoplesoft_id=employee, resource_status='Taken')
        ResourceTakenFactory(company=self.manager.company, peoplesoft_id=other_employee, resource_status='Taken')

        response = self.client.get(
            reverse('tickets:ajax_load_employee_resources'), {'peoplesoft_id': employee.peoplesoft_id}
        )
        self.assertContains(response, str(mine.id))
        self.assertEqual(response.content.decode().count('<option value='), 2)  # placeholder + the one match

    def test_excludes_other_companies_resources(self):
        employee = EmployeeFactory(company=self.manager.company)
        ResourceTakenFactory(peoplesoft_id__peoplesoft_id=employee.peoplesoft_id, resource_status='Taken')  # different company

        response = self.client.get(
            reverse('tickets:ajax_load_employee_resources'), {'peoplesoft_id': employee.peoplesoft_id}
        )
        self.assertContains(response, 'No currently assigned resources found')


class ExportCompletedRequestsCsvTests(TestCase):
    def test_it_admin_export_returns_csv_with_seeded_ticket(self):
        it_admin = ITAdminAccountFactory()
        ticket = TicketFactory(
            company=it_admin.company, request_id='REQ770001',
            request_status='Completed', assigned_to=it_admin.peoplesoft_id,
        )
        self.client.force_login(it_admin)

        response = self.client.get(
            reverse('tickets:export_it_admin_completed_requests_csv', args=[it_admin.id])
        )

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn(ticket.request_id, response.content.decode())

    def test_it_admin_export_excludes_other_admins_tickets(self):
        it_admin = ITAdminAccountFactory()
        other_admin = ITAdminAccountFactory(company=it_admin.company)
        TicketFactory(
            company=it_admin.company, request_id='REQ770099',
            request_status='Completed', assigned_to=other_admin.peoplesoft_id,
        )
        self.client.force_login(it_admin)

        response = self.client.get(
            reverse('tickets:export_it_admin_completed_requests_csv', args=[it_admin.id])
        )

        self.assertNotIn('REQ770099', response.content.decode())

    def test_manager_export_returns_csv_with_seeded_ticket(self):
        manager = ManagerAccountFactory()
        ticket = TicketFactory(
            company=manager.company, request_id='REQ770002',
            request_status='Completed', created_ps_id=manager.peoplesoft_id,
        )
        self.client.force_login(manager)

        response = self.client.get(
            reverse('tickets:export_manager_completed_requests_csv', args=[manager.id])
        )

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn(ticket.request_id, response.content.decode())

    def test_manager_export_excludes_other_companies_tickets(self):
        manager = ManagerAccountFactory()
        TicketFactory(request_id='REQ770098', request_status='Completed')  # different company entirely
        self.client.force_login(manager)

        response = self.client.get(
            reverse('tickets:export_manager_completed_requests_csv', args=[manager.id])
        )

        self.assertNotIn('REQ770098', response.content.decode())
