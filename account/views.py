import os
from datetime import date, datetime, timedelta

from django.contrib import auth
from django.contrib import messages as message_alert
from django.contrib.auth import authenticate
from django.contrib.auth import login as permit_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.db.models import Avg, DurationField, ExpressionWrapper, F
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from department.models import Department
from employees.models import Employee
from tickets.models import Ticket
from resources.models import Category, Resource, ResourceTaken, WARRANTY_ALERT_WINDOW_DAYS
from team.models import Team

from arivom.csv_utils import csv_response
from arivom.account_provisioning import generate_temporary_password, send_account_creation_email
from notifications.services import sync_sla_overdue_notifications, sync_warranty_notifications

from .forms import LoginUsers
from .models import Account, AccountProfile

# Maps the "role" select value on the add/edit user form to the Account
# manager method that creates that role (each sets different is_* flags).
ROLE_ACCOUNT_CREATORS = {
    'Superadmin': Account.objects.create_superuser,
    'Manager': Account.objects.create_manager,
    'IT Administrator': Account.objects.create_IT_admin,
}


def _format_duration_human(td):
    """A timedelta (or None) -> a short human string for a dashboard stat
    tile, e.g. '4.2 hrs' or '1.3 days'. Built here rather than as a template
    filter to match the existing convention of assembling display strings
    in the view (see e.g. resource_label, is_overdue on Ticket).
    """
    if td is None:
        return '-'
    hours = td.total_seconds() / 3600
    if hours < 48:
        return f'{hours:.1f} hrs'
    return f'{hours / 24:.1f} days'


def _company_resource_breakdown():
    """Per-category resource counts, and per-category breakdown by
    availability status, company-wide (not scoped to one admin/manager) --
    feeds the resource charts on both the IT Admin and Superadmin dashboards.
    """
    get_categories = Category.objects.filter(is_active=True)
    category_list = []
    category_count_list = []
    available_resource_list = []
    taken_resource_list = []
    configuration_resource_list = []
    for category in get_categories:
        category_list.append(category.resource_category)
        category_count_list.append(
            Resource.objects.filter(resource_category=category.id, is_active=True).count())
        available_resource_list.append(Resource.objects.filter(
            resource_category=category.id, resource_availability='Available', is_active=True).count())
        taken_resource_list.append(Resource.objects.filter(
            resource_category=category.id, resource_availability='Taken', is_active=True).count())
        configuration_resource_list.append(Resource.objects.filter(
            resource_category=category.id, resource_availability='Configuration', is_active=True).count())
    return {
        'get_categories_count': get_categories.count(),
        'category_list': category_list,
        'category_count_list': category_count_list,
        'available_resource_list': available_resource_list,
        'taken_resource_list': taken_resource_list,
        'configuration_resource_list': configuration_resource_list,
    }


_generate_temporary_password = generate_temporary_password
_send_account_creation_email = send_account_creation_email


def _update_account_profile(request, account):
    """Apply the profile-edit form (name/email/contact/address/photo) POSTed
    for `account`, creating its AccountProfile on first edit. Returns True if
    a POST was processed."""
    if request.method != 'POST':
        return False

    profile, created = AccountProfile.objects.get_or_create(user=account)

    if 'profile_image' in request.FILES:
        if not created and profile.profile_image:
            os.remove(profile.profile_image.path)
        profile.profile_image = request.FILES['profile_image']

    account.first_name = request.POST['first_name']
    account.last_name = request.POST['last_name']
    account.email = request.POST['email']
    profile.contact_number = request.POST['contact_number']
    profile.home_address = request.POST['home_address']

    account.save()
    profile.save()
    message_alert.success(request, 'Your account details was updated successfully!')
    return True


def _process_password_change(request, account):
    """Validate and apply a change-password form POSTed for `account`.
    Returns True on success."""
    current_password = request.POST['current_password']
    new_password = request.POST['new_password']
    confirm_password = request.POST['confirm_password']

    if new_password != confirm_password:
        message_alert.error(request, 'Confirm password does not matches!')
        return False

    if not account.check_password(current_password):
        message_alert.error(request, 'Please enter the current password correctly!')
        return False

    account.set_password(new_password)
    account.save()
    message_alert.success(request, 'Your account password was changed successfully!')
    return True


