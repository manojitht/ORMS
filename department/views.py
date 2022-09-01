from django.shortcuts import render
from django.contrib import messages as message_alert
from django.shortcuts import redirect, render
from .models import Department


def superadmin_add_department(request):
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
                message_alert.success(request, 'Department is created successfully!')
                department.save()
    else:
        pass
    return render(request, 'superadmin/superadmin_add_department.html')
