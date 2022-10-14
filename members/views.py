from django.shortcuts import render
from django.contrib import messages as message_alert, auth
from django.shortcuts import redirect, render
from django.db.models import Q
from members.models import Members
from resource.models import Resource, ResourceTaken, OtherAccessories
from department.models import Department
from account.models import Account
from team.models import Team
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

def manager_dashboard(request):
    return render(request, 'manager/manager_dashboard.html')

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
    get_devices_id = ResourceTaken.objects.filter(peoplesoft_id=get_ps_id, device_status='Taken')
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

def allocate_device(request, memid):
    if request.method == 'POST':
        asset_id = request.POST['asset_id']
        peoplesoft_id = request.POST['peoplesoft_id']
        department = request.POST['department']
        team = request.POST['team']
        added_by = request.POST['added_by']
        device_status = request.POST['device_status']

        if Resource.objects.filter(asset_id=asset_id, device_availability='Taken').exists():
            message_alert.info(request, asset_id + ', is already in use by other team member!')
        elif Resource.objects.filter(asset_id=asset_id, device_availability='Configuration').exists():
            message_alert.info(request, asset_id + ', device is not allocated, please check!')
        elif Resource.objects.filter(asset_id=asset_id, device_availability='Available').exists():
            message_alert.info(request, asset_id + ', device is not allocated, please check!')
        elif Resource.objects.filter(asset_id=asset_id, device_availability='Reserved').exists():
            get_device_type = Resource.objects.get(asset_id=asset_id)
            device_type = get_device_type.device_type

            allocate_device = ResourceTaken(asset_id=Resource.objects.get(asset_id=asset_id), peoplesoft_id=Members.objects.get(peoplesoft_id=peoplesoft_id), device_type=device_type, department=Department.objects.get(department_name=department),
            team=Team.objects.get(team_name=team), added_by=added_by, device_status=device_status)
            allocate_device.save()
            get_asset_id = Resource.objects.filter(asset_id=asset_id)
            for set_taken in get_asset_id:
                set_taken.device_availability = 'Taken'
                set_taken.save()
            message_alert.success(request, asset_id + ' allocated to ' + peoplesoft_id +' successfully!')
        else:
            message_alert.error(request, asset_id + ' invalid asset id, please check!')

            # get_member_id = Members.objects.get(peoplesoft_id=peoplesoft_id)
            # member_id = get_member_id.id

    return redirect(view_team_members_details, memid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def add_other_accessories(request, memid):
    if request.method == 'POST':
        peoplesoft_id = request.POST['peoplesoft_id']
        keyboard = request.POST['keyboard']
        mouse = request.POST['mouse']
        network_adapter = request.POST['network_adapter']
        headset = request.POST['headset']
        other_notes = request.POST['other_notes']

        if keyboard == '--Keyboard Taken--':
            message_alert.info(request, 'Please select option on keyboard!')
        elif mouse == '--Mouse Taken--':
            message_alert.info(request, 'Please select option on mouse!')
        elif network_adapter == '--Network adapter Taken--':
            message_alert.info(request, 'Please select option on network adapter!')
        elif headset == '--Headset Taken--':
            message_alert.info(request, 'Please select option on headset!')
        else:
            add_accessories = OtherAccessories(peoplesoft_id=Members.objects.get(peoplesoft_id=peoplesoft_id), keyboard=keyboard, mouse=mouse,
            network_adapter=network_adapter, headset=headset, other_notes=other_notes)
            add_accessories.save()
            message_alert.success(request, 'Other accessories added to ' + peoplesoft_id +' successfully!')
    return redirect(view_team_members_details, memid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def edit_other_accessories(request, memid):
    get_oa_id = OtherAccessories.objects.get(id=memid)
    context = { 'get_oa_id': get_oa_id, }
    return render(request, 'manager/view_team_member_details.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_other_accessories(request, memid):
    update_oa = OtherAccessories.objects.get(id=memid)

    if request.method == 'POST':
        update_oa.keyboard = request.POST['keyboard']
        update_oa.mouse = request.POST['mouse']
        update_oa.network_adapter = request.POST['network_adapter']
        update_oa.headset = request.POST['headset']
        update_oa.other_notes = request.POST['other_notes']
        update_oa.save()
        message_alert.success(request, 'Other accessories details was updated successfully!')
    return redirect(view_team_members_details, memid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------