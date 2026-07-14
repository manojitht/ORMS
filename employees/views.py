from django.shortcuts import render
from django.contrib import messages as message_alert
from django.shortcuts import redirect
from django.db.models import Q
from employees.models import Employee
from resources.models import Resource, ResourceTaken, OtherAccessories
from department.models import Department
from account.models import Account
from team.models import Team
from datetime import date
import os
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from arivom.csv_utils import csv_response
from arivom.account_provisioning import generate_temporary_password, send_account_creation_email
from notifications.services import notify
from activity.services import log_activity


def _provision_employee_account(request, employee):
    """Create a self-service login for `employee`, linked via
    Account.employee_profile. Mirrors add_user_page's collision-check
    pattern -- Account.peoplesoft_id is globally unique while
    Employee.peoplesoft_id is only unique per company, so two different
    companies' employees can collide on id; when that happens we surface a
    clear message and skip provisioning rather than erroring.
    """
    if Account.objects.filter(peoplesoft_id=employee.peoplesoft_id).exists():
        message_alert.info(request, f'{employee.peoplesoft_id} is already taken by another account -- could not grant portal access.')
        return False

    first_name, _, last_name = employee.fullname.partition(' ')
    password_generated = generate_temporary_password()
    user = Account.objects.create_employee(
        peoplesoft_id=employee.peoplesoft_id,
        first_name=first_name,
        last_name=last_name or first_name,
        email=employee.email,
        department=employee.department,
        team=employee.team,
        ini_pas=password_generated,
        password=password_generated,
        company=request.user.company,
        employee=employee,
    )
    if send_account_creation_email(request, user):
        message_alert.success(request, f'Portal access granted -- {employee.fullname} will get an activation email.')
        return True
    message_alert.error(request, 'Could not send the activation email -- portal access was not granted.')
    return False


@login_required(login_url='account:login')
def grant_portal_access(request, memid):
    employee = Employee.objects.get(id=memid)
    _provision_employee_account(request, employee)
    return redirect('employees:view_team_members_details', memid)


@login_required(login_url='account:login')
def add_member(request):

    if request.method == 'POST':
        peoplesoft_id = request.POST['peoplesoft_id']
        fullname = request.POST['fullname']
        position = request.POST['position']
        email = request.POST['email']
        contact = request.POST['contact']
        home_address = request.POST['home_address']
        manager_peoplesoft_id = request.POST['manager_peoplesoft_id']
        manager_name = request.POST['manager_name']
        department = request.POST['department']
        team = request.POST['team']
        member_image = request.FILES['member_image']
        should_grant_portal_access = 'grant_portal_access' in request.POST

        if Employee.objects.filter(peoplesoft_id=peoplesoft_id).exists():
            message_alert.info(request, peoplesoft_id + ', is already exists as team member profile!')
        elif Employee.objects.filter(email=email).exists():
            message_alert.info(request, email + ', is already exists in team member profile!')
        else:
            new_member = Employee(peoplesoft_id=peoplesoft_id, fullname=fullname, position=position,
            email=email, contact=contact, department=Department.objects.get(department_name=department),
            team=Team.objects.get(team_name=team), home_address=home_address,
            member_image=member_image, manager_name=manager_name, manager_peoplesoft_id=manager_peoplesoft_id)
            new_member.save()
            message_alert.success(request, peoplesoft_id + ' team member profile created successfully!')
            if should_grant_portal_access:
                _provision_employee_account(request, new_member)
            return redirect('employees:add_member')

    return render(request, 'manager/add_member_form.html')


