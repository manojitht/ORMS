# from email import message as message_alert
from base64 import urlsafe_b64decode
from email.message import EmailMessage
from genericpath import exists
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .forms import LoginUsers
from django.contrib.auth import authenticate, login as permit_user
from .models import Account
from django.contrib import messages as message_alert, auth
from django.contrib.auth.decorators import login_required
from department.models import Department
from team.models import Team

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
                return redirect('it_admin_portal')
            elif user is not None and user.is_manager:
                permit_user(request, user)
                return redirect('manager_portal')
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

def superadmin_portal(request):
    return render(request, 'superadmin/superadmin_home.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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

        
        #password = request.POST['password']
        if Account.objects.filter(peoplesoft_id=peoplesoft_id).exists():
            message_alert.info(request, peoplesoft_id + ', is already exists as an user!')
            #print(peoplesoft_id + ', is already exists as an user!')
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
                    user  = Account.objects.create_superuser(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=Department.objects.get(department_name=department), team=Team.objects.get(team_name=team), role=role, ini_pas=password_generated, password=password_generated)
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
                        user.save();
                        message_alert.success(request, 'Superadmin user created successfully!')
                    except: 
                        message_alert.info(request, 'Something went wrong!')
                        user.delete()
        
                    return redirect('add_user_page')
                    #return render(request, 'superadmin/add_user_page.html')
                elif role == 'Manager':
                    user  = Account.objects.create_manager(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=Department.objects.get(department_name=department), team=Team.objects.get(team_name=team), role=role, ini_pas=password_generated, password=password_generated)
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
                        password_generated = 'password@123'
                        send_email = EmailMessage(mail_head_subject, message, to=[to_email])
                        send_email.send()
                        user.save();
                        message_alert.success(request, 'Manager user created successfully!')
                    except: 
                        message_alert.info(request, 'Something went wrong!')
                        user.delete()

                    return redirect('add_user_page')
                    #return render(request, 'superadmin/add_user_page.html')
                elif role == 'IT Administrator':
                    user  = Account.objects.create_IT_admin(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=Department.objects.get(department_name=department), team=Team.objects.get(team_name=team), role=role, ini_pas=password_generated, password=password_generated)
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
                        user.save();
                        message_alert.success(request, 'IT Administrator user created successfully!')
                    except: 
                        message_alert.info(request, 'Something went wrong!')
                        user.delete()
                    return redirect('add_user_page')
                    #return render(request, 'superadmin/add_user_page.html')
    else:
        pass
    return render(request, 'superadmin/add_user_form.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
        
def it_admin_portal(request):
    return render(request, 'it_admin/it_administrator_dashboard.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def manager_portal(request):
    return render(request, 'manager/home.html')

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

def edit_user(request, uid):
    selected_user = Account.objects.get(id=uid)
    team_names = Team.objects.filter(is_active=True)
    department_names = Department.objects.filter(is_active=True)
    context = { 'selected_user': selected_user, 'team_names': team_names, 'department_names': department_names, }
    return render(request, 'superadmin/add_user_form.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_user(request, uid):
    update_user = Account.objects.get(id=uid)
    update_user.peoplesoft_id = request.POST['peoplesoft_id']
    update_user.first_name = request.POST['first_name']
    update_user.last_name = request.POST['last_name']
    update_user.email = request.POST['email']
    get_department = request.POST['department']
    update_user.department = Department.objects.get(department_name=get_department)
    get_team = request.POST['team']
    update_user.team = Team.objects.get(team_name=get_team)
    update_user.role = request.POST['role']

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

def superadmin_users_date_sort(request):
    if request.method == 'POST':
        from_date = request.POST['from_user']
        to_date = request.POST['to_user']
        get_result =  Account.objects.filter(date_joined__gte=from_date, date_joined__lte=to_date)
    context = { 'get_result': get_result, }
    return render(request, 'superadmin/display_user_page.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def users_deletion_history(request):
    users = Account.objects.all().filter(is_active=False)
    context = { 'users': users, }
    return render(request, 'superadmin/user_deletion_history.html', context)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def remove_user_access(request, uid):
    remove_user = Account.objects.get(id=uid)
    remove_user.is_active = False
    remove_user.save()
    message_alert.success(request, 'User access removed successfully!')
    return redirect(superadmin_add_user)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def restore_user(request, uid):
    restoring_user = Account.objects.get(id=uid)
    restoring_user.is_active = True
    restoring_user.save()
    message_alert.success(request, 'User access revoked successfully!')
    return redirect(users_deletion_history)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def permanent_delete_user(request, uid):
    delete_user = Account.objects.get(id=uid)
    delete_user.delete()
    message_alert.success(request, 'User permanently deleted successfully!')
    return redirect(users_deletion_history)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url= 'login')
def logout(request):
    auth.logout(request)
    message_alert.success(request, 'User logged out successfully!')
    return redirect('login')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------