from email import message
from django.shortcuts import redirect, render
from .forms import LoginUsers
from django.contrib.auth import authenticate, login as permit_user
from .models import Account
import random
import string


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
                message = 'Invalid credentials please check!'
        else:
            message = 'Error validating form'
    return render(request, 'account/login.html', {'form': form, 'message': message})

def superadmin_portal(request):
    return render(request, 'superadmin/superadmin_home.html')
    #return render(request, 'it_admin/manage_devices.html')

    # return render(request, 'account/login.html')

def superadmin_add_user(request):
    # generated_pass = {
    #     'password': 'password@123',
    # }
    # message = None
    # if request.method == 'POST':
    #     form = CreateSystemUsers(request.POST)
    #     if form.is_valid():
    #         user = form.save()
    #         message = 'User created successfully!'
    #     else:
    #         message = 'Sorry! something is error occurred'
    # else:
    #     form = CreateSystemUsers()
    # form = CreateSystemUsers(initial=generated_pass)
    # return render(request, 'superadmin/superadmin_add_user.html', {'form': form, 'message': message})

    # #return render(request, 'superadmin/superadmin_add_user.html')
    if request.method == 'POST':
        peoplesoft_id = request.POST['peoplesoft_id']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        department = request.POST['department']
        team = request.POST['team']
        role = request.POST['role']
        #password = request.POST['password']

        if role == 'Superadmin':
            user  = Account.objects.create_superuser(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=department, team=team, role=role, password='password@123')
            user.save();
            return render(request, 'superadmin/superadmin_add_user.html')
        elif role == 'Manager':
            user  = Account.objects.create_manager(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=department, team=team, role=role, password='password@123')
            user.save();
            return render(request, 'superadmin/superadmin_add_user.html')
        elif role == 'IT Administrator':
            user  = Account.objects.create_IT_admin(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=department, team=team, role=role, password='password@123')
            user.save();
            return render(request, 'superadmin/superadmin_add_user.html')

        #user  = Account.objects.create_user(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=department, team=team, role=role, password='password@123')
        #user  = Account.objects.create_user(peoplesoft_id=peoplesoft_id, first_name=first_name, last_name=last_name, email=email, department=department, team=team, role=role, password='password@123')
        
    else:
        return render(request, 'superadmin/superadmin_add_user.html')




def it_admin_portal(request):
    return render(request, 'it_admin/manage_devices.html')

def manager_portal(request):
    return render(request, 'manager/home.html')

def logout(request):
    return
