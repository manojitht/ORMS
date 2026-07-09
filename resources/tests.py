from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from factories import (
    CategoryFactory,
    CompanyFactory,
    ITAdminAccountFactory,
    EmployeeFactory,
    ResourceFactory,
    ResourceTakenFactory,
)

from .models import OtherAccessories

# A 1x1 transparent GIF, the smallest valid image payload Pillow will accept.
TINY_GIF = SimpleUploadedFile(
    'category.gif', b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,'
    b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;', content_type='image/gif',
)


def make_tiny_gif():
    """A fresh SimpleUploadedFile per call -- the module-level TINY_GIF is a
    single stream that gets exhausted after one real upload, so any test
    that actually POSTs a file (rather than passing it to a factory) needs
    its own instance.
    """
    return SimpleUploadedFile(
        'test.gif', b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,'
        b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;', content_type='image/gif',
    )


class CategoryModelTests(TestCase):
    def test_str_returns_resource_category(self):
        category = CategoryFactory(resource_category='Laptops')
        self.assertEqual(str(category), 'Laptops')

    def test_is_active_defaults_to_true(self):
        category = CategoryFactory()
        self.assertTrue(category.is_active)

    def test_tracks_physical_asset_defaults_to_true(self):
        category = CategoryFactory()
        self.assertTrue(category.tracks_physical_asset)

    def test_attribute_schema_defaults_to_empty_list(self):
        category = CategoryFactory()
        self.assertEqual(category.attribute_schema, [])

    def test_duplicate_name_rejected_within_company(self):
        company = CompanyFactory()
        CategoryFactory(company=company, resource_category='Laptops')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CategoryFactory(company=company, resource_category='Laptops')

    def test_duplicate_name_allowed_across_companies(self):
        CategoryFactory(resource_category='Laptops')
        CategoryFactory(resource_category='Laptops')


class ResourceModelTests(TestCase):
    def test_str_returns_asset_id(self):
        resource = ResourceFactory(asset_id='ASSET00001')
        self.assertEqual(str(resource), 'ASSET00001')

    def test_asset_id_must_be_unique_within_a_company(self):
        company = CompanyFactory()
        ResourceFactory(company=company, asset_id='ASSET00001')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ResourceFactory(company=company, asset_id='ASSET00001')

    def test_asset_id_can_repeat_across_companies(self):
        ResourceFactory(asset_id='ASSET00001')
        ResourceFactory(asset_id='ASSET00001')

    def test_belongs_to_category(self):
        company = CompanyFactory()
        category = CategoryFactory(company=company, resource_category='Laptops')
        resource = ResourceFactory(company=company, resource_category=category)
        self.assertEqual(resource.resource_category, category)

    def test_attribute_values_defaults_to_empty_dict(self):
        resource = ResourceFactory()
        self.assertEqual(resource.attribute_values, {})

    def test_attribute_values_stores_arbitrary_json(self):
        resource = ResourceFactory(attribute_values={'bitlocker_key': 'ABC-123'})
        resource.refresh_from_db()
        self.assertEqual(resource.attribute_values, {'bitlocker_key': 'ABC-123'})


class ResourceTakenModelTests(TestCase):
    def test_str_returns_asset_id_of_related_resource(self):
        company = CompanyFactory()
        resource = ResourceFactory(company=company, asset_id='ASSET00002')
        resource_taken = ResourceTakenFactory(company=company, asset_id=resource)
        self.assertEqual(str(resource_taken), 'ASSET00002')

    def test_is_active_defaults_to_true(self):
        resource_taken = ResourceTakenFactory()
        self.assertTrue(resource_taken.is_active)


class OtherAccessoriesModelTests(TestCase):
    def test_str_returns_peoplesoft_id_of_related_member(self):
        member = EmployeeFactory(peoplesoft_id='PM000099')
        accessories = OtherAccessories.objects.create(
            company=member.company, peoplesoft_id=member, other_notes='spare charger'
        )
        self.assertEqual(str(accessories), 'PM000099')

    def test_peoplesoft_id_is_one_to_one(self):
        member = EmployeeFactory()
        OtherAccessories.objects.create(company=member.company, peoplesoft_id=member)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OtherAccessories.objects.create(company=member.company, peoplesoft_id=member)


