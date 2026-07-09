from django.test import TestCase

from companies.context import set_current_company
from factories import ITAdminAccountFactory, ManagerAccountFactory, ResourceFactory, TicketFactory

from activity.models import ActivityEntry
from activity.services import log_activity


class LogActivityTests(TestCase):
    def setUp(self):
        self.actor = ManagerAccountFactory()
        set_current_company(self.actor.company)

    def test_creates_an_entry_with_the_given_fields(self):
        resource = ResourceFactory(company=self.actor.company)
        entry = log_activity(self.actor, 'resource_created', 'a summary', related_resource=resource)
        self.assertEqual(entry.actor, self.actor)
        self.assertEqual(entry.action, 'resource_created')
        self.assertEqual(entry.summary, 'a summary')
        self.assertEqual(entry.related_resource, resource)

    def test_does_not_dedupe_repeated_events(self):
        ticket = TicketFactory(company=self.actor.company)
        log_activity(self.actor, 'ticket_cancelled', 'cancelled once', related_ticket=ticket)
        log_activity(self.actor, 'ticket_cancelled', 'cancelled twice', related_ticket=ticket)
        self.assertEqual(ActivityEntry.objects.filter(related_ticket=ticket).count(), 2)

    def test_entries_are_ordered_newest_first(self):
        resource = ResourceFactory(company=self.actor.company)
        first = log_activity(self.actor, 'resource_created', 'first', related_resource=resource)
        second = log_activity(self.actor, 'resource_updated', 'second', related_resource=resource)
        entries = list(ActivityEntry.objects.filter(related_resource=resource))
        self.assertEqual(entries, [second, first])


class HardDeleteSurvivalTests(TestCase):
    """The whole point of SET_NULL (vs. Notification's CASCADE) is that the
    log entry describing a deletion survives the deletion itself.
    """

    def setUp(self):
        self.actor = ITAdminAccountFactory()
        set_current_company(self.actor.company)

    def test_entry_survives_a_hard_deleted_resource_with_a_readable_summary(self):
        resource = ResourceFactory(company=self.actor.company, asset_id='ASSET99999')
        entry = log_activity(
            self.actor, 'resource_deleted', 'Ivan deleted ASSET99999', related_resource=resource)
        resource.delete()
        entry.refresh_from_db()
        self.assertIsNone(entry.related_resource)
        self.assertEqual(entry.summary, 'Ivan deleted ASSET99999')

    def test_entry_survives_a_hard_deleted_ticket(self):
        ticket = TicketFactory(company=self.actor.company, request_id='REQ900001')
        entry = log_activity(
            self.actor, 'ticket_cancelled', 'cancelled REQ900001', related_ticket=ticket)
        ticket.delete()
        entry.refresh_from_db()
        self.assertIsNone(entry.related_ticket)
        self.assertEqual(entry.summary, 'cancelled REQ900001')

    def test_entry_survives_actor_account_deletion(self):
        resource = ResourceFactory(company=self.actor.company)
        entry = log_activity(self.actor, 'resource_created', 'created it', related_resource=resource)
        self.actor.delete()
        entry.refresh_from_db()
        self.assertIsNone(entry.actor)
        self.assertEqual(entry.summary, 'created it')
