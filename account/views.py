import os
import secrets
import string
from datetime import date, datetime, timedelta

from django.contrib import auth
from django.contrib import messages as message_alert
from django.contrib.auth import authenticate
from django.contrib.auth import login as permit_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from department.models import Department
from members.models import Members
from requests.models import Requests
from resources.models import Category, Resource, ResourceTaken
from team.models import Team

from .forms import LoginUsers
from .models import Account, AccountProfile

# Maps the "role" select value on the add/edit user form to the Account
# manager method that creates that role (each sets different is_* flags).
ROLE_ACCOUNT_CREATORS = {
    'Superadmin': Account.objects.create_superuser,
    'Manager': Account.objects.create_manager,
    'IT Administrator': Account.objects.create_IT_admin,
}


def _generate_temporary_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _send_account_creation_email(request, user):
    """Email the new user their account-activation link. Deletes the account
    and returns False if the email fails to send, so we don't leave behind
    an account the owner has no way to activate."""
    try:
        current_site = get_current_site(request)
        message = render_to_string('account/account_confirmation_email.html', {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        EmailMessage('ORMS account creation', message, to=[user.email]).send()
        return True
    except Exception:
        user.delete()
        return False


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
            else:
                message = 'Invalid credentials please check!'
                message_alert.error(request, 'Invalid credentials please check!')
        else:
            message = 'Error validating form'
    return render(request, 'account/login.html', {'form': form, 'message': message})


@login_required(login_url='account:login')
def superadmin_portal(request):
    get_total_managers_count = Account.objects.filter(is_active=True, role='Manager').count()
    get_total_administrators_count = Account.objects.filter(is_active=True, role='IT Administrator').count()
    get_total_superadmins_count = Account.objects.filter(is_active=True, role='Superadmin').count()
    get_total_users_month_count = Account.objects.filter(
        is_active=True, date_joined__gte=datetime.now() - timedelta(days=30)).count()

    get_total_departments = Department.objects.filter(is_active=True).count()
    get_total_department_month_count = Department.objects.filter(
        is_active=True, created_on__gte=datetime.now() - timedelta(days=30)).count()
    get_total_teams = Team.objects.filter(is_active=True).count()
    get_total_teams_month_count = Team.objects.filter(
        is_active=True, created_date__gte=datetime.now() - timedelta(days=30)).count()

    context = {
        'get_total_managers_count': get_total_managers_count,
        'get_total_administrators_count': get_total_administrators_count,
        'get_total_superadmins_count': get_total_superadmins_count,
        'get_total_users_month_count': get_total_users_month_count,
        'get_total_departments': get_total_departments,
        'get_total_department_month_count': get_total_department_month_count,
        'get_total_teams': get_total_teams,
        'get_total_teams_month_count': get_total_teams_month_count,
    }
    return render(request, 'superadmin/superadmin_home.html', context)


@login_required(login_url='account:login')
def it_admin_portal(request, userid):
    account = Account.objects.get(id=userid)

    completed_requests_count = Requests.objects.filter(
        assigned_to=account, request_status='Completed', is_active=True).count()
    processing_requests_count = Requests.objects.filter(
        assigned_to=account, request_status='Processing', is_active=True).count()
    pending_requests_count = Requests.objects.filter(
        assigned_to=account, request_status='Pending', is_active=True).count()

    get_categories = Category.objects.filter(is_active=True)
    get_categories_count = get_categories.count()

    # Per-category resource counts, and per-category breakdown by
    # availability status, feeding the dashboard's charts.
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

    context = {
        'completed_requests_count': completed_requests_count,
        'processing_requests_count': processing_requests_count,
        'pending_requests_count': pending_requests_count,
        'get_categories_count': get_categories_count,
        'category_list': category_list,
        'category_count_list': category_count_list,
        'available_resource_list': available_resource_list,
        'taken_resource_list': taken_resource_list,
        'configuration_resource_list': configuration_resource_list,
    }
    return render(request, 'it_admin/it_administrator_dashboard.html', context)


@login_required(login_url='account:login')
def manager_portal(request, userid):
    account = Account.objects.get(id=userid)
    team = Team.objects.get(team_name=account.team)

    team_members_count = Members.objects.filter(
        manager_peoplesoft_id=account, is_active=True).order_by('peoplesoft_id').count()
    get_all_requests_count = Requests.objects.filter(created_ps_id=account, is_active=True).count()
    get_all_pending_requests_count = Requests.objects.filter(
        created_ps_id=account, request_status='Pending', is_active=True).count()
    get_all_resources_taken_count = ResourceTaken.objects.filter(
        team=team, resource_status='Taken', is_active=True).count()
    get_all_resources_returned_count = ResourceTaken.objects.filter(
        team=team, resource_status='Returned', is_active=True).count()

    get_count_members_today = Members.objects.filter(
        manager_peoplesoft_id=account, date_joined__gte=date.today()).count()
    get_count_members_week = Members.objects.filter(
        manager_peoplesoft_id=account, date_joined__gte=datetime.now() - timedelta(days=7)).count()
    get_count_members_month = Members.objects.filter(
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
            resource_category=category.resource_category, resource_status='Taken', is_active=True).count())
        request_list.append(Requests.objects.filter(
            request_resource=category.resource_category, created_ps_id=account, is_active=True).count())

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
    if Account.objects.filter(email=email).exists():
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
        role=role,
        ini_pas=password_generated,
        password=password_generated,
    )

    if _send_account_creation_email(request, user):
        message_alert.success(request, f'{role} user created successfully!')
    else:
        message_alert.info(request, 'Something went wrong!')

    return redirect('account:add_user_page')


