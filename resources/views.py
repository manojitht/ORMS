import os
import json
from django.shortcuts import render,redirect
import random
from django.utils.text import slugify
from .models import Resource, Category, ResourceTaken
from django.contrib import messages as message_alert
from account.models import Account
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from sukhra.csv_utils import csv_response
# Create your views here.


def _parse_attribute_schema_from_post(post):
    """Zip the repeatable attr_key[]/attr_label[] rows from the Category
    add/edit forms into the [{"key": ..., "label": ...}, ...] shape stored
    on Category.attribute_schema. Blank rows (no key or no label) are
    dropped, and keys are slugified so they're always safe to use as a
    dict key (Resource.attribute_values) and a POST field-name suffix
    (attr__<key>) later.
    """
    keys = post.getlist('attr_key[]')
    labels = post.getlist('attr_label[]')
    schema = []
    for key, label in zip(keys, labels):
        key, label = key.strip(), label.strip()
        if key and label:
            schema.append({'key': slugify(key).replace('-', '_'), 'label': label})
    return schema


def _parse_attribute_values_from_post(post, category):
    """Read attr__<key> fields for whichever attributes the resource's
    category declares -- the Add/Edit Resource templates only render (and
    enable) inputs for the selected category's own schema, so this only
    ever picks up values relevant to that category.
    """
    values = {}
    for attr_def in category.attribute_schema:
        key = attr_def['key']
        value = post.get(f'attr__{key}', '').strip()
        if value:
            values[key] = value
    return values

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def resources_list_table(request):
    resources = Resource.objects.all().filter(is_active=True)
    context = { 'resources': resources, }
    return render(request, 'it_admin/resources_list_table.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def export_resources_csv(request):
    resources = Resource.objects.filter(is_active=True)
    rows = (
        (r.asset_id, r.resource_category.resource_category, r.added_by, r.added_on, r.resource_availability)
        for r in resources
    )
    return csv_response('resources.csv',
        ('Asset Id', 'Resource Type', 'Lastly Updated By', 'Added On', 'Availability'), rows)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def returned_resources_list_table(request):
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Returned')
    context = { 'resources': resources, }
    return render(request, 'it_admin/view_returns_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def taken_resources_list_table(request):
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Taken')
    context = { 'resources': resources, }
    return render(request, 'it_admin/view_taken_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def _category_schema_context(resource_categories):
    """Shared context builder for the Add/Edit Resource templates: a
    {category_id: [attribute_keys]} map (drives which fields the per-category
    JS shows/enables) and a de-duplicated (key, label) list across all of the
    company's categories (so every possible attribute field can be rendered
    once in the template and just toggled, with no page reload on category
    change).
    """
    category_schema_map = {str(c.id): [a['key'] for a in c.attribute_schema] for c in resource_categories}
    all_attribute_defs = {}
    for c in resource_categories:
        for a in c.attribute_schema:
            all_attribute_defs.setdefault(a['key'], a['label'])
    return {
        'category_schema_json': json.dumps(category_schema_map),
        'all_attribute_defs': list(all_attribute_defs.items()),
    }


@login_required(login_url='account:login')
def add_resource_page(request):
    generated_asset_id = random.randrange(111111111, 999999999, 9)
    full_generated_aset_id = 'TGSSIT' + str(generated_asset_id)
    resource_categories = Category.objects.filter(is_active=True)
    context = { 'resource_categories': resource_categories, 'full_generated_aset_id': full_generated_aset_id, }
    context.update(_category_schema_context(resource_categories))

    if request.method == 'POST':
        asset_id = request.POST['asset_id']
        model_name = request.POST['model_name']
        resource_category_id = request.POST['resource_category']
        resource_availability = request.POST['resource_availability']
        resource_description = request.POST['resource_description']
        added_by = request.POST['added_by']
        resource_image = request.FILES['resource_image']

        if Resource.objects.filter(asset_id=asset_id).exists():
            message_alert.info(request, asset_id + ', is already exists!')
        elif not resource_category_id:
            message_alert.info(request, 'Please choose a device type to add a device!')
            return redirect('resources:add_resource_page')
        elif resource_availability == '--Choose device availability--':
            message_alert.info(request, 'Please choose a device availability to add a device!')
        else:
            category = Category.objects.get(id=resource_category_id)
            attribute_values = _parse_attribute_values_from_post(request.POST, category)
            resource = Resource(asset_id=asset_id, model_name=model_name,
            resource_category=category, attribute_values=attribute_values,
            resource_availability=resource_availability,
            resource_description=resource_description, added_by=added_by, resource_image=resource_image)
            resource.save()
            message_alert.success(request, asset_id + ' is added successfully!')
            return redirect('resources:resources_listings_page')

    return render(request, 'it_admin/add_resource_form.html', context)
    # return render(request, 'it_admin/resource_form.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def edit_resource(request, resid):
    selected_res = Resource.objects.get(id=resid)
    resource_categories = Category.objects.filter(is_active=True)
    context = { 'selected_res': selected_res, 'resource_categories': resource_categories, }
    context.update(_category_schema_context(resource_categories))
    return render(request, 'it_admin/edit_resource_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def update_resource(request, resid):
    update_res = Resource.objects.get(id=resid)

    if request.method == 'POST':
        if len(request.FILES) != 0:
            if len(update_res.resource_image) > 0:
                os.remove(update_res.resource_image.path)
            update_res.resource_image = request.FILES['resource_image']
        update_res.asset_id = request.POST['asset_id']
        update_res.model_name = request.POST['model_name']
        category = Category.objects.get(id=request.POST['resource_category'])
        update_res.resource_category = category
        update_res.attribute_values = _parse_attribute_values_from_post(request.POST, category)
        update_res.resource_availability = request.POST['resource_availability']
        update_res.resource_description = request.POST['resource_description']
        update_res.added_by = request.POST['added_by']
        update_res.save()
        message_alert.success(request, 'Resource details of ' + update_res.asset_id + ' was updated successfully!')
    return redirect('resources:resources_listings_page')

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def resource_deletion_history(request):
    resources = Resource.objects.all().filter(is_active=False)
    context = { 'resources': resources, }
    return render(request, 'it_admin/resource_deletion_history.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def restore_device(request, resid):
    restoring_device = Resource.objects.get(id=resid)
    restoring_device.is_active = True
    restoring_device.save()
    message_alert.success(request, 'Device restored successfully!')
    return redirect('resources:resource_deletion_history')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def permanent_delete_device(request, resid):
    delete_device = Resource.objects.get(id=resid)
    delete_device.delete()
    message_alert.success(request, 'Device permanently deleted successfully!')
    return redirect('resources:resource_deletion_history')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def resources_date_sort(request):
    get_result, from_date, to_date, result_count = None, None, None, 0
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  Resource.objects.filter(added_on__gte=from_date, added_on__lte=to_date)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, 'resources': None, }
    return render(request, 'it_admin/resources_list_table.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def returned_resources_date_sort(request):
    get_result, from_date, to_date, result_count = None, None, None, 0
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  ResourceTaken.objects.filter(returned_date__gte=from_date, returned_date__lte=to_date)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, 'resources': None, }
    return render(request, 'it_admin/view_returns_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def taken_resources_date_sort(request):
    get_result, from_date, to_date, result_count = None, None, None, 0
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  ResourceTaken.objects.filter(taken_date__gte=from_date, taken_date__lte=to_date)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, 'resources': None, }
    return render(request, 'it_admin/view_taken_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def it_admin_notes_page(request):
    return render(request, 'it_admin/it_admin_notes_page.html')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def resources_listings_page(request):
    resources = Resource.objects.all().filter(is_active=True).order_by('resource_availability')
    res_count = resources.count()
    context = { 'resources': resources, 'res_count': res_count, }
    return render(request, 'it_admin/resources_listings_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def view_resource(request, resid):
    selected_res = Resource.objects.get(id=resid)
    context = { 'selected_res': selected_res, }
    return render(request, 'it_admin/view_resource_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def view_resource_categories(request):
    all_categories = Category.objects.all()
    category_count = all_categories.count()
    context = { 'all_categories': all_categories, 'category_count': category_count, }
    return render(request, 'it_admin/view_categories_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def add_category_page(request):
    
    if request.method == 'POST':
        resource_category = request.POST['resource_category']
        description = request.POST['description']
        category_image = request.FILES['category_image']
        tracks_physical_asset = 'tracks_physical_asset' in request.POST
        attribute_schema = _parse_attribute_schema_from_post(request.POST)

        if Category.objects.filter(resource_category=resource_category).exists():
            message_alert.info(request, resource_category + ', is already exists as category!')
        else:
            category = Category(resource_category=resource_category, description=description,
            category_image=category_image, tracks_physical_asset=tracks_physical_asset,
            attribute_schema=attribute_schema)
            category.save()
            message_alert.success(request, resource_category + ' is added successfully as a category!')
            return redirect('resources:view_resource_categories')

    return redirect('resources:view_resource_categories')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def edit_category_page(request, catid):
    get_cat = Category.objects.get(id=catid)
    context = { 'get_cat': get_cat, }
    return render(request, 'it_admin/edit_category_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def update_category(request, catid):
    update_cat = Category.objects.get(id=catid)

    if request.method == 'POST':
        if len(request.FILES) != 0:
            if len(update_cat.category_image) > 0:
                os.remove(update_cat.category_image.path)
            update_cat.category_image = request.FILES['category_image']
        update_cat.resource_category = request.POST['category_name']
        update_cat.description = request.POST['category_description']
        update_cat.tracks_physical_asset = 'tracks_physical_asset' in request.POST
        update_cat.attribute_schema = _parse_attribute_schema_from_post(request.POST)
        update_cat.save()
        message_alert.success(request, update_cat.resource_category + ' category was updated successfully!')
    return redirect('resources:view_resource_categories')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def delete_category_warning(request, delcatid):
    get_cat = Category.objects.get(id=delcatid) 
    # resources_count = Resource.objects.filter(is_active=True, resource_category=get_cat.resource_category).count()
    context = { 'get_cat': get_cat, }
    return render(request, 'it_admin/warning_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def delete_resource(request, resid):
    if request.method == 'POST':
        delete_name = request.POST['delete_name']
        if delete_name == 'delete':
            deleting_res = Resource.objects.get(id=resid)
            deleting_res.delete()
            message_alert.success(request, deleting_res.asset_id + ' - Resource was deleted successfully!')
    return redirect('resources:resources_listings_page')
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def search_resource(request):
    keyword = request.GET.get('keyword', '')
    search_resource = None
    search_count = 0
    if keyword:
        search_resource = Resource.objects.filter(is_active=True).filter(Q(asset_id__icontains=keyword) | Q(model_name__icontains=keyword))
        search_count = search_resource.count()
    context = { 'search_resource': search_resource, 'keyword': keyword, 'search_count': search_count, 'resources': None, }
    return render(request, 'it_admin/resources_listings_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def manager_returned_resources_list_table(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Returned', manager_peoplesoft_id=get_user_psid)
    context = { 'resources': resources, }
    return render(request, 'manager/view_returns_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def manager_taken_resources_list_table(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Taken', manager_peoplesoft_id=get_user_psid)
    context = { 'resources': resources, }
    return render(request, 'manager/view_taken_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def manager_returned_resources_date_sort(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_result, from_date, to_date, result_count = None, None, None, 0
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  ResourceTaken.objects.filter(returned_date__gte=from_date, returned_date__lte=to_date, manager_peoplesoft_id=get_user_psid)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, 'resources': None, }
    return render(request, 'manager/view_returns_page.html', context)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='account:login')
def manager_taken_resources_date_sort(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_result, from_date, to_date, result_count = None, None, None, 0
    if request.method == 'POST':
        from_date = request.POST['from_res']
        to_date = request.POST['to_res']
        get_result =  ResourceTaken.objects.filter(taken_date__gte=from_date, taken_date__lte=to_date, manager_peoplesoft_id=get_user_psid)
        result_count = get_result.count()
    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, 'resources': None, }
    return render(request, 'manager/view_taken_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------