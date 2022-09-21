from importlib.resources import Resource
from multiprocessing import context
from django.shortcuts import render,redirect
import random
from .models import Resource
from django.contrib import messages as message_alert
# Create your views here.

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resources_list_table(request):
    resources = Resource.objects.all().filter(is_active=True)
    context = { 'resources': resources, }
    return render(request, 'it_admin/resources_list_table.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def add_resource_page(request):
    generated_asset_id = random.randrange(11111111111, 99999999999, 11)
    context = { 'generated_asset_id': generated_asset_id, }

    if request.method == 'POST':
        asset_id = request.POST['asset_id']
        device_type = request.POST['device_type']
        device_availability = request.POST['device_availability']
        device_description = request.POST['device_description']
        added_by = request.POST['added_by']
        
        if Resource.objects.filter(asset_id=asset_id).exists():
            message_alert.info(request, asset_id + ', is already exists!')
        elif device_type == '--Choose device type--':
            message_alert.info(request, 'Please choose a device type to add a device!')
        elif device_availability == '--Choose device availability--':
            message_alert.info(request, 'Please choose a device availability to add a device!')
        else:
            resource = Resource(asset_id=asset_id, device_type=device_type, device_availability=device_availability, device_description=device_description, added_by=added_by)
            resource.save()
            message_alert.success(request, asset_id + ' is added successfully!')
            return redirect(resources_list_table)

    return render(request, 'it_admin/resource_form.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def edit_resource(request, resid):
    selected_res = Resource.objects.get(id=resid)
    context = { 'selected_res': selected_res, }
    return render(request, 'it_admin/resource_form.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_resource(request, resid):
    update_res = Resource.objects.get(id=resid)
    update_res.asset_id = request.POST['asset_id']
    update_res.device_type = request.POST['device_type']
    update_res.device_availability = request.POST['device_availability']
    update_res.device_description = request.POST['device_description']
    update_res.added_by = request.POST['added_by']
    update_res.save()
    message_alert.success(request, 'Device details of ' + update_res.asset_id + ' was updated successfully!')
    return redirect(resources_list_table)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_resource(request, resid):
    deleting_res = Resource.objects.get(id=resid)
    deleting_res.is_active = False
    deleting_res.save()
    message_alert.success(request, 'Device removed successfully!')
    return redirect(resources_list_table)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resource_deletion_history(request):
    resources = Resource.objects.all().filter(is_active=False)
    context = { 'resources': resources, }
    return render(request, 'it_admin/resource_deletion_history.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def restore_device(request, resid):
    restoring_device = Resource.objects.get(id=resid)
    restoring_device.is_active = True
    restoring_device.save()
    message_alert.success(request, 'Device restored successfully!')
    return redirect(resource_deletion_history)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def permanent_delete_device(request, resid):
    delete_device = Resource.objects.get(id=resid)
    delete_device.delete()
    message_alert.success(request, 'Device permanently deleted successfully!')
    return redirect(resource_deletion_history)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resources_date_sort(request):
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  Resource.objects.filter(added_on__gte=from_date, added_on__lte=to_date)
    context = { 'get_result': get_result, }
    return render(request, 'it_admin/resources_list_table.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------