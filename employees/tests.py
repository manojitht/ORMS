from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from factories import ManagerAccountFactory, MembersFactory

# A 1x1 transparent GIF, the smallest valid image payload Pillow will accept.
TINY_GIF = SimpleUploadedFile(
    'member.gif', b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,'
    b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;', content_type='image/gif',
)


class MembersModelTests(TestCase):
    def test_str_returns_peoplesoft_id(self):
        member = MembersFactory(peoplesoft_id='PM000001')
        self.assertEqual(str(member), 'PM000001')

    def test_peoplesoft_id_must_be_unique(self):
        MembersFactory(peoplesoft_id='PM000001')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MembersFactory(peoplesoft_id='PM000001')

    def test_email_must_be_unique(self):
        MembersFactory(email='duplicate@example.com')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MembersFactory(email='duplicate@example.com')

    def test_is_active_defaults_to_true(self):
        member = MembersFactory()
        self.assertTrue(member.is_active)


class MembersViewSmokeTests(TestCase):
    """Confirms the members:* URL namespace resolves and renders end to end."""

    def setUp(self):
        self.manager = ManagerAccountFactory()
        self.client.force_login(self.manager)

    def test_view_team_members_returns_200(self):
        response = self.client.get(reverse('members:view_team_members', args=[self.manager.id]))
        self.assertEqual(response.status_code, 200)

    def test_view_team_members_details_returns_200_with_photo(self):
        member = MembersFactory(
            manager_peoplesoft_id=self.manager.peoplesoft_id, member_image=TINY_GIF
        )
        response = self.client.get(reverse('members:view_team_members_details', args=[member.id]))
        self.assertEqual(response.status_code, 200)

    def test_view_team_members_details_returns_200_without_photo(self):
        # Regression test: view_team_member_details.html used to call
        # .member_image.url unconditionally, crashing with ValueError for any
        # member with no uploaded photo. Now guarded with a placeholder image.
        member = MembersFactory(manager_peoplesoft_id=self.manager.peoplesoft_id)
        response = self.client.get(reverse('members:view_team_members_details', args=[member.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        target = reverse('members:view_team_members', args=[self.manager.id])
        response = self.client.get(target)
        self.assertRedirects(
            response, f"{reverse('account:login')}?next={target}", fetch_redirect_response=False
        )