@login_required(login_url='account:login')
def view_team_members(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    team_members = Employee.objects.all().filter(manager_peoplesoft_id=get_user_psid, is_active=True).order_by('peoplesoft_id')
    tm_count = team_members.count()
    context = { 'team_members': team_members, 'tm_count': tm_count, }
    return render(request, 'manager/view_team_member.html', context)


@login_required(login_url='account:login')
def export_team_members_csv(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    team_members = Employee.objects.filter(manager_peoplesoft_id=get_user_id, is_active=True).order_by('peoplesoft_id')
    rows = (
        (m.peoplesoft_id, m.fullname, m.position, m.email, m.contact, m.date_joined)
        for m in team_members
    )
    return csv_response('team_members.csv',
        ('PS Id', 'Fullname', 'Position', 'Email', 'Contact', 'Date Joined'), rows)


@login_required(login_url='account:login')
def view_team_members_details(request, memid):
    get_member_id = Employee.objects.get(id=memid)
    get_ps_id = Employee.objects.get(peoplesoft_id=get_member_id.peoplesoft_id)
    get_devices_id = ResourceTaken.objects.filter(peoplesoft_id=get_ps_id, resource_status='Taken')
    device_count = get_devices_id.count()
    try: 
        get_oa = OtherAccessories.objects.get(peoplesoft_id=get_ps_id)
    except:
        get_oa = OtherAccessories.objects.filter(peoplesoft_id=get_ps_id)
    
    context = { 'get_member_id': get_member_id, 'get_devices_id': get_devices_id, 'get_oa': get_oa, 'device_count': device_count, }
    return render(request, 'manager/view_team_member_details.html', context)


@login_required(login_url='account:login')
def search_team_member(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    keyword = request.GET.get('keyword', '')
    search_team_member = None
    search_count = 0
    if keyword:
        search_team_member = Employee.objects.filter(manager_peoplesoft_id=get_user_psid,
        is_active=True).filter(Q(peoplesoft_id__icontains=keyword) | Q(fullname__icontains=keyword))
        search_count = search_team_member.count()
    context = {
        'search_team_member': search_team_member,
        'keyword': keyword,
        'search_count': search_count,
        'team_members': None,
    }
    return render(request, 'manager/view_team_member.html', context)


@login_required(login_url='account:login')
def edit_team_member(request, memid):
    get_member_id = Employee.objects.get(id=memid)
    context = { 'get_member_id': get_member_id, }
    return render(request, 'manager/edit_team_member.html', context)


@login_required(login_url='account:login')
def update_team_member(request, memid):
    update_tm = Employee.objects.get(id=memid)

    if request.method == 'POST':
        if len(request.FILES) != 0:
            if len(update_tm.member_image) > 0:
                os.remove(update_tm.member_image.path)
            update_tm.member_image = request.FILES['member_image']
        update_tm.fullname = request.POST['fullname']
        update_tm.peoplesoft_id = request.POST['peoplesoft_id']
        update_tm.position = request.POST['position']
        update_tm.email = request.POST['email']
        update_tm.contact = request.POST['contact']
        update_tm.home_address = request.POST['home_address']
        update_tm.save()
        message_alert.success(request, 'Team member details of ' + update_tm.peoplesoft_id + ' was updated successfully!')
    return redirect('employees:view_team_members_details', memid)


@login_required(login_url='account:login')
def add_other_notes(request, memid):
    if request.method == 'POST':
        peoplesoft_id = request.POST['peoplesoft_id']
        other_notes = request.POST['other_notes']
        add_accessories = OtherAccessories(peoplesoft_id=Employee.objects.get(peoplesoft_id=peoplesoft_id), other_notes=other_notes)
        add_accessories.save()
        message_alert.success(request, 'Other notes added to ' + peoplesoft_id +' successfully!')
    return redirect('employees:view_team_members_details', memid)


@login_required(login_url='account:login')
def edit_other_notes(request, memid):
    get_oa_id = OtherAccessories.objects.get(id=memid)
    context = { 'get_oa_id': get_oa_id, }
    return render(request, 'manager/view_team_member_details.html', context)


@login_required(login_url='account:login')
def update_other_notes(request, memid, psid):
    update_oa = OtherAccessories.objects.get(id=memid)

    if request.method == 'POST':
        update_oa.other_notes = request.POST['other_notes']
        update_oa.save()
        message_alert.success(request, 'Other notes was updated successfully!')
    return redirect('employees:view_team_members_details', psid)


@login_required(login_url='account:login')
def mark_returned(request, resid, memid):
    get_asset = ResourceTaken.objects.get(id=resid)
    take_asset_id = ResourceTaken.objects.get(id=get_asset.id, asset_id=get_asset.asset_id)
    update_resource = Resource.objects.filter(asset_id=take_asset_id.asset_id)

    if request.method == 'POST':
        reason_notes = request.POST['return_reason']

        if reason_notes == 'Leaving From Company' or reason_notes == 'Swaping For Highend Resource':
            get_asset.resource_status = 'Returned'
            get_asset.returned_date = date.today()
            get_asset.reason_notes = reason_notes
            get_asset.save()
            for update in update_resource:
                update.resource_availability = 'Available'
                update.save()

                mail_head_subject = ' Resource Mark Returned Completed For ' + update.asset_id + ''
                return_email_context = {'get_asset': get_asset, 'asset_id': update.asset_id}
                text_body = render_to_string('account/resource_mark_return_email.html', return_email_context)
                html_body = render_to_string('account/emails/resource_mark_return_email.html', return_email_context)
                email = EmailMultiAlternatives(mail_head_subject, text_body, settings.EMAIL_HOST_USER, [get_asset.peoplesoft_id.email,])
                email.attach_alternative(html_body, 'text/html')
                email.send()

                employee_account = Account.objects.filter(
                    company=request.user.company, employee_profile=get_asset.peoplesoft_id).first()
                if employee_account:
                    notify(
                        employee_account, 'resource_returned',
                        title=f'{update.asset_id} marked returned',
                        body='Your device has been marked as returned.',
                        link_url=reverse(
                            'resources:employee_taken_resources_list_table', args=[employee_account.id]),
                        dedupe_key=f'resource_returned:{get_asset.id}',
                    )
                log_activity(
                    request.user, 'resource_returned',
                    f'{update.asset_id} returned by {get_asset.peoplesoft_id}',
                    related_resource=update,
                )

                message_alert.success(request, 'Mark returned on the device successfully!')

        elif reason_notes == 'Resource Damaged' or reason_notes == 'Facing Software Issue':
            get_asset.resource_status = 'Returned'
            get_asset.returned_date = date.today()
            get_asset.reason_notes = reason_notes
            get_asset.save()
            for update in update_resource:
                update.resource_availability = 'Configuration'
                update.save()

            mail_head_subject = ' Resource Mark Returned Completed For ' + update.asset_id + ''
            return_email_context = {'get_asset': get_asset, 'asset_id': update.asset_id}
            text_body = render_to_string('account/resource_mark_return_email.html', return_email_context)
            html_body = render_to_string('account/emails/resource_mark_return_email.html', return_email_context)
            email = EmailMultiAlternatives(mail_head_subject, text_body, settings.EMAIL_HOST_USER, [get_asset.peoplesoft_id.email,])
            email.attach_alternative(html_body, 'text/html')
            email.send()

            employee_account = Account.objects.filter(
                company=request.user.company, employee_profile=get_asset.peoplesoft_id).first()
            if employee_account:
                notify(
                    employee_account, 'resource_returned',
                    title=f'{update.asset_id} marked returned',
                    body='Your device has been marked as returned for repair/configuration.',
                    link_url=reverse(
                        'resources:employee_taken_resources_list_table', args=[employee_account.id]),
                    dedupe_key=f'resource_returned:{get_asset.id}',
                )
            log_activity(
                request.user, 'resource_returned',
                f'{update.asset_id} returned by {get_asset.peoplesoft_id} ({reason_notes})',
                related_resource=update,
            )

            message_alert.success(request, 'Mark returned on the device successfully!')

        elif reason_notes == '-------------':
            message_alert.info(request, 'Please choose a return reason to mark it as return!')
    
    return redirect('employees:view_team_members_details', memid)


@login_required(login_url='account:login')
def view_member_resource_info(request, memid, resid):
    get_member_id = Employee.objects.get(id=memid)
    get_devices_id = ResourceTaken.objects.get(id=resid)
    context = { 'get_devices_id': get_devices_id, 'get_member_id': get_member_id, }
    return render(request, 'manager/view_resource_info.html', context)


@login_required(login_url='account:login')
def view_history_resources(request, memid):
    get_member_id = Employee.objects.get(id=memid)
    get_ps_id = Employee.objects.get(peoplesoft_id=get_member_id.peoplesoft_id)
    get_devices_id = ResourceTaken.objects.filter(peoplesoft_id=get_ps_id, resource_status='Returned')
    context = { 'get_devices_id': get_devices_id, 'get_member_id': get_member_id, }
    return render(request, 'manager/view_history_devices.html', context)


@login_required(login_url='account:login')
def delete_team_member(request, memid, userid):
    deleting_mem = Employee.objects.get(id=memid)
    if request.method == 'POST':
        delete_name = request.POST['delete_name']
        if delete_name == 'delete':
            # Deactivate any linked self-service login before the delete --
            # employee_profile is SET_NULL, so the FK would just go blank on
            # its own, silently leaving an orphaned *active* account behind.
            linked_account = Account.objects.filter(employee_profile=deleting_mem).first()
            if linked_account:
                linked_account.is_active = False
                linked_account.save()
            message_alert.success(request, deleting_mem.fullname + ' was deleted successfully!')
            deleting_mem.delete()
    return redirect('employees:view_team_members', userid)


@login_required(login_url='account:login')
def view_team_members_index_table(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    team_members = Employee.objects.all().filter(manager_peoplesoft_id=get_user_psid, is_active=True).order_by('peoplesoft_id')
    context = { 'team_members': team_members, }
    return render(request, 'manager/member_index_table.html', context)


@login_required(login_url='account:login')
def date_sort_team_members_index_table(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    if request.method == 'POST':
        from_date = request.POST['from_mem']
        to_date = request.POST['to_mem']
        get_result =  Employee.objects.filter(date_joined__gte=from_date, date_joined__lte=to_date, manager_peoplesoft_id=get_user_psid, is_active=True).order_by('peoplesoft_id')
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, 'team_members': None, }
    return render(request, 'manager/member_index_table.html', context)
