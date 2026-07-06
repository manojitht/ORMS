from django.contrib import messages as message_alert
from django.db import transaction
from django.shortcuts import redirect, render

from account.models import Account
from department.models import Department
from team.models import Team

from .models import Company


def signup(request):
    if request.method != 'POST':
        return render(request, 'account/signup.html')

    company_name = request.POST['company_name']
    company_code = request.POST['company_code']
    peoplesoft_id = request.POST['peoplesoft_id']
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    email = request.POST['email']
    password = request.POST['password']
    confirm_password = request.POST['confirm_password']

    if password != confirm_password:
        message_alert.error(request, 'Passwords does not match, please check!')
        return redirect('companies:signup')
    if Company.objects.filter(company_code=company_code).exists():
        message_alert.info(request, f'"{company_code}" is already taken, please choose another company code!')
        return redirect('companies:signup')
    if Account.objects.filter(peoplesoft_id=peoplesoft_id).exists():
        message_alert.info(request, f'{peoplesoft_id} is already in use, please choose another peoplesoft id!')
        return redirect('companies:signup')

    full_name = f'{first_name} {last_name}'
    with transaction.atomic():
        company = Company.objects.create(name=company_name, company_code=company_code)
        # Scaffolding so the new superadmin has somewhere to land — they can
        # rename/add more departments and teams from the normal admin UI.
        department = Department.all_objects.create(
            company=company, department_name='General', department_head=full_name, created_by=full_name,
        )
        team = Team.all_objects.create(
            company=company, team_name='General', team_head=full_name, department=department, created_by=full_name,
        )
        # Active immediately (unlike Manager/IT Admin accounts): there's no
        # one else at this company yet to click an activation link.
        Account.objects.create_superuser(
            peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email,
            department=department, team=team, ini_pas=password,
            company=company, password=password,
        )

    message_alert.success(request, f'Welcome to Sukhra, {company_name}! You can log in now.')
    return redirect('account:login')
