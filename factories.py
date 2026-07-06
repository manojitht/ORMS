"""Shared factory_boy factories for tests across all apps.

`company` is threaded through every factory via `factory.SelfAttribute('..company')`
on nested SubFactories, so a plain `ManagerAccountFactory()` call produces a fully
coherent single-tenant object graph (account/department/team all share one company)
unless a test explicitly passes `company=` to build a specific tenant, or a different
`company=` per object to test cross-tenant isolation.
"""

import factory
from companies.models import Company
from department.models import Department
from team.models import Team
from account.models import Account
from employees.models import Employee
from resources.models import Category, Resource, ResourceTaken
from tickets.models import Ticket

DEFAULT_PASSWORD = 'TestPass123!'


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f'Company {n}')
    company_code = factory.Sequence(lambda n: f'company{n}')


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department

    company = factory.SubFactory(CompanyFactory)
    department_name = factory.Sequence(lambda n: f'Department {n}')
    department_head = factory.Faker('name')
    created_by = 'test-setup'


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    company = factory.SubFactory(CompanyFactory)
    team_name = factory.Sequence(lambda n: f'Team {n}')
    team_head = factory.Faker('name')
    department = factory.SubFactory(DepartmentFactory, company=factory.SelfAttribute('..company'))
    created_by = 'test-setup'


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account
        skip_postgeneration_save = True

    company = factory.SubFactory(CompanyFactory)
    peoplesoft_id = factory.Sequence(lambda n: f'PS{n:06d}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    department = factory.SubFactory(DepartmentFactory, company=factory.SelfAttribute('..company'))
    team = factory.SubFactory(TeamFactory, company=factory.SelfAttribute('..company'))
    ini_pas = 'Initial@123'
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or DEFAULT_PASSWORD)
        if create:
            obj.save()


class ManagerAccountFactory(AccountFactory):
    is_manager = True


class ITAdminAccountFactory(AccountFactory):
    is_it_admin = True


class SuperAdminAccountFactory(AccountFactory):
    is_superadmin = True
    is_staff = True


class EmployeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Employee

    company = factory.SubFactory(CompanyFactory)
    peoplesoft_id = factory.Sequence(lambda n: f'PM{n:06d}')
    fullname = factory.Faker('name')
    position = 'Engineer'
    email = factory.Sequence(lambda n: f'member{n}@example.com')
    contact = '0000000000'
    department = factory.SubFactory(DepartmentFactory, company=factory.SelfAttribute('..company'))
    team = factory.SubFactory(TeamFactory, company=factory.SelfAttribute('..company'))
    home_address = '123 Test Street'
    manager_name = 'Test Manager'
    manager_peoplesoft_id = factory.Sequence(lambda n: f'PS{n:06d}')


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    company = factory.SubFactory(CompanyFactory)
    resource_category = factory.Sequence(lambda n: f'Category {n}')
    description = 'A test category'
    tracks_physical_asset = True
    attribute_schema = factory.LazyFunction(list)


class ResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Resource

    company = factory.SubFactory(CompanyFactory)
    asset_id = factory.Sequence(lambda n: f'ASSET{n:05d}')
    model_name = 'Test Model'
    resource_category = factory.SubFactory(CategoryFactory, company=factory.SelfAttribute('..company'))
    attribute_values = factory.LazyFunction(dict)
    resource_availability = 'Available'
    added_by = 'test-setup'


class ResourceTakenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResourceTaken

    company = factory.SubFactory(CompanyFactory)
    asset_id = factory.SubFactory(ResourceFactory, company=factory.SelfAttribute('..company'))
    peoplesoft_id = factory.SubFactory(EmployeeFactory, company=factory.SelfAttribute('..company'))
    department = factory.SubFactory(DepartmentFactory, company=factory.SelfAttribute('..company'))
    team = factory.SubFactory(TeamFactory, company=factory.SelfAttribute('..company'))
    added_by = 'test-setup'
    resource_status = 'Taken'


class TicketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ticket

    company = factory.SubFactory(CompanyFactory)
    request_id = factory.Sequence(lambda n: f'REQ{n:06d}')
    created_for = factory.SubFactory(EmployeeFactory, company=factory.SelfAttribute('..company'))
    created_by = 'test-setup'
    created_ps_id = factory.Sequence(lambda n: f'PS{n:06d}')
    department = factory.SubFactory(DepartmentFactory, company=factory.SelfAttribute('..company'))
    team = factory.SubFactory(TeamFactory, company=factory.SelfAttribute('..company'))
    requested_category = factory.SubFactory(CategoryFactory, company=factory.SelfAttribute('..company'))
    request_category = 'Request new'
    request_status = 'Pending'
    request_decription = 'Test request description'


class SupportTicketFactory(TicketFactory):
    requested_category = None
    request_category = 'Support'
    regarding_resource_taken = factory.SubFactory(ResourceTakenFactory, company=factory.SelfAttribute('..company'))
