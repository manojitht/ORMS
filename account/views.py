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
import random
import string

#sending mail library
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


# Create your views here.
# def register_superadmin(request):
#     # if request.method == 'POST':

#     #     #Get fromt form values (registration superadmin)
#     #     peoplesoft_id = request.POST['peoplesoft_id']
#     #     firstname = request.POST['firstname']
#     #     lastname = request.POST['lastname']
#     #     email = request.POST['email']
#     #     password = request.POST['password1']
#     #     confirm_password = request.POST['password2']

#     #     if password == confirm_password:
       
#     # return render(request, 'account/register_superadmin.html')
#     pass

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

def superadmin_portal(request):
    return render(request, 'superadmin/superadmin_home.html')
    #return render(request, 'it_admin/manage_devices.html')

    # return render(request, 'account/login.html')

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
                    user  = Account.objects.create_superuser(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=department, team=team, role=role, password='password@123')
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
                        password_generated = 'password@123'
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
                    user  = Account.objects.create_manager(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=department, team=team, role=role, password='password@123')
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
                    user  = Account.objects.create_IT_admin(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=department, team=team, role=role, password='password@123')
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
                        message_alert.success(request, 'IT Administrator user created successfully!')
                    except: 
                        message_alert.info(request, 'Something went wrong!')
                        user.delete()
                    return redirect('add_user_page')
                    #return render(request, 'superadmin/add_user_page.html')
    else:
        pass
    return render(request, 'superadmin/add_user_form.html', context)


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
        
def it_admin_portal(request):
    return render(request, 'it_admin/manage_devices.html')

def manager_portal(request):
    return render(request, 'manager/home.html')

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

@login_required(login_url= 'login')
def logout(request):
    auth.logout(request)
    message_alert.success(request, 'User logged out successfully!')
    return redirect('login')