def login(request):
    form = LoginUsers(request.POST or None)
    message = None
    if request.method == 'POST':
        if form.is_valid():
            peoplesoft_id = form.cleaned_data.get('peoplesoft_id')
            password = form.cleaned_data.get('password')
            user = authenticate(peoplesoft_id=peoplesoft_id, password=password)

            if user is not None and user.is_it_admin:
                permit_user(request, user)
                return redirect('account:it_admin_portal', user.id)
            elif user is not None and user.is_manager:
                permit_user(request, user)
                return redirect('account:manager_portal', user.id)
            elif user is not None and user.is_superadmin:
                permit_user(request, user)
                return redirect('account:superadmin_portal')
            elif user is not None and user.is_employee:
                permit_user(request, user)
                return redirect('account:employee_portal', user.id)
            else:
                message = 'Invalid credentials please check!'
                message_alert.error(request, 'Invalid credentials please check!')
        else:
            message = 'Error validating form'
    return render(request, 'account/login.html', {'form': form, 'message': message})


@login_required(login_url='account:login')
def superadmin_portal(request):
    company = request.user.company
    get_total_managers_count = Account.objects.filter(company=company, is_active=True, is_manager=True).count()
    get_total_administrators_count = Account.objects.filter(company=company, is_active=True, is_it_admin=True).count()
    get_total_superadmins_count = Account.objects.filter(company=company, is_active=True, is_superadmin=True).count()
    get_total_users_month_count = Account.objects.filter(
        company=company, is_active=True, date_joined__gte=datetime.now() - timedelta(days=30)).count()

    get_total_departments = Department.objects.filter(is_active=True).count()
    get_total_department_month_count = Department.objects.filter(
        is_active=True, created_on__gte=datetime.now() - timedelta(days=30)).count()
    get_total_teams = Team.objects.filter(is_active=True).count()
    get_total_teams_month_count = Team.objects.filter(
        is_active=True, created_date__gte=datetime.now() - timedelta(days=30)).count()

    # Company-wide ticket volume by status, for the "Tickets by status" chart.
    ticket_status_labels = ['Pending', 'Processing', 'Completed', 'Cancelled']
    ticket_status_counts = [
        Ticket.objects.filter(is_active=True, request_status=status).count()
        for status in ticket_status_labels
    ]

    # Accounts added per month over the last 6 months, for the user-growth
    # trend line chart -- the stat tiles above only show point-in-time counts.
    # Build the last 6 (year, month) pairs walking backwards from this month.
    user_growth_labels = []
    user_growth_counts = []
    today = datetime.now()
    year, month = today.year, today.month
    months = []
    for _ in range(6):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    for y, m in months:
        user_growth_labels.append(date(y, m, 1).strftime('%b %Y'))
        user_growth_counts.append(Account.objects.filter(
            company=company, is_active=True, date_joined__year=y, date_joined__month=m).count())

    # Company-wide SLA stats -- same shape as it_admin_portal's, just not
    # scoped to one assignee.
    avg_response_time = Ticket.objects.filter(
        is_active=True, processing_started_on__isnull=False
    ).aggregate(avg=Avg(ExpressionWrapper(F('processing_started_on') - F('created_on'), output_field=DurationField())))['avg']
    avg_resolution_time = Ticket.objects.filter(
        is_active=True, completed_on__isnull=False, processing_started_on__isnull=False
    ).aggregate(avg=Avg(ExpressionWrapper(F('completed_on') - F('processing_started_on'), output_field=DurationField())))['avg']
    open_tickets = Ticket.objects.filter(is_active=True).exclude(request_status__in=['Completed', 'Cancelled'])
    overdue_requests_count = sum(1 for t in open_tickets if t.is_overdue)

    # SLA-overdue notifications are synced from it_admin_portal instead (each
    # ticket has exactly one assigned_to IT admin, the correct recipient) --
    # warranty alerts have no owning IT admin, so they're the one ambient
    # notification superadmin's own dashboard visit also broadcasts.
    sync_warranty_notifications(company)

    context = {
        'get_total_managers_count': get_total_managers_count,
        'get_total_administrators_count': get_total_administrators_count,
        'get_total_superadmins_count': get_total_superadmins_count,
        'get_total_users_month_count': get_total_users_month_count,
        'get_total_departments': get_total_departments,
        'get_total_department_month_count': get_total_department_month_count,
        'get_total_teams': get_total_teams,
        'get_total_teams_month_count': get_total_teams_month_count,
        'ticket_status_labels': ticket_status_labels,
        'ticket_status_counts': ticket_status_counts,
        'user_growth_labels': user_growth_labels,
        'user_growth_counts': user_growth_counts,
        'avg_response_time': _format_duration_human(avg_response_time),
        'avg_resolution_time': _format_duration_human(avg_resolution_time),
        'overdue_requests_count': overdue_requests_count,
    }
    context.update(_company_resource_breakdown())
    return render(request, 'superadmin/superadmin_home.html', context)


