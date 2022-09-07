from django.shortcuts import render
from django.contrib import messages as message_alert
from django.shortcuts import redirect, render
from .models import Team
from department.models import Department
#from .forms import TeamForm


def superadmin_add_team(request):
    teams = Team.objects.all().filter(is_active=True)
    department_names = Department.objects.all().filter(is_active=True)

    context = {
        'teams': teams,
        'department_names': department_names,
    }

    if request.method == 'POST':
        team_name = request.POST['team_name']
        team_head = request.POST['team_head']
        department = request.POST['department']
        created_by = request.POST['created_by']

        if Team.objects.filter(team_name=team_name).exists():
            message_alert.info(request, team_name + ', is already exists!')
        elif department == '--Choose department oriented with--':
            message_alert.info(request, 'Please choose a department to create a team!')
        else:
            team = Team(team_name=team_name, team_head=team_head, department=Department.objects.get(department_name=department), created_by=created_by)
            message_alert.success(request, team_name + ' is created successfully!')
            team.save()
    else:
        pass
    return render(request, 'superadmin/superadmin_add_team.html', context)