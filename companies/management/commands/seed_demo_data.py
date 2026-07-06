from django.core.management.base import BaseCommand

from companies.context import set_current_company
from companies.models import Company
from department.models import Department
from team.models import Team
from account.models import Account
from resources.models import Category, Resource, ResourceTaken
from employees.models import Employee
from tickets.models import Ticket

CREDENTIALS = [
    ('Superadmin', '10000001', 'SuperPass1!'),
    ('Manager', '10000002', 'ManagerPass1!'),
    ('IT Administrator', '10000003', 'ITAdminPass1!'),
]


class Command(BaseCommand):
    help = (
        'Seed one demo company with accounts, categories, resources, an '
        'employee, and tickets in every lifecycle state -- so local dev has '
        'something to look at without clicking through the whole signup + '
        'setup flow by hand.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--company-code', default='demo', help='Slug for the demo company (default: demo)')
        parser.add_argument('--company-name', default='Demo Co', help='Display name for the demo company')
        parser.add_argument(
            '--reset', action='store_true',
            help='Delete an existing company with this code first, then recreate it.',
        )

    def handle(self, *args, **options):
        company_code = options['company_code']
        company_name = options['company_name']

        existing = Company.objects.filter(company_code=company_code).first()
        if existing:
            if not options['reset']:
                self.stdout.write(self.style.WARNING(
                    f'Company "{company_code}" already exists (id={existing.id}). '
                    'Re-run with --reset to wipe and recreate it.'
                ))
                return
            existing.delete()
            self.stdout.write(self.style.WARNING(f'Deleted existing company "{company_code}".'))

        company = Company.objects.create(name=company_name, company_code=company_code)
        set_current_company(company)

        dept = Department.objects.create(
            company=company, department_name='General', department_head='Sam Owner', created_by='seed')
        team = Team.objects.create(
            company=company, team_name='General', team_head='Sam Owner', department=dept, created_by='seed')

        superadmin = Account.objects.create_superuser(
            peoplesoft_id='10000001', first_name='Sam', last_name='Owner', email='sam@demo.example',
            department=dept, team=team, ini_pas='SuperPass1!', company=company, password='SuperPass1!')

        manager = Account.objects.create_manager(
            peoplesoft_id='10000002', first_name='Mia', last_name='Manager', email='mia@demo.example',
            department=dept, team=team, ini_pas='ManagerPass1!', company=company, password='ManagerPass1!')
        manager.is_active = True
        manager.save()

        it_admin = Account.objects.create_IT_admin(
            peoplesoft_id='10000003', first_name='Ivan', last_name='Admin', email='ivan@demo.example',
            department=dept, team=team, ini_pas='ITAdminPass1!', company=company, password='ITAdminPass1!')
        it_admin.is_active = True
        it_admin.save()

        laptops = Category.objects.create(
            company=company, resource_category='Laptops', description='Company laptops',
            attribute_schema=[{'key': 'bitlocker_key', 'label': 'BitLocker Key'}])
        phones = Category.objects.create(
            company=company, resource_category='Phones', description='Company mobile phones',
            attribute_schema=[{'key': 'imei', 'label': 'IMEI'}])

        laptop_resources = [
            Resource.objects.create(
                company=company, asset_id=f'LAP-{i:03d}', model_name='ThinkPad X1', resource_category=laptops,
                resource_availability='Available' if i < 3 else 'Taken', added_by='seed',
                attribute_values={'bitlocker_key': f'483-DEMO-{i:03d}'})
            for i in range(5)
        ]
        for i in range(3):
            Resource.objects.create(
                company=company, asset_id=f'PHN-{i:03d}', model_name='iPhone 15', resource_category=phones,
                resource_availability='Available', added_by='seed', attribute_values={'imei': f'00000000000{i}'})

        employee = Employee.objects.create(
            company=company, peoplesoft_id='10000010', fullname='Eve Employee', position='Software Engineer',
            email='eve@demo.example', contact='5551234567', department=dept, team=team, home_address='1 Main St',
            manager_name='Mia Manager', manager_peoplesoft_id='10000002')

        taken = ResourceTaken.objects.create(
            company=company, asset_id=laptop_resources[3], peoplesoft_id=employee, department=dept, team=team,
            added_by='seed', assigned_by='Ivan Admin', resource_status='Taken')

        ticket_specs = [
            ('Request new', 'Pending', laptops, None),
            ('Request new', 'Processing', laptops, None),
            ('Request new', 'Completed', laptops, None),
            ('Support', 'Completed', None, taken),
            ('Replacement', 'Cancelled', phones, None),
        ]
        for i, (request_category, status, category, resource_taken) in enumerate(ticket_specs):
            Ticket.objects.create(
                company=company, request_id=f'REQ{i:06d}', created_for=employee, created_by='Mia Manager',
                created_ps_id='10000002', department=dept, team=team, requested_category=category,
                regarding_resource_taken=resource_taken, request_category=request_category,
                request_status=status, request_decription='Seeded demo ticket', assigned_to='10000003')

        self.stdout.write(self.style.SUCCESS(f'\nSeeded company "{company_name}" (code: {company_code}).\n'))
        self.stdout.write('Log in at /account/login_page with:\n')
        for role, peoplesoft_id, password in CREDENTIALS:
            self.stdout.write(f'  {role:<17} PeopleSoft ID {peoplesoft_id}   password {password}')
        self.stdout.write('')