@login_required(login_url='account:login')
def it_admin_portal(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)

    completed_requests_count = Ticket.objects.filter(
        assigned_to=account, request_status='Completed', is_active=True).count()
    processing_requests_count = Ticket.objects.filter(
        assigned_to=account, request_status='Processing', is_active=True).count()
    pending_requests_count = Ticket.objects.filter(
        assigned_to=account, request_status='Pending', is_active=True).count()

    warranty_cutoff = date.today() + timedelta(days=WARRANTY_ALERT_WINDOW_DAYS)
    expired_warranty_count = Resource.objects.filter(
        is_active=True, warranty_expiry_date__lt=date.today()).count()
    expiring_soon_warranty_count = Resource.objects.filter(
        is_active=True, warranty_expiry_date__gte=date.today(), warranty_expiry_date__lte=warranty_cutoff).count()

    avg_response_time = Ticket.objects.filter(
        assigned_to=account, is_active=True, processing_started_on__isnull=False
    ).aggregate(avg=Avg(ExpressionWrapper(F('processing_started_on') - F('created_on'), output_field=DurationField())))['avg']
    avg_resolution_time = Ticket.objects.filter(
        assigned_to=account, is_active=True, completed_on__isnull=False, processing_started_on__isnull=False
    ).aggregate(avg=Avg(ExpressionWrapper(F('completed_on') - F('processing_started_on'), output_field=DurationField())))['avg']
    open_tickets = list(Ticket.objects.filter(assigned_to=account, is_active=True).exclude(
        request_status__in=['Completed', 'Cancelled']))
    overdue_requests_count = sum(1 for t in open_tickets if t.is_overdue)

    sync_sla_overdue_notifications(account, open_tickets)
    sync_warranty_notifications(request.user.company)

    context = {
        'completed_requests_count': completed_requests_count,
        'processing_requests_count': processing_requests_count,
        'pending_requests_count': pending_requests_count,
        'expired_warranty_count': expired_warranty_count,
        'expiring_soon_warranty_count': expiring_soon_warranty_count,
        'avg_response_time': _format_duration_human(avg_response_time),
        'avg_resolution_time': _format_duration_human(avg_resolution_time),
        'overdue_requests_count': overdue_requests_count,
    }
    context.update(_company_resource_breakdown())
    return render(request, 'it_admin/it_administrator_dashboard.html', context)


