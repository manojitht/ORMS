from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from factories import (
    CategoryFactory,
    ITAdminAccountFactory,
    MembersFactory,
    ResourceFactory,
    ResourceTakenFactory,
)

from .models import OtherAccessories

# A 1x1 transparent GIF, the smallest valid image payload Pillow will accept.
TINY_GIF = SimpleUploadedFile(
    'category.gif', b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,'
    b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;', content_type='image/gif',
)


class CategoryModelTests(TestCase):
    def test_str_returns_resource_category(self):
        category = CategoryFactory(resource_category='Laptops')
        self.assertEqual(str(category), 'Laptops')

    def test_is_active_defaults_to_true(self):
        category = CategoryFactory()
        self.assertTrue(category.is_active)


class ResourceModelTests(TestCase):
    def test_str_returns_asset_id(self):
        resource = ResourceFactory(asset_id='ASSET00001')
        self.assertEqual(str(resource), 'ASSET00001')

    def test_asset_id_must_be_unique(self):
        ResourceFactory(asset_id='ASSET00001')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ResourceFactory(asset_id='ASSET00001')

    def test_belongs_to_category(self):
        category = CategoryFactory(resource_category='Laptops')
        resource = ResourceFactory(resource_category=category)
        self.assertEqual(resource.resource_category, category)


class ResourceTakenModelTests(TestCase):
    def test_str_returns_asset_id_of_related_resource(self):
        resource = ResourceFactory(asset_id='ASSET00002')
        resource_taken = ResourceTakenFactory(asset_id=resource)
        self.assertEqual(str(resource_taken), 'ASSET00002')

    def test_is_active_defaults_to_true(self):
        resource_taken = ResourceTakenFactory()
        self.assertTrue(resource_taken.is_active)


class OtherAccessoriesModelTests(TestCase):
    def test_str_returns_peoplesoft_id_of_related_member(self):
        member = MembersFactory(peoplesoft_id='PM000099')
        accessories = OtherAccessories.objects.create(peoplesoft_id=member, other_notes='spare charger')
        self.assertEqual(str(accessories), 'PM000099')

    def test_peoplesoft_id_is_one_to_one(self):
        member = MembersFactory()
        OtherAccessories.objects.create(peoplesoft_id=member)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OtherAccessories.objects.create(peoplesoft_id=member)


class ResourcesViewSmokeTests(TestCase):
    """Confirms the resources:* URL namespace resolves and renders end to end."""

    def setUp(self):
        self.client.force_login(ITAdminAccountFactory())

    def test_resources_list_table_returns_200(self):
        response = self.client.get(reverse('resources:resources_list_table'))
        self.assertEqual(response.status_code, 200)

    def test_view_resource_categories_returns_200_with_photo(self):
        CategoryFactory(category_image=TINY_GIF)
        response = self.client.get(reverse('resources:view_resource_categories'))
        self.assertEqual(response.status_code, 200)

    def test_view_resource_categories_returns_200_without_photo(self):
        # Regression test: view_categories_page.html used to call
        # .category_image.url unconditionally, crashing with ValueError for any
        # category with no uploaded image. Now guarded with a placeholder image.
        CategoryFactory()
        response = self.client.get(reverse('resources:view_resource_categories'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('resources:resources_list_table'))
        self.assertRedirects(
            response,
            f"{reverse('account:login')}?next={reverse('resources:resources_list_table')}",
            fetch_redirect_response=False,
        )
