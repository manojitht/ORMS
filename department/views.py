from django.shortcuts import render
from django.contrib import messages as message_alert
from django.shortcuts import redirect, render
from .models import Department


def superadmin_add_department(request):

    departments = Department.objects.all().filter(is_active=True)

    context = {
        'departments': departments
    }

    if request.method == 'POST':
        cost_code = request.POST['cost_code']
        department_name = request.POST['department_name']
        department_head = request.POST['department_head']
        created_by = request.POST['created_by']

        if Department.objects.filter(cost_code=cost_code).exists():
            message_alert.info(request, cost_code + ', is already exists!')
        else:
            if Department.objects.filter(department_name=department_name).exists():
                message_alert.info(request, 'Department is already exists!')
            else:
                department = Department(cost_code=cost_code, department_name=department_name, department_head=department_head, created_by=created_by)
                message_alert.success(request, department_name + ' is created successfully!')
                department.save()
    else:
        pass
    return render(request, 'superadmin/superadmin_add_department.html', context)


def delete_department(request, depid):
    deleting_dep = Department.objects.get(id=depid)
    deleting_dep.delete()
    message_alert.success(request, 'Department deleted successfully!')
    return redirect(superadmin_add_department)


def edit_department(request, depid):
    selected_dep = Department.objects.get(id=depid)
    dep_list = Department.objects.all()
    context = {
        'selected_dep': selected_dep,
        'dep_list': dep_list,
    }
    return render(request, 'superadmin/superadmin_add_department.html', context)
