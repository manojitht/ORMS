from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages as message_alert
from django.shortcuts import redirect, render
from .models import Team
from department.models import Department
from department.views import display_departments
from django.db.models import Q
from django.shortcuts import redirect

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def superadmin_add_team(request):
    teams = Team.objects.all().filter(is_active=True)
    department_names = Department.objects.all().filter(is_active=True)
    context = { 'teams': teams, 'department_names': department_names, }
    
    if request.method == 'POST':
        team_name = request.POST['team_name']
        team_head = request.POST['team_head']
        department = request.POST['department']
        team_description = request.POST['team_description']
        created_by = request.POST['created_by']

        if Team.objects.filter(team_name=team_name).exists():
            message_alert.info(request, team_name + ', is already exists!')
        elif department == '--Choose department oriented with--':
            message_alert.info(request, 'Please choose a department to create a team!')
        else:
            team = Team(team_name=team_name, team_head=team_head, department=Department.objects.get(department_name=department), team_description=team_description, created_by=created_by)
            message_alert.success(request, team_name + ' is created successfully!')
            team.save()
    else:
        pass
    return render(request, 'superadmin/add_team_form.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def superadmin_list_team(request):
    teams = Team.objects.all().filter(is_active=True)
    department_names = Department.objects.all().filter(is_active=True)

    context = { 'teams': teams, 'department_names': department_names, }
    return render(request, 'superadmin/display_team_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def edit_team(request, temid):
    selected_tem = Team.objects.get(id=temid)
    tem_list = Team.objects.all()
    dep_list = Department.objects.all()
    context = { 'selected_tem': selected_tem, 'tem_list': tem_list, 'dep_list': dep_list, }
    return render(request, 'superadmin/add_team_form.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_team(request, temid):
    update_tem = Team.objects.get(id=temid)
    update_tem.team_name = request.POST['team_name']
    update_tem.team_head = request.POST['team_head']
    take_dep = request.POST['department']
    update_tem.department = Department.objects.get(department_name=take_dep)
    update_tem.team_description = request.POST['team_description']
    update_tem.created_by = request.POST['created_by']
    update_tem.save()
    message_alert.success(request, 'Team is updated on the ' + take_dep + ' department successfully!')
    return redirect(display_departments)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_team(request, temid):
    deleting_tem = Team.objects.get(id=temid)
    deleting_tem.is_active = False
    deleting_tem.save()
    message_alert.success(request, 'Team deleted successfully!')
    return redirect(display_departments)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def superadmin_team_table(request):
    teams_table = Team.objects.all().order_by('team_name')
    context = { 'teams_table': teams_table, }
    return render(request, 'superadmin/team_table_view.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
