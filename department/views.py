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

def display_departments(request):
    departments = Department.objects.all().filter(is_active=True).order_by('department_name')
    context = { 'departments': departments, }
    return render(request, 'superadmin/display_department_page.html', context)
    # naming convention finished.

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
            message_alert.success(request, department_name + ' is created successfully!')
            department.save()
    else:
        pass
    return render(request, 'superadmin/add_department_form.html')
    # naming convention finished.

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_department(request, depid):
    deleting_dep = Department.objects.get(id=depid)
    #deleting_dep.delete()
    deleting_dep.is_active = False
    deleting_dep.save()
    message_alert.success(request, 'Department deleted successfully!')
    return redirect(display_departments)
    # naming convention finished.

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
    return redirect(display_departments)
    # naming convention finished.

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def search_department(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            search_department = Department.objects.order_by('-created_on').filter(Q(department_name__icontains=keyword) | Q(department_head__icontains=keyword) | Q(department_description__icontains=keyword) | Q(created_by__icontains=keyword))
    context = { 'search_department': search_department, }
    return render(request, 'superadmin/display_department_page.html', context)
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
        #from_date = request.POST.get('from_date')
        #from_date = request.POST.get('to_date')
        #get_result = Department.objects.raw('select id,department_name,department_head,department_description,created_by,created_on from departments where created_on between "'+from_date+'" and "'+to_date+'"')
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