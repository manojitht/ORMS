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
        elif department == '--Choose department--':
            message_alert.info(request, 'Please choose a department to create a team!')
        else:
            team = Team(team_name=team_name, team_head=team_head, 
            department=Department.objects.get(department_name=department), 
            team_description=team_description, created_by=created_by)
            team.save()
            message_alert.success(request, team_name + ' is created successfully!')
            return redirect(superadmin_team_table)
    else:
        pass
    return render(request, 'superadmin/add_team_form.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def display_team(request, temid):
    selected_tem = Team.objects.get(id=temid)
    context = { 'selected_tem': selected_tem, }
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
    return redirect(display_team, temid)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_team(request, temid):
    if request.method == 'POST':
        delete_name = request.POST['delete_name']
        if delete_name == 'delete':
            deleting_tem = Team.objects.get(id=temid)
            deleting_tem.delete()
            message_alert.success(request, deleting_tem.team_name + ' Team deleted successfully!')
    return redirect(superadmin_team_table)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# def restore_team(request, temid):
#     restoring_tem = Team.objects.get(id=temid)
#     restoring_tem.is_active = True
#     restoring_tem.save()
#     message_alert.success(request, 'Team restored successfully!')
#     return redirect(team_deletion_history)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# def permanent_delete_team(request, temid):
#     restoring_tem = Team.objects.get(id=temid)
#     restoring_tem.delete()
#     message_alert.success(request, 'Team deleted successfully!')
#     return redirect(team_deletion_history)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def superadmin_team_table(request):
    teams_table = Team.objects.all().order_by('team_name')
    context = { 'teams_table': teams_table, }
    return render(request, 'superadmin/team_table_view.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def superadmin_team_date_sort(request):
    if request.method == 'POST':
        from_date = request.POST['from_tem']
        to_date = request.POST['to_tem']
        get_result =  Team.objects.filter(created_date__gte=from_date, created_date__lte=to_date)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'superadmin/team_table_view.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def team_deletion_history(request):
    teams = Team.objects.all().filter(is_active=False)
    context = { 'teams': teams, }
    return render(request, 'superadmin/team_deletion_history.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