@login_required(login_url='account:login')
def manager_user_profile(request, userid):
    account = Account.objects.get(id=userid)
    team_members_count = Members.objects.filter(
        manager_peoplesoft_id=account, is_active=True).order_by('peoplesoft_id').count()
    get_all_requests_count = Requests.objects.filter(created_ps_id=account, is_active=True).count()

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
    account = Account.objects.get(id=userid)
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
    account = Account.objects.get(id=userid)
    _update_account_profile(request, account)
    return redirect('account:superadmin_user_profile')


@login_required(login_url='account:login')
def it_admin_user_profile(request, userid):
    account = Account.objects.get(id=userid)
    completed_requests_count = Requests.objects.filter(
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
    account = Account.objects.get(id=userid)
    _update_account_profile(request, account)
    return redirect('account:it_admin_user_profile', userid)


@login_required(login_url='account:login')
def superadmin_add_user(request):
    context = {
        'users': Account.objects.all(),
        'department_names': Department.objects.filter(is_active=True),
        'team_names': Team.objects.filter(is_active=True),
    }
    return render(request, 'superadmin/display_user_page.html', context)


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
    context = {'get_user': Account.objects.get(id=uid)}
    return render(request, 'superadmin/view_user_details.html', context)


@login_required(login_url='account:login')
def edit_user(request, uid):
    context = {
        'selected_user': Account.objects.get(id=uid),
        'team_names': Team.objects.filter(is_active=True),
        'department_names': Department.objects.filter(is_active=True),
    }
    return render(request, 'superadmin/add_user_form.html', context)


@login_required(login_url='account:login')
def update_user(request, uid):
    account = Account.objects.get(id=uid)
    account.peoplesoft_id = request.POST['peoplesoft_id']
    account.first_name = request.POST['first_name']
    account.last_name = request.POST['last_name']
    account.email = request.POST['email']
    account.department = Department.objects.get(id=request.POST['department'])
    account.role = request.POST['role']

    team = request.POST['team']
    if team == '':
        message_alert.info(request, 'Please choose the team for relative department!')
        return redirect('account:edit_user', uid)

    account.team = Team.objects.get(id=team)
    account.is_superadmin = account.role == 'Superadmin'
    account.is_manager = account.role == 'Manager'
    account.is_it_admin = account.role == 'IT Administrator'
    account.is_staff = account.role == 'Superadmin'
    account.save()
    message_alert.success(request, 'User is updated successfully!')

    return redirect('account:superadmin_add_user')


@login_required(login_url='account:login')
def superadmin_users_date_sort(request):
    context = {}
    if request.method == 'POST':
        from_date = request.POST['from_user']
        to_date = request.POST['to_user']
        get_result = Account.objects.filter(date_joined__gte=from_date, date_joined__lte=to_date)
        context = {
            'get_result': get_result,
            'from_date': from_date,
            'to_date': to_date,
            'result_count': get_result.count(),
        }
    return render(request, 'superadmin/display_user_page.html', context)


@login_required(login_url='account:login')
def users_deletion_history(request):
    context = {'users': Account.objects.filter(is_active=False)}
    return render(request, 'superadmin/user_deletion_history.html', context)


@login_required(login_url='account:login')
def remove_user_access(request, uid):
    account = Account.objects.get(id=uid)
    account.is_active = False
    account.save()
    message_alert.success(request, 'User access removed successfully!')
    return redirect('account:superadmin_add_user')


@login_required(login_url='account:login')
def restore_user(request, uid):
    account = Account.objects.get(id=uid)
    account.is_active = True
    account.save()
    message_alert.success(request, 'User access restored successfully!')
    return redirect('account:users_deletion_history')


@login_required(login_url='account:login')
def permanent_delete_user(request, uid):
    if request.method == 'POST' and request.POST.get('delete_name') == 'delete':
        Account.objects.get(id=uid).delete()
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
        message = render_to_string('account/reset_password_email.html', {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        EmailMessage('ORMS Reset Password Link', message, to=[email]).send()
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
    account = Account.objects.get(id=userid)
    if request.method == 'POST':
        _process_password_change(request, account)
    return redirect('account:manager_user_profile', userid)


@login_required(login_url='account:login')
def it_admin_change_password(request, userid):
    account = Account.objects.get(id=userid)
    if request.method == 'POST':
        _process_password_change(request, account)
    return redirect('account:it_admin_user_profile', userid)


@login_required(login_url='account:login')
def superadmin_change_password(request, userid):
    account = Account.objects.get(id=userid)
    if request.method == 'POST':
        _process_password_change(request, account)
    return redirect('account:superadmin_user_profile')