@login_required(login_url='account:login')
def manager_portal(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    team = Team.objects.get(team_name=account.team)

    team_members_count = Employee.objects.filter(
        manager_peoplesoft_id=account, is_active=True).order_by('peoplesoft_id').count()
    get_all_requests_count = Ticket.objects.filter(created_ps_id=account, is_active=True).count()
    get_all_pending_requests_count = Ticket.objects.filter(
        created_ps_id=account, request_status='Pending', is_active=True).count()
    get_all_resources_taken_count = ResourceTaken.objects.filter(
        team=team, resource_status='Taken', is_active=True).count()
    get_all_resources_returned_count = ResourceTaken.objects.filter(
        team=team, resource_status='Returned', is_active=True).count()

    get_count_members_today = Employee.objects.filter(
        manager_peoplesoft_id=account, date_joined__gte=date.today()).count()
    get_count_members_week = Employee.objects.filter(
        manager_peoplesoft_id=account, date_joined__gte=datetime.now() - timedelta(days=7)).count()
    get_count_members_month = Employee.objects.filter(
        manager_peoplesoft_id=account, date_joined__gte=datetime.now() - timedelta(days=30)).count()

    # Per-category counts feeding the dashboard's charts: resources
    # currently taken by this manager's team, and requests they raised.
    get_categories = Category.objects.filter(is_active=True)
    category_list = []
    category_count_list = []
    request_list = []
    for category in get_categories:
        category_list.append(category.resource_category)
        category_count_list.append(ResourceTaken.objects.filter(
            asset_id__resource_category=category, resource_status='Taken', is_active=True).count())
        request_list.append(Ticket.objects.filter(
            requested_category=category, created_ps_id=account, is_active=True).count())

    context = {
        'team_members_count': team_members_count,
        'get_all_requests_count': get_all_requests_count,
        'get_count_members_week': get_count_members_week,
        'get_count_members_month': get_count_members_month,
        'get_count_members_today': get_count_members_today,
        'get_all_pending_requests_count': get_all_pending_requests_count,
        'get_all_resources_taken_count': get_all_resources_taken_count,
        'get_all_resources_returned_count': get_all_resources_returned_count,
        'category_list': category_list,
        'category_count_list': category_count_list,
        'request_list': request_list,
    }
    return render(request, 'manager/manager_dashboard.html', context)


@login_required(login_url='account:login')
def employee_portal(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    employee = account.employee_profile

    resources_taken_count = ResourceTaken.objects.filter(
        peoplesoft_id=employee, resource_status='Taken', is_active=True).count() if employee else 0
    my_requests_count = Ticket.objects.filter(created_ps_id=account, is_active=True).count()
    awaiting_approval_count = Ticket.objects.filter(
        created_ps_id=account, request_status='Pending Manager Approval', is_active=True).count()
    in_progress_count = Ticket.objects.filter(
        created_ps_id=account, request_status__in=['Pending', 'Processing'], is_active=True).count()
    completed_requests_count = Ticket.objects.filter(
        created_ps_id=account, request_status='Completed', is_active=True).count()

    context = {
        'employee': employee,
        'resources_taken_count': resources_taken_count,
        'my_requests_count': my_requests_count,
        'awaiting_approval_count': awaiting_approval_count,
        'in_progress_count': in_progress_count,
        'completed_requests_count': completed_requests_count,
    }
    return render(request, 'employee/employee_dashboard.html', context)


@login_required(login_url='account:login')
def employee_user_profile(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    context = { 'employee': account.employee_profile }
    return render(request, 'employee/employee_profile.html', context)


@login_required(login_url='account:login')
def employee_edit_user_profile(request):
    return render(request, 'employee/edit_employee_profile.html')


@login_required(login_url='account:login')
def employee_update_user_profile(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    _update_account_profile(request, account)
    return redirect('account:employee_user_profile', userid)


@login_required(login_url='account:login')
def employee_change_password(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    if request.method == 'POST':
        _process_password_change(request, account)
    return redirect('account:employee_user_profile', userid)


@login_required(login_url='account:login')
def add_user_page(request):
    context = {
        'department_names': Department.objects.filter(is_active=True),
        'team_names': Team.objects.filter(is_active=True),
    }

    if request.method != 'POST':
        return render(request, 'superadmin/add_user_form.html', context)

    peoplesoft_id = request.POST['peoplesoft_id']
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    email = request.POST['email']
    department = request.POST['department']
    team = request.POST['team']
    role = request.POST['role']

    if team == '':
        message_alert.info(request, 'Please choose the team for relative department!')
        return redirect('account:add_user_page')
    if role not in ROLE_ACCOUNT_CREATORS:
        message_alert.info(request, 'Please choose the role for the user!')
        return redirect('account:add_user_page')
    if Account.objects.filter(peoplesoft_id=peoplesoft_id).exists():
        message_alert.info(request, f'{peoplesoft_id}, is already exists as an user!')
        return redirect('account:add_user_page')
    if Account.objects.filter(company=request.user.company, email=email).exists():
        message_alert.info(request, 'Given email was already taken!')
        return redirect('account:add_user_page')

    password_generated = _generate_temporary_password()
    create_account = ROLE_ACCOUNT_CREATORS[role]
    user = create_account(
        peoplesoft_id=peoplesoft_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        department=Department.objects.get(id=department),
        team=Team.objects.get(id=team),
        ini_pas=password_generated,
        password=password_generated,
        company=request.user.company,
    )

    if _send_account_creation_email(request, user):
        message_alert.success(request, f'{role} user created successfully!')
    else:
        message_alert.info(request, 'Something went wrong!')

    return redirect('account:add_user_page')


@login_required(login_url='account:login')
def manager_user_profile(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    team_members_count = Employee.objects.filter(
        manager_peoplesoft_id=account, is_active=True).order_by('peoplesoft_id').count()
    get_all_requests_count = Ticket.objects.filter(created_ps_id=account, is_active=True).count()

    context = {
        'team_members_count': team_members_count,
        'get_all_requests_count': get_all_requests_count,
    }
    return render(request, 'manager/manager_user_profile.html', context)


@login_required(login_url='account:login')
def manager_edit_user_profile(request):
    return render(request, 'manager/edit_manager_profile.html')


@login_required(login_url='account:login')
def manager_update_user_profile(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    _update_account_profile(request, account)
    return redirect('account:manager_user_profile', userid)


@login_required(login_url='account:login')
def superadmin_user_profile(request):
    return render(request, 'superadmin/superadmin_user_profile.html')


@login_required(login_url='account:login')
def superadmin_edit_user_profile(request):
    return render(request, 'superadmin/edit_superadmin_profile.html')


@login_required(login_url='account:login')
def superadmin_update_user_profile(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    _update_account_profile(request, account)
    return redirect('account:superadmin_user_profile')


@login_required(login_url='account:login')
def it_admin_user_profile(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    completed_requests_count = Ticket.objects.filter(
        assigned_to=account, request_status='Completed', is_active=True).count()
    count_resources = Resource.objects.filter(is_active=True).count()

    context = {
        'completed_requests_count': completed_requests_count,
        'count_resources': count_resources,
    }
    return render(request, 'it_admin/it_admin_user_profile.html', context)


@login_required(login_url='account:login')
def it_admin_edit_user_profile(request):
    return render(request, 'it_admin/edit_it_admin_profile.html')


@login_required(login_url='account:login')
def it_admin_update_user_profile(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    _update_account_profile(request, account)
    return redirect('account:it_admin_user_profile', userid)


@login_required(login_url='account:login')
def superadmin_add_user(request):
    context = {
        'users': Account.objects.filter(company=request.user.company),
        'department_names': Department.objects.filter(is_active=True),
        'team_names': Team.objects.filter(is_active=True),
    }
    return render(request, 'superadmin/display_user_page.html', context)


@login_required(login_url='account:login')
def export_users_csv(request):
    users = Account.objects.filter(company=request.user.company)
    rows = (
        (u.peoplesoft_id, f'{u.first_name} {u.last_name}', u.department, u.team, u.role,
         u.date_joined, 'Active' if u.is_active else 'Inactive')
        for u in users
    )
    return csv_response('users.csv',
        ('PS Id', 'Fullname', 'Department', 'Team', 'Role', 'Created On', 'Status'), rows)


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()  # decode the URL token verification
        user = Account._default_manager.get(pk=uid)  # look up the account by primary key
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        message_alert.success(request, 'Welcome!, now you can login here.')
        return redirect('account:login')

    message_alert.error(request, 'OOPS!, it seems invalid link.')
    return redirect('account:login')


@login_required(login_url='account:login')
def view_user_details(request, uid):
    context = {'get_user': Account.objects.get(id=uid, company=request.user.company)}
    return render(request, 'superadmin/view_user_details.html', context)


@login_required(login_url='account:login')
def edit_user(request, uid):
    context = {
        'selected_user': Account.objects.get(id=uid, company=request.user.company),
        'team_names': Team.objects.filter(is_active=True),
        'department_names': Department.objects.filter(is_active=True),
    }
    return render(request, 'superadmin/add_user_form.html', context)


@login_required(login_url='account:login')
def update_user(request, uid):
    account = Account.objects.get(id=uid, company=request.user.company)
    account.peoplesoft_id = request.POST['peoplesoft_id']
    account.first_name = request.POST['first_name']
    account.last_name = request.POST['last_name']
    account.email = request.POST['email']
    account.department = Department.objects.get(id=request.POST['department'])

    role = request.POST['role']
    if role not in ROLE_ACCOUNT_CREATORS:
        message_alert.info(request, 'Please choose a valid role for the user!')
        return redirect('account:edit_user', uid)

    team = request.POST['team']
    if team == '':
        message_alert.info(request, 'Please choose the team for relative department!')
        return redirect('account:edit_user', uid)

    account.team = Team.objects.get(id=team)
    account.is_superadmin = role == 'Superadmin'
    account.is_manager = role == 'Manager'
    account.is_it_admin = role == 'IT Administrator'
    account.is_staff = role == 'Superadmin'
    account.save()
    message_alert.success(request, 'User is updated successfully!')

    return redirect('account:superadmin_add_user')


@login_required(login_url='account:login')
def superadmin_users_date_sort(request):
    context = {'users': None}
    if request.method == 'POST':
        from_date = request.POST['from_user']
        to_date = request.POST['to_user']
        get_result = Account.objects.filter(
            company=request.user.company, date_joined__gte=from_date, date_joined__lte=to_date)
        context = {
            'get_result': get_result,
            'from_date': from_date,
            'to_date': to_date,
            'result_count': get_result.count(),
            'users': None,
        }
    return render(request, 'superadmin/display_user_page.html', context)


@login_required(login_url='account:login')
def users_deletion_history(request):
    context = {'users': Account.objects.filter(company=request.user.company, is_active=False)}
    return render(request, 'superadmin/user_deletion_history.html', context)


@login_required(login_url='account:login')
def remove_user_access(request, uid):
    account = Account.objects.get(id=uid, company=request.user.company)
    account.is_active = False
    account.save()
    message_alert.success(request, 'User access removed successfully!')
    return redirect('account:superadmin_add_user')


@login_required(login_url='account:login')
def restore_user(request, uid):
    account = Account.objects.get(id=uid, company=request.user.company)
    account.is_active = True
    account.save()
    message_alert.success(request, 'User access restored successfully!')
    return redirect('account:users_deletion_history')


@login_required(login_url='account:login')
def permanent_delete_user(request, uid):
    if request.method == 'POST' and request.POST.get('delete_name') == 'delete':
        Account.objects.get(id=uid, company=request.user.company).delete()
        message_alert.success(request, 'User permanently deleted successfully!')
    return redirect('account:superadmin_add_user')


@login_required(login_url='account:login')
def logout(request):
    auth.logout(request)
    message_alert.success(request, 'User logged out successfully!')
    return redirect('account:login')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if not Account.objects.filter(email=email).exists():
            message_alert.error(request, 'Your email is not exists, please check!')
            return redirect('account:forgot_password')

        user = Account.objects.get(email__exact=email)
        current_site = get_current_site(request)
        context = {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        }
        text_body = render_to_string('account/reset_password_email.html', context)
        html_body = render_to_string('account/emails/reset_password_email.html', context)
        email_message = EmailMultiAlternatives('Arivom Reset Password Link', text_body, to=[email])
        email_message.attach_alternative(html_body, 'text/html')
        email_message.send()
        message_alert.success(request, 'Reset password link has been sent to your email successfully!')
        return redirect('account:login')

    return render(request, 'account/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()  # decode the URL token verification
        user = Account._default_manager.get(pk=uid)  # look up the account by primary key
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        message_alert.info(request, 'Please reset your password!')
        return redirect('account:reset_password_activity')

    message_alert.error(request, 'Seems that the link is expired!')
    return redirect('account:login')


def reset_password_activity(request):
    if request.method != 'POST':
        return render(request, 'account/reset_password_page.html')

    password = request.POST['password']
    confirm_password = request.POST['confirm_password']
    if password != confirm_password:
        message_alert.error(request, 'Passwords does not match, please check!')
        return redirect('account:reset_password_activity')

    user = Account.objects.get(pk=request.session.get('uid'))
    user.set_password(password)
    user.save()
    message_alert.success(request, 'Your password reset done sucsessfully!')
    return redirect('account:login')


def load_teams(request):
    department_id = request.GET.get('department')
    context = {'teams': Team.objects.filter(department_id=department_id).order_by('team_name')}
    return render(request, 'superadmin/teams_dropdownlist_options.html', context)


@login_required(login_url='account:login')
def manager_change_password(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    if request.method == 'POST':
        _process_password_change(request, account)
    return redirect('account:manager_user_profile', userid)


@login_required(login_url='account:login')
def it_admin_change_password(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    if request.method == 'POST':
        _process_password_change(request, account)
    return redirect('account:it_admin_user_profile', userid)


@login_required(login_url='account:login')
def superadmin_change_password(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    if request.method == 'POST':
        _process_password_change(request, account)
    return redirect('account:superadmin_user_profile')
