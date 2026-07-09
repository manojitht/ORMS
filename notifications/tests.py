from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from companies.context import set_current_company
from factories import (
    CompanyFactory,
    EmployeeAccountFactory,
    ITAdminAccountFactory,
    ManagerAccountFactory,
    SuperAdminAccountFactory,
    ResourceFactory,
    TicketFactory,
)

from notifications.models import Notification
from notifications.services import notify, sync_sla_overdue_notifications, sync_warranty_notifications
from tickets.models import SLA_HOURS_TO_START_PROCESSING, Ticket


def _backdate_created_on(ticket, created_on):
    """created_on is auto_now_add -- backdating it after the row already
    exists is only possible via a plain queryset .update(), not .save()."""
    Ticket.all_objects.filter(id=ticket.id).update(created_on=created_on)
    ticket.refresh_from_db()


class NotifyServiceTests(TestCase):
    def setUp(self):
        self.recipient = ManagerAccountFactory()
        set_current_company(self.recipient.company)

    def test_creates_a_notification_for_the_recipient(self):
        notify(self.recipient, 'ticket_created', title='A new request')
        self.assertEqual(Notification.objects.filter(recipient=self.recipient).count(), 1)

    def test_noops_silently_for_a_none_recipient(self):
        result = notify(None, 'ticket_created', title='A new request')
        self.assertIsNone(result)
        self.assertEqual(Notification.objects.count(), 0)

    def test_dedupe_key_prevents_a_duplicate_on_double_submit(self):
        notify(self.recipient, 'ticket_created', title='A new request', dedupe_key='ticket_state:1:Pending')
        notify(self.recipient, 'ticket_created', title='A new request', dedupe_key='ticket_state:1:Pending')
        self.assertEqual(Notification.objects.filter(recipient=self.recipient).count(), 1)

    def test_without_a_dedupe_key_duplicates_are_allowed(self):
        notify(self.recipient, 'ticket_created', title='A new request')
        notify(self.recipient, 'ticket_created', title='A new request')
        self.assertEqual(Notification.objects.filter(recipient=self.recipient).count(), 2)


class SyncSlaOverdueNotificationsTests(TestCase):
    def setUp(self):
        self.it_admin = ITAdminAccountFactory()
        set_current_company(self.it_admin.company)

    def _make_overdue_pending_ticket(self):
        ticket = TicketFactory(
            company=self.it_admin.company, request_status='Pending', assigned_to=self.it_admin.peoplesoft_id,
        )
        overdue_since = timezone.now() - timezone.timedelta(hours=SLA_HOURS_TO_START_PROCESSING + 1)
        _backdate_created_on(ticket, overdue_since)
        return ticket

    def test_creates_a_notification_for_an_overdue_ticket(self):
        ticket = self._make_overdue_pending_ticket()
        sync_sla_overdue_notifications(self.it_admin, [ticket])
        self.assertTrue(Notification.objects.filter(
            recipient=self.it_admin, kind='sla_overdue', related_ticket=ticket).exists())

    def test_ignores_a_ticket_that_is_not_yet_overdue(self):
        ticket = TicketFactory(
            company=self.it_admin.company, request_status='Pending', assigned_to=self.it_admin.peoplesoft_id,
        )
        sync_sla_overdue_notifications(self.it_admin, [ticket])
        self.assertFalse(Notification.objects.filter(kind='sla_overdue').exists())

    def test_is_idempotent_on_a_second_call(self):
        ticket = self._make_overdue_pending_ticket()
        sync_sla_overdue_notifications(self.it_admin, [ticket])
        sync_sla_overdue_notifications(self.it_admin, [ticket])
        self.assertEqual(
            Notification.objects.filter(recipient=self.it_admin, kind='sla_overdue').count(), 1)


