from importlib.resources import Resource
from multiprocessing import context
import os
from unicodedata import category
from django.shortcuts import render,redirect
import random
from .models import Resource, Category
from django.contrib import messages as message_alert
from department.models import Department
# Create your views here.

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resources_list_table(request):
    resources = Resource.objects.all().filter(is_active=True)
    context = { 'resources': resources, }
    return render(request, 'it_admin/resources_list_table.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def add_resource_page(request):
    # generated_asset_id = random.randrange(11111111111, 99999999999, 11)
    # context = { 'generated_asset_id': generated_asset_id, }

    resource_categories = Category.objects.all()
    context = { 'resource_categories': resource_categories, }

    if request.method == 'POST':
        asset_id = request.POST['asset_id']
        model_name = request.POST['model_name']
        resource_category = request.POST['resource_category']
        resource_availability = request.POST['resource_availability']
        resource_description = request.POST['resource_description']
        added_by = request.POST['added_by']
        bitlocker_key = request.POST['bitlocker_key']
        resource_image = request.FILES['resource_image']
        
        if Resource.objects.filter(asset_id=asset_id).exists():
            message_alert.info(request, asset_id + ', is already exists!')
        elif resource_category == '--Choose resource type--':
            message_alert.info(request, 'Please choose a device type to add a device!')
        elif resource_availability == '--Choose device availability--':
            message_alert.info(request, 'Please choose a device availability to add a device!')
        else:
            resource = Resource(asset_id=asset_id, model_name=model_name, resource_category=Category.objects.get(resource_category=resource_category), bitlocker_key=bitlocker_key, resource_availability=resource_availability, resource_description=resource_description, added_by=added_by, resource_image=resource_image)
            resource.save()
            message_alert.success(request, asset_id + ' is added successfully!')
            return redirect(resources_listings_page)
            # return redirect(resources_list_table)

    return render(request, 'it_admin/add_resource_form.html', context)
    # return render(request, 'it_admin/resource_form.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def edit_resource(request, resid):
    selected_res = Resource.objects.get(id=resid)
    resource_categories = Category.objects.all()
    context = { 'selected_res': selected_res, 'resource_categories': resource_categories, }
    return render(request, 'it_admin/edit_resource_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_resource(request, resid):
    update_res = Resource.objects.get(id=resid)

    if request.method == 'POST':
        if len(request.FILES) != 0:
            if len(update_res.resource_image) > 0:
                os.remove(update_res.resource_image.path)
            update_res.resource_image = request.FILES['resource_image']
        update_res.asset_id = request.POST['asset_id']
        update_res.model_name = request.POST['model_name']
        take_category = request.POST['resource_category']
        update_res.resource_category = Category.objects.get(resource_category=take_category)
        update_res.resource_availability = request.POST['resource_availability']
        update_res.resource_description = request.POST['resource_description']
        update_res.added_by = request.POST['added_by']
        update_res.bitlocker_key = request.POST['bitlocker_key']
        update_res.save()
        message_alert.success(request, 'Resource details of ' + update_res.asset_id + ' was updated successfully!')
    return redirect(resources_listings_page)

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

def it_admin_notes_page(request):
    return render(request, 'it_admin/it_admin_notes_page.html')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resources_listings_page(request):
    resources = Resource.objects.all().filter(is_active=True).order_by('resource_availability')
    context = { 'resources': resources, }
    return render(request, 'it_admin/resources_listings_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_resource(request, resid):
    selected_res = Resource.objects.get(id=resid)
    context = { 'selected_res': selected_res, }
    return render(request, 'it_admin/view_resource_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_resource_categories(request):
    all_categories = Category.objects.all()
    context = { 'all_categories': all_categories, }
    return render(request, 'it_admin/view_categories_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def add_category_page(request):
    
    if request.method == 'POST':
        resource_category = request.POST['resource_category']
        description = request.POST['description']
        category_image = request.FILES['category_image']
        
        if Category.objects.filter(resource_category=resource_category).exists():
            message_alert.info(request, resource_category + ', is already exists as category!')
        else:
            category = Category(resource_category=resource_category, description=description, category_image=category_image)
            category.save()
            message_alert.success(request, resource_category + ' is added successfully as a category!')
            return redirect(view_resource_categories)

    return redirect(view_resource_categories)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------