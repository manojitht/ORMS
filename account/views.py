# from email import message as message_alert
from base64 import urlsafe_b64decode
from email.message import EmailMessage
from genericpath import exists
from importlib.resources import Resource
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from .forms import LoginUsers
from django.contrib.auth import authenticate, login as permit_user
from .models import Account, AccountProfile
from django.contrib import messages as message_alert, auth
from django.contrib.auth.decorators import login_required
from department.models import Department
from team.models import Team
from members.models import Members
from requests.models import Requests
from resource.models import ResourceTaken, Resource, Category
from datetime import datetime, timedelta, date
from django.core import serializers
import json
import os

#generating random password
import string
import secrets

#sending mail library
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
                return redirect('it_admin_portal', user.id)
            elif user is not None and user.is_manager:
                permit_user(request, user)
                return redirect('manager_portal', user.id)
            elif user is not None and user.is_superadmin:
                permit_user(request, user)
                return redirect('superadmin_portal')
            else:
                # if user is not None and user.is_active != True:
                #     message = 'Please activate your account!'
                #     message_alert.info(request, 'Please activate your account!')
                # else:
                message = 'Invalid credentials please check!'
                message_alert.error(request, 'Invalid credentials please check!')
        else:
            message = 'Error validating form'
    return render(request, 'account/login.html', {'form': form, 'message': message})

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def superadmin_portal(request):
    
    total_managers = Account.objects.filter(is_active=True, role='Manager')
    get_total_managers_count = total_managers.count()
    total_it_administrators = Account.objects.filter(is_active=True, role='IT Administrator')
    get_total_administrators_count = total_it_administrators.count()
    total_superadmins = Account.objects.filter(is_active=True, role='Superadmin')
    get_total_superadmins_count = total_superadmins.count()
    total_users_month = Account.objects.filter(is_active=True, date_joined__gte=datetime.now()-timedelta(days=30))
    get_total_users_month_count = total_users_month.count()

    total_departments = Department.objects.filter(is_active=True)
    get_total_departments = total_departments.count()
    total_departments_month = Department.objects.filter(is_active=True, created_on__gte=datetime.now()-timedelta(days=30))
    get_total_department_month_count = total_departments_month.count()
    total_teams = Team.objects.filter(is_active=True)
    get_total_teams = total_teams.count()
    total_teams_month = Team.objects.filter(is_active=True, created_date__gte=datetime.now()-timedelta(days=30))
    get_total_teams_month_count = total_teams_month.count()

    context = {'get_total_managers_count': get_total_managers_count, 
    'get_total_administrators_count': get_total_administrators_count, 
    'get_total_superadmins_count': get_total_superadmins_count, 
    'get_total_users_month_count': get_total_users_month_count, 
    'get_total_departments': get_total_departments, 
    'get_total_department_month_count': get_total_department_month_count,
    'get_total_teams': get_total_teams, 
    'get_total_teams_month_count': get_total_teams_month_count, }

    return render(request, 'superadmin/superadmin_home.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def it_admin_portal(request, userid):
    # count of requests completed
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    completed_requests = Requests.objects.all().filter(assigned_to=get_user_psid, request_status='Completed', is_active=True)
    completed_requests_count = completed_requests.count()

    # count of requests processing
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    processing_requests = Requests.objects.all().filter(assigned_to=get_user_psid, request_status='Processing', is_active=True)
    processing_requests_count = processing_requests.count()

    # count of requests pending
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    pending_requests = Requests.objects.all().filter(assigned_to=get_user_psid, request_status='Pending', is_active=True)
    pending_requests_count = pending_requests.count()

    # count of resource categories
    get_categories = Category.objects.filter(is_active=True)
    get_categories_count = get_categories.count()

    # resource categories dashboard info
    category_list = []
    category_count_list = []
    for category in get_categories:
        category_list.append(category.resource_category)
        get_resources = Resource.objects.filter(resource_category=category.id, is_active=True)
        count_resources = get_resources.count()
        category_count_list.append(count_resources)

    # resources dashboard info
    available_resource_list = []
    taken_resource_list = []
    configuration_resource_list = []
    for resource_cat in get_categories:
        get_available_resources = Resource.objects.filter(resource_category=resource_cat.id, resource_availability='Available', is_active=True)
        count_available_resources = get_available_resources.count()
        available_resource_list.append(count_available_resources)

        get_taken_resources = Resource.objects.filter(resource_category=resource_cat.id, resource_availability='Taken', is_active=True)
        count_taken_resources = get_taken_resources.count()
        taken_resource_list.append(count_taken_resources)

        get_configuration_resources = Resource.objects.filter(resource_category=resource_cat.id, resource_availability='Configuration', is_active=True)
        count_configuration_resources = get_configuration_resources.count()
        configuration_resource_list.append(count_configuration_resources)
    

    context = { 'completed_requests_count': completed_requests_count,
     'processing_requests_count': processing_requests_count, 
     'pending_requests_count': pending_requests_count, 
     'get_categories_count': get_categories_count,
     'category_list': category_list,
     'category_count_list': category_count_list,
     'available_resource_list': available_resource_list,
     'taken_resource_list': taken_resource_list,
     'configuration_resource_list': configuration_resource_list, }

    return render(request, 'it_admin/it_administrator_dashboard.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def manager_portal(request, userid):
    # total no of team members
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    team_members = Members.objects.all().filter(manager_peoplesoft_id=get_user_psid, 
    is_active=True).order_by('peoplesoft_id')
    team_members_count = team_members.count()

    # total no of requests created
    get_all_requests = Requests.objects.all().filter(created_ps_id=get_user_psid, 
    is_active=True)
    get_all_requests_count = get_all_requests.count()

    # total no of requests on pending
    get_all_pending_requests = Requests.objects.all().filter(created_ps_id=get_user_psid, 
    request_status='Pending', is_active=True)
    get_all_pending_requests_count = get_all_pending_requests.count()

    # total resource taken by team
    resources_taken = ResourceTaken.objects.filter(team=Team.objects.get(team_name=get_user_id.team), 
    resource_status='Taken', is_active=True)
    get_all_resources_taken_count = resources_taken.count()

    # total resource taken by team
    resources_returned = ResourceTaken.objects.filter(team=Team.objects.get(team_name=get_user_id.team), 
    resource_status='Returned', is_active=True)
    get_all_resources_returned_count = resources_returned.count()

    # total no of users added today
    members_today = Members.objects.filter(manager_peoplesoft_id=get_user_psid, 
    date_joined__gte=date.today())
    get_count_members_today = members_today.count()

    # total no of users added this week
    members_week = Members.objects.filter(manager_peoplesoft_id=get_user_psid, 
    date_joined__gte=datetime.now()-timedelta(days=7))
    get_count_members_week = members_week.count()

    # total no of users added this month
    members_month = Members.objects.filter(manager_peoplesoft_id=get_user_psid, 
    date_joined__gte=datetime.now()-timedelta(days=30))
    get_count_members_month = members_month.count()

    # resource categories dashboard info
    get_categories = Category.objects.filter(is_active=True)
    category_list = []
    category_count_list = []
    for category in get_categories:
        category_list.append(category.resource_category)
        get_resources = ResourceTaken.objects.filter(resource_category=category.resource_category, resource_status='Taken', is_active=True)
        count_resources = get_resources.count()
        category_count_list.append(count_resources)

    # request count on dashboard info
    request_list = []
    for resource_cat in get_categories:
        get_requests = Requests.objects.filter(request_resource=resource_cat.resource_category, created_ps_id=get_user_psid, is_active=True)
        request_count = get_requests.count()
        request_list.append(request_count)

    context = { 'team_members_count': team_members_count,
     'get_all_requests_count': get_all_requests_count,
     'get_count_members_week': get_count_members_week,
     'get_count_members_month': get_count_members_month,
     'get_count_members_today': get_count_members_today,
     'get_all_pending_requests_count': get_all_pending_requests_count, 
     'get_all_resources_taken_count': get_all_resources_taken_count, 
     'get_all_resources_returned_count': get_all_resources_returned_count,
     'category_list': category_list,
     'category_count_list': category_count_list, 
     'request_list': request_list, }
    
    return render(request, 'manager/manager_dashboard.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def add_user_page(request):

    department_names = Department.objects.all().filter(is_active=True)
    team_names = Team.objects.all().filter(is_active=True)

    context = {
        'department_names': department_names,
        'team_names': team_names,
    }
    
    if request.method == 'POST':
        peoplesoft_id = request.POST['peoplesoft_id']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        department = request.POST['department']
        team = request.POST['team']
        role = request.POST['role']
        characters = string.ascii_letters + string.digits
        password_generated = ''.join(secrets.choice(characters) for i in range(10))
        if team == '':
            message_alert.info(request, 'Please choose the team for relative department!')
            return redirect(add_user_page)
        elif role == '--Choose role--':
            message_alert.info(request, 'Please choose the role for the user!')
            return redirect(add_user_page)
        else:
            if Account.objects.filter(peoplesoft_id=peoplesoft_id).exists():
                message_alert.info(request, peoplesoft_id + ', is already exists as an user!')
                return redirect('add_user_page')
            elif Account.objects.filter(email=email).exists():
                message_alert.info(request, 'Given email was already taken!')
                return redirect('add_user_page')
            else:
                if Account.objects.filter(email=email).exists():
                    message_alert.info(request, 'Given email was already taken!')
                    return redirect('add_user_page')
                else:
                    if role == 'Superadmin':
                        user  = Account.objects.create_superuser(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=Department.objects.get(id=department), team=Team.objects.get(id=team), role=role, ini_pas=password_generated, password=password_generated)
                        #Send email to user
                        try: 
                            current_site = get_current_site(request)
                            mail_head_subject = 'ORMS account creation'
                            message = render_to_string('account/account_confirmation_email.html', {
                                'user': user,
                                'domain': current_site,
                                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                'token': default_token_generator.make_token(user),
                            })
                            to_email = email
                            send_email = EmailMessage(mail_head_subject, message, to=[to_email])
                            send_email.send()
                            user.save()
                            message_alert.success(request, 'Superadmin user created successfully!')
                        except: 
                            message_alert.info(request, 'Something went wrong!')
                            user.delete()
                        return redirect('add_user_page')
                    elif role == 'Manager':
                        user  = Account.objects.create_manager(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=Department.objects.get(id=department), team=Team.objects.get(id=team), role=role, ini_pas=password_generated, password=password_generated)
                        try: 
                            current_site = get_current_site(request)
                            mail_head_subject = 'ORMS account creation'
                            message = render_to_string('account/account_confirmation_email.html', {
                                'user': user,
                                'domain': current_site,
                                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                'token': default_token_generator.make_token(user),
                            })
                            to_email = email
                            send_email = EmailMessage(mail_head_subject, message, to=[to_email])
                            send_email.send()
                            user.save()
                            message_alert.success(request, 'Manager user created successfully!')
                        except: 
                            message_alert.info(request, 'Something went wrong!')
                            user.delete()
                        return redirect('add_user_page')
                    elif role == 'IT Administrator':
                        user  = Account.objects.create_IT_admin(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=Department.objects.get(id=department), team=Team.objects.get(id=team), role=role, ini_pas=password_generated, password=password_generated)
                        try: 
                            current_site = get_current_site(request)
                            mail_head_subject = 'ORMS account creation'
                            message = render_to_string('account/account_confirmation_email.html', {
                                'user': user,
                                'domain': current_site,
                                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                'token': default_token_generator.make_token(user),
                            })
                            to_email = email
                            send_email = EmailMessage(mail_head_subject, message, to=[to_email])
                            send_email.send()
                            user.save()
                            message_alert.success(request, 'IT Administrator user created successfully!')
                        except: 
                            message_alert.info(request, 'Something went wrong!')
                            user.delete()
                        return redirect('add_user_page')
    else:
        pass
    return render(request, 'superadmin/add_user_form.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def manager_user_profile(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    team_members = Members.objects.all().filter(manager_peoplesoft_id=get_user_psid, 
    is_active=True).order_by('peoplesoft_id')
    team_members_count = team_members.count()
    get_all_requests = Requests.objects.all().filter(created_ps_id=get_user_psid, 
    is_active=True)
    get_all_requests_count = get_all_requests.count()

    context = {'team_members_count': team_members_count, 'get_all_requests_count': get_all_requests_count, }

    return render(request, 'manager/manager_user_profile.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def manager_edit_user_profile(request):
    return render(request, 'manager/edit_manager_profile.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def manager_update_user_profile(request, userid):
    update_manager = Account.objects.get(id=userid)
    get_account = AccountProfile.objects.filter(user=userid).count()

    if get_account == 0:    
        if request.method == 'POST':
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            contact_number = request.POST['contact_number']
            home_address = request.POST['home_address']
            profile_image = request.FILES['profile_image']
            update_manager.first_name = first_name
            update_manager.last_name = last_name
            update_manager.email = email
            new_account_profile = AccountProfile(user=Account.objects.get(id=userid), home_address=home_address, contact_number=contact_number, profile_image=profile_image)
            update_manager.save()
            new_account_profile.save()
            message_alert.success(request, 'Your account details was updated successfully!')
    elif get_account == 1:
        update_account = AccountProfile.objects.get(user=userid)
        if request.method == 'POST':
            if len(request.FILES) != 0:
                if len(update_account.profile_image) > 0:
                    os.remove(update_account.profile_image.path)
                update_account.profile_image = request.FILES['profile_image']
            update_manager.first_name = request.POST['first_name']
            update_manager.last_name = request.POST['last_name']
            update_manager.email = request.POST['email']
            update_account.contact_number = request.POST['contact_number']
            update_account.home_address = request.POST['home_address']
            update_account.save()
            update_manager.save()
            message_alert.success(request, 'Your account details was updated successfully!')
    
    return redirect(manager_user_profile, userid)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def superadmin_user_profile(request):
    return render(request, 'superadmin/superadmin_user_profile.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def superadmin_edit_user_profile(request):
    return render(request, 'superadmin/edit_superadmin_profile.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def superadmin_add_user_profile(request, userid):
    update_superadmin = Account.objects.get(id=userid)
    
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        contact_number = request.POST['contact_number']
        home_address = request.POST['home_address']
        profile_image = request.FILES['profile_image']
        update_superadmin.first_name = first_name
        update_superadmin.last_name = last_name
        update_superadmin.email = email
        update_superadmin.save()
        new_account_profile = AccountProfile(user=Account.objects.get(id=userid), home_address=home_address, contact_number=contact_number, profile_image=profile_image)
        new_account_profile.save()
        message_alert.success(request, 'Your account details was updated successfully!')
        
    return render(request, 'superadmin/edit_superadmin_profile.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def superadmin_update_user_profile(request, userid):
    update_superadmin = Account.objects.get(id=userid)
    get_account = AccountProfile.objects.filter(user=userid).count()

    if get_account == 0:    
        if request.method == 'POST':
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            contact_number = request.POST['contact_number']
            home_address = request.POST['home_address']
            profile_image = request.FILES['profile_image']
            update_superadmin.first_name = first_name
            update_superadmin.last_name = last_name
            update_superadmin.email = email
            new_account_profile = AccountProfile(user=Account.objects.get(id=userid), home_address=home_address, contact_number=contact_number, profile_image=profile_image)
            update_superadmin.save()
            new_account_profile.save()
            message_alert.success(request, 'Your account details was updated successfully!')
    elif get_account == 1:
        update_account = AccountProfile.objects.get(user=userid)
        if request.method == 'POST':
            if len(request.FILES) != 0:
                if len(update_account.profile_image) > 0:
                    os.remove(update_account.profile_image.path)
                update_account.profile_image = request.FILES['profile_image']
            update_superadmin.first_name = request.POST['first_name']
            update_superadmin.last_name = request.POST['last_name']
            update_superadmin.email = request.POST['email']
            update_account.contact_number = request.POST['contact_number']
            update_account.home_address = request.POST['home_address']
            update_account.save()
            update_superadmin.save()
            message_alert.success(request, 'Your account details was updated successfully!')

    return redirect(superadmin_user_profile)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def it_admin_user_profile(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    completed_requests = Requests.objects.all().filter(assigned_to=get_user_psid, request_status='Completed', is_active=True)
    completed_requests_count = completed_requests.count()
    get_resources = Resource.objects.filter(is_active=True)
    count_resources = get_resources.count()

    context = { 'completed_requests_count': completed_requests_count, 'count_resources': count_resources, }

    return render(request, 'it_admin/it_admin_user_profile.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def it_admin_edit_user_profile(request):
    return render(request, 'it_admin/edit_it_admin_profile.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def it_admin_update_user_profile(request, userid):
    update_it_admin = Account.objects.get(id=userid)
    get_account = AccountProfile.objects.filter(user=userid).count()

    if get_account == 0:    
        if request.method == 'POST':
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            contact_number = request.POST['contact_number']
            home_address = request.POST['home_address']
            profile_image = request.FILES['profile_image']
            update_it_admin.first_name = first_name
            update_it_admin.last_name = last_name
            update_it_admin.email = email
            new_account_profile = AccountProfile(user=Account.objects.get(id=userid), home_address=home_address, contact_number=contact_number, profile_image=profile_image)
            update_it_admin.save()
            new_account_profile.save()
            message_alert.success(request, 'Your account details was updated successfully!')
    elif get_account == 1:
        update_account = AccountProfile.objects.get(user=userid)
        if request.method == 'POST':
            if len(request.FILES) != 0:
                if len(update_account.profile_image) > 0:
                    os.remove(update_account.profile_image.path)
                update_account.profile_image = request.FILES['profile_image']
            update_it_admin.first_name = request.POST['first_name']
            update_it_admin.last_name = request.POST['last_name']
            update_it_admin.email = request.POST['email']
            update_account.contact_number = request.POST['contact_number']
            update_account.home_address = request.POST['home_address']
            update_account.save()
            update_it_admin.save()
            message_alert.success(request, 'Your account details was updated successfully!')
    
    return redirect(it_admin_user_profile, userid)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def superadmin_add_user(request):

    users = Account.objects.all()
    department_names = Department.objects.all().filter(is_active=True)
    team_names = Team.objects.all().filter(is_active=True)

    context = {
        'users': users,
        'department_names': department_names,
        'team_names': team_names,
    }

    return render(request, 'superadmin/display_user_page.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode() #decoding the URL token verification
        user = Account._default_manager.get(pk=uid) #getting the user account by primary key
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist): #checking the user exists or not and raise an error if user ! in db.
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True #setting the user status into active status
        user.save()
        message_alert.success(request, 'Welcome!, now you can login here.')
        return redirect('login')
    else:
        message_alert.error(request, 'OOPS!, it seems invalid link.')
        return redirect('login')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def view_user_details(request, uid):
    get_user = Account.objects.get(id=uid)
    context = { 'get_user': get_user, }
    return render(request, 'superadmin/view_user_details.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def edit_user(request, uid):
    selected_user = Account.objects.get(id=uid)
    team_names = Team.objects.filter(is_active=True)
    department_names = Department.objects.filter(is_active=True)
    context = { 'selected_user': selected_user, 'team_names': team_names, 'department_names': department_names, }
    return render(request, 'superadmin/add_user_form.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def update_user(request, uid):
    update_user = Account.objects.get(id=uid)
    update_user.peoplesoft_id = request.POST['peoplesoft_id']
    update_user.first_name = request.POST['first_name']
    update_user.last_name = request.POST['last_name']
    update_user.email = request.POST['email']
    get_department = request.POST['department']
    update_user.department = Department.objects.get(id=get_department)
    update_user.role = request.POST['role']
    get_team = request.POST['team']
    if get_team == '':
        message_alert.info(request, 'Please choose the team for relative department!')
        return redirect(edit_user, uid)
    else:
        update_user.team = Team.objects.get(id=get_team)
        if update_user.role == 'Superadmin':
            update_user.is_superadmin = True
            update_user.is_staff = True
            update_user.is_manager = False
            update_user.is_it_admin = False
            update_user.save()
            message_alert.success(request, 'User is updated successfully!')
        elif update_user.role == 'Manager':
            update_user.is_it_admin = False
            update_user.is_superadmin = False
            update_user.is_staff = False
            update_user.is_manager = True
            update_user.save()
            message_alert.success(request, 'User is updated successfully!')
        elif update_user.role == 'IT Administrator':
            update_user.is_superadmin = False
            update_user.is_staff = False
            update_user.is_manager = False
            update_user.is_it_admin = True
            update_user.save()
            message_alert.success(request, 'User is updated successfully!')

    return redirect(superadmin_add_user)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def superadmin_users_date_sort(request):
    if request.method == 'POST':
        from_date = request.POST['from_user']
        to_date = request.POST['to_user']
        get_result =  Account.objects.filter(date_joined__gte=from_date, date_joined__lte=to_date)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'superadmin/display_user_page.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def users_deletion_history(request):
    users = Account.objects.all().filter(is_active=False)
    context = { 'users': users, }
    return render(request, 'superadmin/user_deletion_history.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def remove_user_access(request, uid):
    remove_user = Account.objects.get(id=uid)
    remove_user.is_active = False
    remove_user.save()
    message_alert.success(request, 'User access removed successfully!')
    return redirect(superadmin_add_user)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def restore_user(request, uid):
    restoring_user = Account.objects.get(id=uid)
    restoring_user.is_active = True
    restoring_user.save()
    message_alert.success(request, 'User access revoked successfully!')
    return redirect(users_deletion_history)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def permanent_delete_user(request, uid):
    if request.method == 'POST':
        delete_name = request.POST['delete_name']
        if delete_name == 'delete':
            user_delete = Account.objects.get(id=uid)
            user_delete.delete()
            message_alert.success(request, 'User permanently deleted successfully!')
    return redirect(superadmin_add_user)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def logout(request):
    auth.logout(request)
    message_alert.success(request, 'User logged out successfully!')
    return redirect('login')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            current_site = get_current_site(request)
            mail_head_subject = 'ORMS Reset Password Link'
            message = render_to_string('account/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_head_subject, message, to=[to_email])
            send_email.send()
            message_alert.success(request, 'Reset password link has been sent to your email successfully!')
            return redirect(login)
        else:
            message_alert.error(request, 'Your email is not exists, please check!')
            return redirect(forgot_password)
    return render(request, 'account/forgot_password.html')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode() #decoding the URL token verification
        user = Account._default_manager.get(pk=uid) #getting the user account by primary key
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist): #checking the user exists or not and raise an error if user ! in db.
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        message_alert.info(request, 'Please reset your password!')
        return redirect(reset_password_activity)
    else:
        message_alert.error(request, 'Seems that the link is expired!')
        return redirect(login)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def reset_password_activity(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            message_alert.success(request, 'Your password reset done sucsessfully!')
            return redirect(login)
        else:
            message_alert.error(request, 'Passwords does not match, please check!')
            return redirect(reset_password_activity)
    else:
        return render(request, 'account/reset_password_page.html')
    
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def load_teams(request):
    department_id = request.GET.get('department')
    teams = Team.objects.filter(department_id=department_id).order_by('team_name')
    context = { 'teams': teams, }
    return render(request, 'superadmin/teams_dropdownlist_options.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def manager_change_password(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    user = Account.objects.get(peoplesoft_id__exact=get_user_psid)
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                message_alert.success(request, 'Your account password was changed successfully!')
                return redirect(manager_user_profile, userid)
            else:
                message_alert.error(request, 'Please enter the current password correctly!')
                return redirect(manager_user_profile, userid)
        else:
            message_alert.error(request, 'Confirm password does not matches!')
            return redirect(manager_user_profile, userid)
    return redirect(manager_user_profile, userid)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def it_admin_change_password(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    user = Account.objects.get(peoplesoft_id__exact=get_user_psid)
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                message_alert.success(request, 'Your account password was changed successfully!')
                return redirect(it_admin_user_profile, userid)
            else:
                message_alert.error(request, 'Please enter the current password correctly!')
                return redirect(it_admin_user_profile, userid)
        else:
            message_alert.error(request, 'Confirm password does not matches!')
            return redirect(it_admin_user_profile, userid)
    return redirect(it_admin_user_profile, userid)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def superadmin_change_password(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    user = Account.objects.get(peoplesoft_id__exact=get_user_psid)
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                message_alert.success(request, 'Your account password was changed successfully!')
                return redirect(superadmin_user_profile)
            else:
                message_alert.error(request, 'Please enter the current password correctly!')
                return redirect(superadmin_user_profile)
        else:
            message_alert.error(request, 'Confirm password does not matches!')
            return redirect(superadmin_user_profile)
    return redirect(superadmin_user_profile)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                

        