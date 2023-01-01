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
            # return redirect('add_member')
        elif Members.objects.filter(email=email).exists():
            message_alert.info(request, email + ', is already exists in team member profile!')
            # return redirect('add_member')
        else:
            new_member = Members(peoplesoft_id=peoplesoft_id, fullname=fullname, position=position, email=email, contact=contact, department=Department.objects.get(department_name=department),
            team=Team.objects.get(team_name=team), home_address=home_address, member_image=member_image, manager_name=manager_name, manager_peoplesoft_id=manager_peoplesoft_id)
            new_member.save()
            message_alert.success(request, peoplesoft_id + ' team member profile created successfully!')
            return redirect('add_member')

    return render(request, 'manager/add_member_form.html')

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_team_members(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    team_members = Members.objects.all().filter(manager_peoplesoft_id=get_user_psid, is_active=True).order_by('peoplesoft_id')
    context = { 'team_members': team_members, }
    return render(request, 'manager/view_team_member.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_team_members_details(request, memid):
    get_member_id = Members.objects.get(id=memid)
    get_ps_id = Members.objects.get(peoplesoft_id=get_member_id.peoplesoft_id)
    get_devices_id = ResourceTaken.objects.filter(peoplesoft_id=get_ps_id, resource_status='Taken')
    try: 
        get_oa = OtherAccessories.objects.get(peoplesoft_id=get_ps_id)
    except:
        get_oa = OtherAccessories.objects.filter(peoplesoft_id=get_ps_id)

    # for get_devices in get_devices_id:
    #     description = get_devices.asset_id.device_description
    #     image = get_devices.asset_id.device_image
    #     bitlocker = get_devices.asset_id.bitlocker_key
    
    context = { 'get_member_id': get_member_id, 'get_devices_id': get_devices_id, 'get_oa': get_oa, }
    return render(request, 'manager/view_team_member_details.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def search_team_member(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            search_team_member = Members.objects.filter(manager_peoplesoft_id=get_user_psid, is_active=True).filter(Q(peoplesoft_id__icontains=keyword) | Q(fullname__icontains=keyword))
    context = { 'search_team_member': search_team_member, }
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

# def allocate_device(request, memid):
#     if request.method == 'POST':
#         asset_id = request.POST['asset_id']
#         peoplesoft_id = request.POST['peoplesoft_id']
#         department = request.POST['department']
#         team = request.POST['team']
#         added_by = request.POST['added_by']
#         resource_status = request.POST['resource_status']

#         if Resource.objects.filter(asset_id=asset_id, resource_availability='Taken').exists():
#             message_alert.info(request, asset_id + ', is already in use by other team member!')
#         elif Resource.objects.filter(asset_id=asset_id, resource_availability='Configuration').exists():
#             message_alert.info(request, asset_id + ', resource is not allocated, please check!')
#         elif Resource.objects.filter(asset_id=asset_id, resource_availability='Available').exists():
#             message_alert.info(request, asset_id + ', resource is not allocated, please check!')
#         elif Resource.objects.filter(asset_id=asset_id, resource_availability='Reserved').exists():
#             get_resource_type = Resource.objects.get(asset_id=asset_id)
#             # resource_category = get_resource_type.resource_category.resource_category

#             allocate_device = ResourceTaken(asset_id=Resource.objects.get(asset_id=asset_id), peoplesoft_id=Members.objects.get(peoplesoft_id=peoplesoft_id), resource_category=get_resource_type.resource_category.resource_category, department=Department.objects.get(department_name=department),
#             team=Team.objects.get(team_name=team), added_by=added_by, resource_status=resource_status)
#             allocate_device.save()
#             get_asset_id = Resource.objects.filter(asset_id=asset_id)
#             for set_taken in get_asset_id:
#                 set_taken.resource_availability = 'Taken'
#                 set_taken.save()
#             message_alert.success(request, asset_id + ' allocated to ' + peoplesoft_id +' successfully!')
#         else:
#             message_alert.error(request, asset_id + ' invalid asset id, please check!')

#             # get_member_id = Members.objects.get(peoplesoft_id=peoplesoft_id)
#             # member_id = get_member_id.id

#     return redirect(view_team_members_details, memid)

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

def update_other_notes(request, memid):
    update_oa = OtherAccessories.objects.get(id=memid)

    if request.method == 'POST':
        update_oa.other_notes = request.POST['other_notes']
        update_oa.save()
        message_alert.success(request, 'Other notes was updated successfully!')
    return redirect(view_team_members_details, memid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def mark_returned(request, resid, memid):
    get_asset = ResourceTaken.objects.get(id=resid)
    get_asset_id = ResourceTaken.objects.filter(asset_id=get_asset.asset_id)
    take_asset_id = ResourceTaken.objects.get(asset_id=get_asset.asset_id, id=get_asset.id)
    update_resource = Resource.objects.filter(asset_id=take_asset_id.asset_id)
    get_asset.resource_status = 'Returned'
    get_asset.returned_date = date.today()
    get_asset.save()

    # for asset in get_asset_id:
    #     asset.device_status = 'Returned'
    #     asset.returned_date = datetime.date.today()
    #     asset.save()
    
    for update in update_resource:
        update.resource_availability = 'Available'
        update.save()
    
    message_alert.success(request, 'Mark returned on the device successfully!')

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