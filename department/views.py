from ast import keyword
from django.db.models import Q
from django.shortcuts import render
from django.contrib import messages as message_alert
from django.shortcuts import redirect, render
from .models import Department
from team.models import Team

def notes_page(request):
    return render(request, 'superadmin/notes_page.html')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def display_departments(request, depid):
    selected_dep = Department.objects.get(id=depid)
    context = { 'selected_dep': selected_dep, }
    return render(request, 'superadmin/display_department_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def add_new_department(request):
    if request.method == 'POST':
        department_name = request.POST['department_name']
        department_head = request.POST['department_head']
        department_description = request.POST['department_description']
        created_by = request.POST['created_by']
        if Department.objects.filter(department_name=department_name).exists():
            message_alert.info(request, 'Department is already exists!')
        else:
            department = Department(department_name=department_name, department_head=department_head, department_description=department_description, created_by=created_by)
            department.save()
            message_alert.success(request, department_name + ' is created successfully!')
            return redirect(superadmin_department_table)
    else:
        pass
    return render(request, 'superadmin/add_department_form.html')
    # naming convention finished.

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_department(request, depid):
    if request.method == 'POST':
        delete_name = request.POST['delete_name']
        if delete_name == 'delete':
            dep_delete = Department.objects.get(id=depid)
            dep_delete.delete()
            message_alert.success(request, dep_delete.department_name + ' Department deleted successfully!')
    return redirect(superadmin_department_table)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def edit_department(request, depid):
    selected_dep = Department.objects.get(id=depid)
    dep_list = Department.objects.all()
    context = { 'selected_dep': selected_dep, 'dep_list': dep_list, }
    return render(request, 'superadmin/add_department_form.html', context)
    # naming convention finished.

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_department(request, depid):
    update_dep = Department.objects.get(id=depid)
    update_dep.department_name = request.POST['department_name']
    update_dep.department_head = request.POST['department_head']
    update_dep.department_description = request.POST['department_description']
    update_dep.created_by = request.POST['created_by']
    update_dep.save()
    message_alert.success(request, 'Department is updated successfully!')
    return redirect(display_departments, depid)
    # naming convention finished.

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def superadmin_department_table(request):
    departments_table = Department.objects.all().order_by('department_name')
    context = { 'departments_table': departments_table, }
    return render(request, 'superadmin/department_table_view.html', context)
    # naming convention finished.

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def superadmin_department_date_sort(request):
    if request.method == 'POST':
        from_date = request.POST['from_dep']
        to_date = request.POST['to_dep']
        if from_date != '' and to_date != '':
            get_result =  Department.objects.filter(created_on__gte=from_date, created_on__lte=to_date)
        else:
            message_alert.info(request, 'Please select the date fields properly!')
    context = { 'get_result': get_result, }
    return render(request, 'superadmin/department_table_view.html', context)
    # naming convention finished.

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def department_view_teams(request, depid):
    get_department = Department.objects.get(id=depid)
    name = Department.objects.get(department_name=get_department.department_name)
    # department_name = depname.replace('-', ' ')
    # corrected_name = department_name.title()
    department_view_teams = Team.objects.all().filter(department=name, is_active=True)
    team_count = department_view_teams.count()
    context = { 'department_view_teams': department_view_teams, 'name': name, 'team_count': team_count, }
    return render(request, 'superadmin/display_team_page.html', context)
    # naming convention finished.

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def department_deletion_history(request):
    departments = Department.objects.all().filter(is_active=False)
    context = { 'departments': departments, }
    return render(request, 'superadmin/department_deletion_history.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