class ResourcesViewSmokeTests(TestCase):
    """Confirms the resources:* URL namespace resolves and renders end to end."""

    def setUp(self):
        self.it_admin = ITAdminAccountFactory()
        self.client.force_login(self.it_admin)

    def test_resources_list_table_returns_200(self):
        response = self.client.get(reverse('resources:resources_list_table'))
        self.assertEqual(response.status_code, 200)

    def test_view_resource_categories_returns_200_with_photo(self):
        CategoryFactory(company=self.it_admin.company, category_image=TINY_GIF)
        response = self.client.get(reverse('resources:view_resource_categories'))
        self.assertEqual(response.status_code, 200)

    def test_view_resource_categories_returns_200_without_photo(self):
        # Regression test: view_categories_page.html used to call
        # .category_image.url unconditionally, crashing with ValueError for any
        # category with no uploaded image. Now guarded with a placeholder image.
        CategoryFactory(company=self.it_admin.company)
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

    def test_add_resource_page_looks_up_category_by_id_not_name(self):
        # Regression test: add_resource_page used to resolve the posted
        # category via Category.objects.get(resource_category=<name>), which
        # breaks (MultipleObjectsReturned/name drift) the moment two
        # categories share a name or the name has incidental whitespace. The
        # category name below has a trailing space specifically to prove the
        # id-based lookup doesn't care about the display text at all.
        category = CategoryFactory(company=self.it_admin.company, resource_category='Laptops ')
        response = self.client.post(reverse('resources:add_resource_page'), {
            'asset_id': 'ASSET99001',
            'model_name': 'ThinkPad X1',
            'resource_category': category.id,
            'resource_availability': 'Available',
            'resource_description': 'test',
            'added_by': 'IT Admin',
            'resource_image': make_tiny_gif(),
        })
        self.assertRedirects(response, reverse('resources:resources_listings_page'))

    def test_add_resource_page_stores_attribute_values_from_dynamic_fields(self):
        category = CategoryFactory(
            company=self.it_admin.company,
            attribute_schema=[{'key': 'bitlocker_key', 'label': 'BitLocker Key'}],
        )
        self.client.post(reverse('resources:add_resource_page'), {
            'asset_id': 'ASSET99002',
            'model_name': 'ThinkPad X1',
            'resource_category': category.id,
            'resource_availability': 'Available',
            'resource_description': 'test',
            'added_by': 'IT Admin',
            'attr__bitlocker_key': '483-XXXX-XXXX',
            'resource_image': make_tiny_gif(),
        })
        from .models import Resource
        # all_objects, not objects: there's no request-scoped company context
        # active here (the TenantManager only sees one during the request
        # that just completed via self.client.post above).
        resource = Resource.all_objects.get(asset_id='ASSET99002')
        self.assertEqual(resource.attribute_values, {'bitlocker_key': '483-XXXX-XXXX'})

    def test_add_category_page_stores_attribute_schema_and_tracks_physical_asset(self):
        self.client.post(reverse('resources:add_category_page'), {
            'resource_category': 'Phones',
            'description': 'Company mobile phones',
            'category_image': make_tiny_gif(),
            'attr_key[]': ['imei'],
            'attr_label[]': ['IMEI'],
        })
        from .models import Category
        category = Category.all_objects.get(resource_category='Phones', company=self.it_admin.company)
        self.assertEqual(category.attribute_schema, [{'key': 'imei', 'label': 'IMEI'}])

    def test_add_category_page_without_tracks_physical_asset_checkbox_sets_false(self):
        self.client.post(reverse('resources:add_category_page'), {
            'resource_category': 'Software License',
            'description': 'Per-seat software licenses',
            'category_image': make_tiny_gif(),
        })
        from .models import Category
        category = Category.all_objects.get(resource_category='Software License', company=self.it_admin.company)
        self.assertFalse(category.tracks_physical_asset)


class ExportResourcesCsvTests(TestCase):
    def test_returns_csv_with_seeded_resource(self):
        it_admin = ITAdminAccountFactory()
        resource = ResourceFactory(company=it_admin.company, asset_id='ASSET77001')
        self.client.force_login(it_admin)

        response = self.client.get(reverse('resources:export_resources_csv'))

        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.decode()
        self.assertIn('Asset Id', body.splitlines()[0])
        self.assertIn('ASSET77001', body)

    def test_excludes_other_companies_resources(self):
        it_admin = ITAdminAccountFactory()
        ResourceFactory(asset_id='ASSET77099')  # different company
        self.client.force_login(it_admin)

        response = self.client.get(reverse('resources:export_resources_csv'))

        self.assertNotIn('ASSET77099', response.content.decode())


