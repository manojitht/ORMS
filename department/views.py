from django.shortcuts import render
from django.contrib import messages as message_alert
from django.shortcuts import redirect, render
from .models import Department


def superadmin_list_department(request):

    # departments = Department.objects.all().filter(is_active=True)
    departments = Department.objects.all().order_by('department_name')

    context = {
        'departments': departments
    }

    return render(request, 'superadmin/superadmin_add_department.html', context)

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
    return render(request, 'superadmin/add_department_page.html')


def delete_department(request, depid):
    deleting_dep = Department.objects.get(id=depid)
    deleting_dep.delete()
    message_alert.success(request, 'Department deleted successfully!')
    return redirect(superadmin_list_department)


def edit_department(request, depid):
    selected_dep = Department.objects.get(id=depid)
    dep_list = Department.objects.all()
    context = {
        'selected_dep': selected_dep,
        'dep_list': dep_list,
    }
    return render(request, 'superadmin/add_department_page.html', context)

def update_department(request, depid):
    update_dep = Department.objects.get(id=depid)
    update_dep.department_name = request.POST['department_name']
    update_dep.department_head = request.POST['department_head']
    update_dep.department_description = request.POST['department_description']
    update_dep.created_by = request.POST['created_by']
    update_dep.save()
    message_alert.success(request, 'Department is updated successfully!')
    return redirect(superadmin_list_department)

