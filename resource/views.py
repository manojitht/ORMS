from importlib.resources import Resource
from multiprocessing import context
import os
from unicodedata import category
from django.shortcuts import render,redirect
import random
from .models import Resource, Category, ResourceTaken
from django.contrib import messages as message_alert
from department.models import Department
from account.models import Account
from django.db.models import Q
# Create your views here.

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resources_list_table(request):
    resources = Resource.objects.all().filter(is_active=True)
    context = { 'resources': resources, }
    return render(request, 'it_admin/resources_list_table.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def returned_resources_list_table(request):
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Returned')
    context = { 'resources': resources, }
    return render(request, 'it_admin/view_returns_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def taken_resources_list_table(request):
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Taken')
    context = { 'resources': resources, }
    return render(request, 'it_admin/view_taken_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def add_resource_page(request):
    generated_asset_id = random.randrange(111111111, 999999999, 9)
    full_generated_aset_id = 'TGSSIT' + str(generated_asset_id)
    resource_categories = Category.objects.all()
    context = { 'resource_categories': resource_categories, 'full_generated_aset_id': full_generated_aset_id, }

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
        elif resource_category == '--Choose Resource Type--':
            message_alert.info(request, 'Please choose a device type to add a device!')
            return redirect(add_resource_page)
        elif resource_availability == '--Choose device availability--':
            message_alert.info(request, 'Please choose a device availability to add a device!')
        else:
            resource = Resource(asset_id=asset_id, model_name=model_name, 
            resource_category=Category.objects.get(resource_category=resource_category), 
            bitlocker_key=bitlocker_key, resource_availability=resource_availability, 
            resource_description=resource_description, added_by=added_by, resource_image=resource_image)
            resource.save()
            message_alert.success(request, asset_id + ' is added successfully!')
            return redirect(resources_listings_page)

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
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'it_admin/resources_list_table.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def returned_resources_date_sort(request):
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  ResourceTaken.objects.filter(returned_date__gte=from_date, returned_date__lte=to_date)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'it_admin/view_returns_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def taken_resources_date_sort(request):
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  ResourceTaken.objects.filter(taken_date__gte=from_date, taken_date__lte=to_date)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'it_admin/view_taken_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def it_admin_notes_page(request):
    return render(request, 'it_admin/it_admin_notes_page.html')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resources_listings_page(request):
    resources = Resource.objects.all().filter(is_active=True).order_by('resource_availability')
    res_count = resources.count()
    context = { 'resources': resources, 'res_count': res_count, }
    return render(request, 'it_admin/resources_listings_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_resource(request, resid):
    selected_res = Resource.objects.get(id=resid)
    context = { 'selected_res': selected_res, }
    return render(request, 'it_admin/view_resource_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_resource_categories(request):
    all_categories = Category.objects.all()
    category_count = all_categories.count()
    context = { 'all_categories': all_categories, 'category_count': category_count, }
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

def edit_category_page(request, catid):
    get_cat = Category.objects.get(id=catid)
    context = { 'get_cat': get_cat, }
    return render(request, 'it_admin/edit_category_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def update_category(request, catid):
    update_cat = Category.objects.get(id=catid)

    if request.method == 'POST':
        if len(request.FILES) != 0:
            if len(update_cat.category_image) > 0:
                os.remove(update_cat.category_image.path)
            update_cat.category_image = request.FILES['category_image']
        update_cat.resource_category = request.POST['category_name']
        update_cat.description = request.POST['category_description']
        update_cat.save()
        message_alert.success(request, update_cat.resource_category + ' category was updated successfully!')
    return redirect(view_resource_categories)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_category_warning(request, delcatid):
    get_cat = Category.objects.get(id=delcatid) 
    # resources_count = Resource.objects.filter(is_active=True, resource_category=get_cat.resource_category).count()
    context = { 'get_cat': get_cat, }
    return render(request, 'it_admin/warning_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_resource(request, resid):
    if request.method == 'POST':
        delete_name = request.POST['delete_name']
        if delete_name == 'delete':
            deleting_res = Resource.objects.get(id=resid)
            deleting_res.delete()
            message_alert.success(request, deleting_res.asset_id + ' - Resource was deleted successfully!')
    return redirect(resources_listings_page)
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def search_resource(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            search_resource = Resource.objects.filter(is_active=True).filter(Q(asset_id__icontains=keyword) | Q(model_name__icontains=keyword))
            search_count = search_resource.count()
    context = { 'search_resource': search_resource, 'keyword': keyword, 'search_count': search_count, }
    return render(request, 'it_admin/resources_listings_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def manager_returned_resources_list_table(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Returned', manager_peoplesoft_id=get_user_psid)
    context = { 'resources': resources, }
    return render(request, 'manager/view_returns_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def manager_taken_resources_list_table(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Taken', manager_peoplesoft_id=get_user_psid)
    context = { 'resources': resources, }
    return render(request, 'manager/view_taken_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def manager_returned_resources_date_sort(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  ResourceTaken.objects.filter(returned_date__gte=from_date, returned_date__lte=to_date, manager_peoplesoft_id=get_user_psid)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'manager/view_returns_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def manager_taken_resources_date_sort(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  ResourceTaken.objects.filter(taken_date__gte=from_date, taken_date__lte=to_date, manager_peoplesoft_id=get_user_psid)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'manager/view_taken_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------