class ResourceActivityLogTests(TestCase):
    def setUp(self):
        self.it_admin = ITAdminAccountFactory()
        self.client.force_login(self.it_admin)

    def test_add_resource_page_logs_resource_created(self):
        category = CategoryFactory(company=self.it_admin.company)
        self.client.post(reverse('resources:add_resource_page'), {
            'asset_id': 'ASSET88001', 'model_name': 'ThinkPad X1', 'resource_category': category.id,
            'resource_availability': 'Available', 'resource_description': 'test',
            'added_by': 'IT Admin', 'resource_image': make_tiny_gif(),
        })
        from activity.models import ActivityEntry
        self.assertTrue(ActivityEntry.all_objects.filter(
            action='resource_created', summary__icontains='ASSET88001').exists())

    def test_update_resource_logs_availability_change_in_summary(self):
        category = CategoryFactory(company=self.it_admin.company)
        resource = ResourceFactory(
            company=self.it_admin.company, asset_id='ASSET88002',
            resource_category=category, resource_availability='Available',
        )
        self.client.post(reverse('resources:update_resource', args=[resource.id]), {
            'asset_id': resource.asset_id, 'model_name': resource.model_name,
            'resource_category': category.id, 'resource_availability': 'Taken',
            'resource_description': '', 'added_by': 'IT Admin',
        })
        from activity.models import ActivityEntry
        entry = ActivityEntry.all_objects.filter(action='resource_updated', related_resource=resource).first()
        self.assertIsNotNone(entry)
        self.assertIn('availability: Available -> Taken', entry.summary)

    def test_update_resource_omits_availability_note_when_unchanged(self):
        category = CategoryFactory(company=self.it_admin.company)
        resource = ResourceFactory(
            company=self.it_admin.company, asset_id='ASSET88003',
            resource_category=category, resource_availability='Available',
        )
        self.client.post(reverse('resources:update_resource', args=[resource.id]), {
            'asset_id': resource.asset_id, 'model_name': 'New name', 'resource_category': category.id,
            'resource_availability': 'Available', 'resource_description': '', 'added_by': 'IT Admin',
        })
        from activity.models import ActivityEntry
        entry = ActivityEntry.all_objects.filter(action='resource_updated', related_resource=resource).first()
        self.assertIsNotNone(entry)
        self.assertNotIn('availability:', entry.summary)

    def test_update_resource_omits_warranty_note_when_the_date_is_resubmitted_unchanged(self):
        # Regression test: warranty_expiry_date starts as a real `date`
        # object (read from the DB) but the POST value is always a string --
        # comparing them directly without parsing the POST value first
        # always reads as "changed", even when it wasn't.
        category = CategoryFactory(company=self.it_admin.company)
        resource = ResourceFactory(
            company=self.it_admin.company, asset_id='ASSET88005',
            resource_category=category, warranty_expiry_date='2026-07-03',
        )
        self.client.post(reverse('resources:update_resource', args=[resource.id]), {
            'asset_id': resource.asset_id, 'model_name': resource.model_name, 'resource_category': category.id,
            'resource_availability': resource.resource_availability, 'resource_description': '',
            'added_by': 'IT Admin', 'warranty_expiry_date': '2026-07-03',
        })
        from activity.models import ActivityEntry
        entry = ActivityEntry.all_objects.filter(action='resource_updated', related_resource=resource).first()
        self.assertIsNotNone(entry)
        self.assertNotIn('warranty:', entry.summary)

    def test_delete_resource_logs_before_deleting_and_survives_it(self):
        resource = ResourceFactory(company=self.it_admin.company, asset_id='ASSET88004')
        self.client.post(reverse('resources:delete_resource', args=[resource.id]), {'delete_name': 'delete'})
        from activity.models import ActivityEntry
        from .models import Resource
        self.assertFalse(Resource.all_objects.filter(asset_id='ASSET88004').exists())
        entry = ActivityEntry.all_objects.filter(
            action='resource_deleted', summary__icontains='ASSET88004').first()
        self.assertIsNotNone(entry)
        self.assertIsNone(entry.related_resource)
