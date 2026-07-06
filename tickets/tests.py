from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from factories import (
    ITAdminAccountFactory,
    ManagerAccountFactory,
    MembersFactory,
    RequestsFactory,
)


class RequestsModelTests(TestCase):
    def test_str_returns_request_id(self):
        request = RequestsFactory(request_id='REQ000001')
        self.assertEqual(str(request), 'REQ000001')

    def test_request_id_must_be_unique(self):
        RequestsFactory(request_id='REQ000001')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RequestsFactory(request_id='REQ000001')

    def test_is_active_defaults_to_true(self):
        request = RequestsFactory()
        self.assertTrue(request.is_active)

    def test_created_for_links_to_member(self):
        member = MembersFactory()
        request = RequestsFactory(created_for=member)
        self.assertEqual(request.created_for, member)


class RequestsViewSmokeTests(TestCase):
    """Confirms the requests:* URL namespace resolves and renders end to end."""

    def test_list_requests_manager_returns_200(self):
        manager = ManagerAccountFactory()
        self.client.force_login(manager)
        response = self.client.get(reverse('requests:list_requests_manager', args=[manager.id]))
        self.assertEqual(response.status_code, 200)

    def test_list_pending_requests_it_admin_returns_200(self):
        it_admin = ITAdminAccountFactory()
        self.client.force_login(it_admin)
        response = self.client.get(
            reverse('requests:list_pending_requests_it_admin', args=[it_admin.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected_to_login(self):
        manager = ManagerAccountFactory()
        target = reverse('requests:list_requests_manager', args=[manager.id])
        response = self.client.get(target)
        self.assertRedirects(
            response, f"{reverse('account:login')}?next={target}", fetch_redirect_response=False
        )
