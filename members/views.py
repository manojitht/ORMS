from django.shortcuts import render
from django.contrib import messages as message_alert, auth
from django.shortcuts import redirect, render
from django.db.models import Q
from members.models import Members
from resource.models import Resource, ResourceTaken, OtherAccessories
from department.models import Department
from account.models import Account
from team.models import Team
from datetime import date
import os
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

# Create your views here.

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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

        if Members.objects.filter(peoplesoft_id=peoplesoft_id).exists():
            message_alert.info(request, peoplesoft_id + ', is already exists as team member profile!')
        elif Members.objects.filter(email=email).exists():
            message_alert.info(request, email + ', is already exists in team member profile!')
        else:
            new_member = Members(peoplesoft_id=peoplesoft_id, fullname=fullname, position=position, 
            email=email, contact=contact, department=Department.objects.get(department_name=department),
            team=Team.objects.get(team_name=team), home_address=home_address, 
            member_image=member_image, manager_name=manager_name, manager_peoplesoft_id=manager_peoplesoft_id)
            new_member.save()
            message_alert.success(request, peoplesoft_id + ' team member profile created successfully!')
            return redirect('add_member')

    return render(request, 'manager/add_member_form.html')

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_team_members(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    team_members = Members.objects.all().filter(manager_peoplesoft_id=get_user_psid, is_active=True).order_by('peoplesoft_id')
    tm_count = team_members.count()
    context = { 'team_members': team_members, 'tm_count': tm_count, }
    return render(request, 'manager/view_team_member.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_team_members_details(request, memid):
    get_member_id = Members.objects.get(id=memid)
    get_ps_id = Members.objects.get(peoplesoft_id=get_member_id.peoplesoft_id)
    get_devices_id = ResourceTaken.objects.filter(peoplesoft_id=get_ps_id, resource_status='Taken')
    device_count = get_devices_id.count()
    try: 
        get_oa = OtherAccessories.objects.get(peoplesoft_id=get_ps_id)
    except:
        get_oa = OtherAccessories.objects.filter(peoplesoft_id=get_ps_id)
    
    context = { 'get_member_id': get_member_id, 'get_devices_id': get_devices_id, 'get_oa': get_oa, 'device_count': device_count, }
    return render(request, 'manager/view_team_member_details.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def search_team_member(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            search_team_member = Members.objects.filter(manager_peoplesoft_id=get_user_psid, 
            is_active=True).filter(Q(peoplesoft_id__icontains=keyword) | Q(fullname__icontains=keyword))
            search_count = search_team_member.count()
    context = { 'search_team_member': search_team_member, 'keyword': keyword, 'search_count': search_count, }
    return render(request, 'manager/view_team_member.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def manager_notes_page(request):
    return render(request, 'manager/manager_notes_page.html')

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def edit_team_member(request, memid):
    get_member_id = Members.objects.get(id=memid)
    context = { 'get_member_id': get_member_id, }
    return render(request, 'manager/edit_team_member.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_team_member(request, memid):
    update_tm = Members.objects.get(id=memid)

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
    return redirect(view_team_members_details, memid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def add_other_notes(request, memid):
    if request.method == 'POST':
        peoplesoft_id = request.POST['peoplesoft_id']
        other_notes = request.POST['other_notes']
        add_accessories = OtherAccessories(peoplesoft_id=Members.objects.get(peoplesoft_id=peoplesoft_id), other_notes=other_notes)
        add_accessories.save()
        message_alert.success(request, 'Other notes added to ' + peoplesoft_id +' successfully!')
    return redirect(view_team_members_details, memid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def edit_other_notes(request, memid):
    get_oa_id = OtherAccessories.objects.get(id=memid)
    context = { 'get_oa_id': get_oa_id, }
    return render(request, 'manager/view_team_member_details.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_other_notes(request, memid, psid):
    update_oa = OtherAccessories.objects.get(id=memid)

    if request.method == 'POST':
        update_oa.other_notes = request.POST['other_notes']
        update_oa.save()
        message_alert.success(request, 'Other notes was updated successfully!')
    return redirect(view_team_members_details, psid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def mark_returned(request, resid, memid):
    get_asset = ResourceTaken.objects.get(id=resid)
    take_asset_id = ResourceTaken.objects.get(id=get_asset.id, asset_id=get_asset.asset_id)
    update_resource = Resource.objects.filter(asset_id=take_asset_id.asset_id)

    if request.method == 'POST':
        reason_notes = request.POST['return_reason']
        # peoplesoft_id = request.POST['peoplesoft_id']

        if reason_notes == 'Leaving From Company' or reason_notes == 'Swaping For Highend Resource':
            get_asset.resource_status = 'Returned'
            get_asset.returned_date = date.today()
            get_asset.reason_notes = reason_notes
            get_asset.save()
            for update in update_resource:
                update.resource_availability = 'Available'
                update.save()

                #send email functionality for return resource process
                mail_head_subject = ' Resource Mark Returned Completed For ' + update.asset_id + ''
                message = render_to_string('account/resource_mark_return_email.html', {
                    'get_asset': get_asset,
                    'asset_id': update.asset_id,
                })
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [get_asset.peoplesoft_id.email,]
                send_mail(mail_head_subject, message, email_from, recipient_list)
                message_alert.success(request, 'Mark returned on the device successfully!')

        elif reason_notes == 'Resource Damaged' or reason_notes == 'Facing Software Issue':
            get_asset.resource_status = 'Returned'
            get_asset.returned_date = date.today()
            get_asset.reason_notes = reason_notes
            get_asset.save()
            for update in update_resource:
                update.resource_availability = 'Configuration'
                update.save()

            #send email functionality for return resource process
            mail_head_subject = ' Resource Mark Returned Completed For ' + update.asset_id + ''
            message = render_to_string('account/resource_mark_return_email.html', {
                'get_asset': get_asset,
                'asset_id': update.asset_id,
            })
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [get_asset.peoplesoft_id.email,]
            send_mail(mail_head_subject, message, email_from, recipient_list)
            message_alert.success(request, 'Mark returned on the device successfully!')

        elif reason_notes == '-------------':
            message_alert.info(request, 'Please choose a return reason to mark it as return!')
    
    return redirect(view_team_members_details, memid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_member_resource_info(request, memid, resid):
    get_member_id = Members.objects.get(id=memid)
    # get_ps_id = Members.objects.get(peoplesoft_id=get_member_id.peoplesoft_id)
    get_devices_id = ResourceTaken.objects.get(id=resid)
    context = { 'get_devices_id': get_devices_id, 'get_member_id': get_member_id, }
    return render(request, 'manager/view_resource_info.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_history_resources(request, memid):
    get_member_id = Members.objects.get(id=memid)
    get_ps_id = Members.objects.get(peoplesoft_id=get_member_id.peoplesoft_id)
    get_devices_id = ResourceTaken.objects.filter(peoplesoft_id=get_ps_id, resource_status='Returned')

    # for date_range in get_devices_id:
    #     get_date_taken = ResourceTaken.objects.get(taken_date=date_range.taken_date)
    #     get_date_returned = ResourceTaken.objects.get(returned_date=date_range.returned_date)
    #     date_format = "%Y-%m-%d"
    #     take_date = datetime.strptime(get_date_taken, date_format)
    #     return_date = datetime.strptime(get_date_returned, date_format)
    #     no_of_days = return_date - take_date
    #     print(no_of_days)


    context = { 'get_devices_id': get_devices_id, 'get_member_id': get_member_id, }
    return render(request, 'manager/view_history_devices.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_team_member(request, memid, userid):
    deleting_mem = Members.objects.get(id=memid)
    if request.method == 'POST':
        delete_name = request.POST['delete_name']
        if delete_name == 'delete':
            message_alert.success(request, deleting_mem.fullname + ' was deleted successfully!')
            deleting_mem.delete()
    return redirect(view_team_members, userid)    

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_team_members_index_table(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    team_members = Members.objects.all().filter(manager_peoplesoft_id=get_user_psid, is_active=True).order_by('peoplesoft_id')
    context = { 'team_members': team_members, }
    return render(request, 'manager/member_index_table.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def date_sort_team_members_index_table(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    if request.method == 'POST':
        from_date = request.POST['from_mem']
        to_date = request.POST['to_mem']
        get_result =  Members.objects.filter(date_joined__gte=from_date, date_joined__lte=to_date, manager_peoplesoft_id=get_user_psid, is_active=True).order_by('peoplesoft_id')
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'manager/member_index_table.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------