class SyncWarrantyNotificationsTests(TestCase):
    def setUp(self):
        self.company = CompanyFactory()
        self.it_admin = ITAdminAccountFactory(company=self.company)
        self.superadmin = SuperAdminAccountFactory(company=self.company)
        self.manager = ManagerAccountFactory(company=self.company)  # should NOT receive warranty alerts
        set_current_company(self.company)

    def test_notifies_it_admins_and_superadmins_for_an_expired_resource(self):
        ResourceFactory(
            company=self.company, warranty_expiry_date=timezone.now().date() - timezone.timedelta(days=1))
        sync_warranty_notifications(self.company)
        alerts = Notification.objects.filter(kind='warranty_alert')
        self.assertTrue(alerts.filter(recipient=self.it_admin).exists())
        self.assertTrue(alerts.filter(recipient=self.superadmin).exists())
        self.assertFalse(alerts.filter(recipient=self.manager).exists())

    def test_ignores_a_resource_with_no_warranty_date(self):
        ResourceFactory(company=self.company, warranty_expiry_date=None)
        sync_warranty_notifications(self.company)
        self.assertFalse(Notification.objects.filter(kind='warranty_alert').exists())

    def test_ignores_a_resource_whose_warranty_is_healthy(self):
        ResourceFactory(
            company=self.company, warranty_expiry_date=timezone.now().date() + timezone.timedelta(days=365))
        sync_warranty_notifications(self.company)
        self.assertFalse(Notification.objects.filter(kind='warranty_alert').exists())

    def test_is_idempotent_on_a_second_call(self):
        ResourceFactory(
            company=self.company, warranty_expiry_date=timezone.now().date() - timezone.timedelta(days=1))
        sync_warranty_notifications(self.company)
        sync_warranty_notifications(self.company)
        self.assertEqual(
            Notification.objects.filter(recipient=self.it_admin, kind='warranty_alert').count(), 1)


class NotificationViewTests(TestCase):
    def setUp(self):
        self.account = EmployeeAccountFactory()
        set_current_company(self.account.company)
        self.client.force_login(self.account)

    def test_unread_count_returns_json_count(self):
        notify(self.account, 'ticket_completed', title='Done')
        notify(self.account, 'ticket_completed', title='Also done')
        response = self.client.get(reverse('notifications:unread_count'))
        self.assertEqual(response.json(), {'count': 2})

    def test_panel_renders_recent_notifications(self):
        notify(self.account, 'ticket_completed', title='Your laptop request is done')
        response = self.client.get(reverse('notifications:panel'))
        self.assertContains(response, 'Your laptop request is done')

    def test_panel_shows_empty_state_with_no_notifications(self):
        response = self.client.get(reverse('notifications:panel'))
        self.assertContains(response, 'No notifications yet')

    def test_open_marks_read_and_redirects_to_link_url(self):
        n = notify(self.account, 'ticket_completed', title='Done', link_url='/some/place/')
        response = self.client.get(reverse('notifications:open', args=[n.id]))
        self.assertRedirects(response, '/some/place/', fetch_redirect_response=False)
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)

    def test_open_404s_for_someone_elses_notification(self):
        other_account = EmployeeAccountFactory(company=self.account.company)
        n = notify(other_account, 'ticket_completed', title='Not yours')
        response = self.client.get(reverse('notifications:open', args=[n.id]))
        self.assertEqual(response.status_code, 404)

    def test_mark_all_read_marks_every_unread_notification(self):
        notify(self.account, 'ticket_completed', title='One')
        notify(self.account, 'ticket_completed', title='Two')
        response = self.client.post(reverse('notifications:mark_all_read'))
        self.assertEqual(response.json(), {'ok': True})
        # Query via all_objects, not the tenant-scoped default manager -- the
        # request just completed and CurrentCompanyMiddleware already reset
        # the company context back to None in its finally block.
        self.assertEqual(Notification.all_objects.filter(recipient=self.account, is_read=False).count(), 0)
        self.assertEqual(Notification.all_objects.filter(recipient=self.account, is_read=True).count(), 2)

    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('notifications:unread_count'))
        self.assertEqual(response.status_code, 302)
