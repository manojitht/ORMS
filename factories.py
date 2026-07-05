"""Shared factory_boy factories for tests across all apps."""

import factory
from department.models import Department
from team.models import Team
from account.models import Account
from members.models import Members
from resources.models import Category, Resource, ResourceTaken
from requests.models import Requests

DEFAULT_PASSWORD = 'TestPass123!'


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department

    department_name = factory.Sequence(lambda n: f'Department {n}')
    department_head = factory.Faker('name')
    created_by = 'test-setup'


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    team_name = factory.Sequence(lambda n: f'Team {n}')
    team_head = factory.Faker('name')
    department = factory.SubFactory(DepartmentFactory)
    created_by = 'test-setup'


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account
        skip_postgeneration_save = True

    peoplesoft_id = factory.Sequence(lambda n: f'PS{n:06d}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    department = factory.SubFactory(DepartmentFactory)
    team = factory.SubFactory(TeamFactory)
    role = 'Manager'
    ini_pas = 'Initial@123'
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or DEFAULT_PASSWORD)
        if create:
            obj.save()


class ManagerAccountFactory(AccountFactory):
    role = 'Manager'
    is_manager = True


class ITAdminAccountFactory(AccountFactory):
    role = 'IT Administrator'
    is_it_admin = True


class SuperAdminAccountFactory(AccountFactory):
    role = 'Superadmin'
    is_superadmin = True
    is_staff = True


class MembersFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Members

    peoplesoft_id = factory.Sequence(lambda n: f'PM{n:06d}')
    fullname = factory.Faker('name')
    position = 'Engineer'
    email = factory.Sequence(lambda n: f'member{n}@example.com')
    contact = '0000000000'
    department = factory.SubFactory(DepartmentFactory)
    team = factory.SubFactory(TeamFactory)
    home_address = '123 Test Street'
    manager_name = 'Test Manager'
    manager_peoplesoft_id = factory.Sequence(lambda n: f'PS{n:06d}')


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    resource_category = factory.Sequence(lambda n: f'Category {n}')
    description = 'A test category'


class ResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Resource

    asset_id = factory.Sequence(lambda n: f'ASSET{n:05d}')
    model_name = 'Test Model'
    resource_category = factory.SubFactory(CategoryFactory)
    resource_availability = 'Available'
    added_by = 'test-setup'


class ResourceTakenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResourceTaken

    asset_id = factory.SubFactory(ResourceFactory)
    peoplesoft_id = factory.SubFactory(MembersFactory)
    resource_category = factory.Sequence(lambda n: f'Category {n}')
    department = factory.SubFactory(DepartmentFactory)
    team = factory.SubFactory(TeamFactory)
    added_by = 'test-setup'
    resource_status = 'Taken'


class RequestsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Requests

    request_id = factory.Sequence(lambda n: f'REQ{n:06d}')
    created_for = factory.SubFactory(MembersFactory)
    created_by = 'test-setup'
    created_ps_id = factory.Sequence(lambda n: f'PS{n:06d}')
    department = factory.SubFactory(DepartmentFactory)
    team = factory.SubFactory(TeamFactory)
    request_resource = 'Laptop'
    request_category = 'Hardware'
    request_status = 'Pending'
    request_decription = 'Test request description'
