import os
import csv
import io
import json
import qrcode
from datetime import date, timedelta
from django.shortcuts import render,redirect
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from django.urls import reverse
import random
from django.utils.text import slugify
from .models import Resource, Category, ResourceTaken, WARRANTY_ALERT_WINDOW_DAYS
from django.contrib import messages as message_alert
from account.models import Account
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from sukhra.csv_utils import csv_response
from activity.models import ActivityEntry
from activity.services import log_activity

RESOURCE_IMPORT_FIXED_COLUMNS = ('Asset Id', 'Model Name', 'Resource Type', 'Availability', 'Description', 'Added By')


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


@login_required(login_url='account:login')
def resources_list_table(request):
    resources = Resource.objects.all().filter(is_active=True)
    context = { 'resources': resources, }
    return render(request, 'it_admin/resources_list_table.html', context)


@login_required(login_url='account:login')
def export_resources_csv(request):
    resources = Resource.objects.filter(is_active=True)
    rows = (
        (r.asset_id, r.resource_category.resource_category, r.added_by, r.added_on, r.resource_availability)
        for r in resources
    )
    return csv_response('resources.csv',
        ('Asset Id', 'Resource Type', 'Lastly Updated By', 'Added On', 'Availability'), rows)


def _all_attribute_keys(resource_categories):
    """De-duplicated (key, label) pairs across every category's
    attribute_schema, in the exact same shape _category_schema_context
    builds for the Add/Edit Resource forms -- reused here so the CSV
    template/import share one column-naming convention (attr__<key>)
    with the manual entry forms.
    """
    all_attribute_defs = {}
    for c in resource_categories:
        for a in c.attribute_schema:
            all_attribute_defs.setdefault(a['key'], a['label'])
    return list(all_attribute_defs.items())


@login_required(login_url='account:login')
def download_resource_import_template_csv(request):
    resource_categories = Category.objects.filter(is_active=True)
    attribute_keys = _all_attribute_keys(resource_categories)
    header = list(RESOURCE_IMPORT_FIXED_COLUMNS) + [f'attr__{key}' for key, _label in attribute_keys]
    rows = (
        (f'EXAMPLE-{c.resource_category[:10]}', 'e.g. ThinkPad X1', c.resource_category, 'Available', '', '')
        + tuple('' for _ in attribute_keys)
        for c in resource_categories
    )
    return csv_response('resource_import_template.csv', header, rows)


@login_required(login_url='account:login')
def import_resources_csv(request):
    resource_categories = Category.objects.filter(is_active=True)

    if request.method == 'POST':
        csv_file = request.FILES.get('file')
        if not csv_file:
            message_alert.info(request, 'Please choose a CSV file to import!')
            return render(request, 'it_admin/import_resources_page.html', {'resource_categories': resource_categories})

        categories_by_name = {c.resource_category.strip().lower(): c for c in resource_categories}
        reader = csv.DictReader(io.TextIOWrapper(csv_file.file, encoding='utf-8-sig'))

        imported_count = 0
        skipped_rows = []
        # row_number starts at 2 since the header itself is row 1 -- matches
        # what a user would count opening the file in a spreadsheet app.
        for row_number, row in enumerate(reader, start=2):
            try:
                asset_id = (row.get('Asset Id') or '').strip()
                model_name = (row.get('Model Name') or '').strip()
                category_name = (row.get('Resource Type') or '').strip()
                availability = (row.get('Availability') or '').strip() or 'Available'
                description = (row.get('Description') or '').strip()
                added_by = (row.get('Added By') or '').strip() or request.user.first_name

                if not asset_id or not model_name or not category_name:
                    raise ValueError('Asset Id, Model Name, and Resource Type are required')
                if Resource.objects.filter(asset_id=asset_id).exists():
                    raise ValueError(f'"{asset_id}" already exists')
                category = categories_by_name.get(category_name.lower())
                if not category:
                    raise ValueError(f'Unknown resource category "{category_name}"')

                attribute_values = {}
                for attr_def in category.attribute_schema:
                    key = attr_def['key']
                    value = (row.get(f'attr__{key}') or '').strip()
                    if value:
                        attribute_values[key] = value

                created_resource = Resource.objects.create(
                    asset_id=asset_id, model_name=model_name, resource_category=category,
                    attribute_values=attribute_values, resource_availability=availability,
                    resource_description=description, added_by=added_by,
                )
                log_activity(
                    request.user, 'resource_created',
                    f'{request.user} imported {asset_id} via CSV',
                    related_resource=created_resource,
                )
                imported_count += 1
            except Exception as exc:
                skipped_rows.append({'row_number': row_number, 'reason': str(exc)})

        context = { 'imported_count': imported_count, 'skipped_rows': skipped_rows, }
        return render(request, 'it_admin/import_resources_result.html', context)

    return render(request, 'it_admin/import_resources_page.html', {'resource_categories': resource_categories})


@login_required(login_url='account:login')
def returned_resources_list_table(request):
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Returned')
    context = { 'resources': resources, }
    return render(request, 'it_admin/view_returns_page.html', context)


@login_required(login_url='account:login')
def taken_resources_list_table(request):
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Taken')
    context = { 'resources': resources, }
    return render(request, 'it_admin/view_taken_page.html', context)


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
        warranty_expiry_date = request.POST.get('warranty_expiry_date') or None

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
            resource_availability=resource_availability, warranty_expiry_date=warranty_expiry_date,
            resource_description=resource_description, added_by=added_by, resource_image=resource_image)
            resource.save()
            log_activity(
                request.user, 'resource_created',
                f'{request.user} added {asset_id}',
                related_resource=resource,
            )
            message_alert.success(request, asset_id + ' is added successfully!')
            return redirect('resources:resources_listings_page')

    return render(request, 'it_admin/add_resource_form.html', context)


@login_required(login_url='account:login')
def edit_resource(request, resid):
    selected_res = Resource.objects.get(id=resid)
    resource_categories = Category.objects.filter(is_active=True)
    context = { 'selected_res': selected_res, 'resource_categories': resource_categories, }
    context.update(_category_schema_context(resource_categories))
    return render(request, 'it_admin/edit_resource_page.html', context)


@login_required(login_url='account:login')
def update_resource(request, resid):
    update_res = Resource.objects.get(id=resid)

    if request.method == 'POST':
        old_availability = update_res.resource_availability
        old_warranty = update_res.warranty_expiry_date

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
        # Parsed to a real date (not left as the raw POST string) so the
        # before/after comparison below isn't comparing a date to a string,
        # which would always read as "changed" even when it wasn't.
        update_res.warranty_expiry_date = parse_date(request.POST.get('warranty_expiry_date') or '')
        update_res.resource_description = request.POST['resource_description']
        update_res.added_by = request.POST['added_by']
        update_res.save()

        summary = f'{request.user} updated {update_res.asset_id}'
        if old_availability != update_res.resource_availability:
            summary += f' (availability: {old_availability} -> {update_res.resource_availability})'
        if old_warranty != update_res.warranty_expiry_date:
            summary += f' (warranty: {old_warranty} -> {update_res.warranty_expiry_date})'
        log_activity(request.user, 'resource_updated', summary, related_resource=update_res)

        message_alert.success(request, 'Resource details of ' + update_res.asset_id + ' was updated successfully!')
    return redirect('resources:resources_listings_page')


@login_required(login_url='account:login')
def resource_deletion_history(request):
    resources = Resource.objects.all().filter(is_active=False)
    context = { 'resources': resources, }
    return render(request, 'it_admin/resource_deletion_history.html', context)


@login_required(login_url='account:login')
def restore_device(request, resid):
    restoring_device = Resource.objects.get(id=resid)
    restoring_device.is_active = True
    restoring_device.save()
    log_activity(
        request.user, 'resource_restored',
        f'{request.user} restored {restoring_device.asset_id}',
        related_resource=restoring_device,
    )
    message_alert.success(request, 'Device restored successfully!')
    return redirect('resources:resource_deletion_history')


@login_required(login_url='account:login')
def permanent_delete_device(request, resid):
    delete_device = Resource.objects.get(id=resid)
    # Logged before the delete, not after -- an entry created against an
    # already-deleted PK works silently on SQLite (no FK enforcement) but
    # raises IntegrityError on Postgres.
    log_activity(
        request.user, 'resource_deleted',
        f'{request.user} permanently deleted {delete_device.asset_id}',
        related_resource=delete_device,
    )
    delete_device.delete()
    message_alert.success(request, 'Device permanently deleted successfully!')
    return redirect('resources:resource_deletion_history')


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


@login_required(login_url='account:login')
def resources_listings_page(request):
    resources = Resource.objects.all().filter(is_active=True).order_by('resource_availability')
    res_count = resources.count()
    context = { 'resources': resources, 'res_count': res_count, }
    return render(request, 'it_admin/resources_listings_page.html', context)


@login_required(login_url='account:login')
def expiring_resources_page(request):
    today = date.today()
    alert_cutoff = today + timedelta(days=WARRANTY_ALERT_WINDOW_DAYS)
    expiring_qs = Resource.objects.filter(
        is_active=True, warranty_expiry_date__isnull=False, warranty_expiry_date__lte=alert_cutoff
    ).order_by('warranty_expiry_date')
    expired_resources = [r for r in expiring_qs if r.warranty_expiry_date < today]
    expiring_soon_resources = [r for r in expiring_qs if r.warranty_expiry_date >= today]
    context = { 'expired_resources': expired_resources, 'expiring_soon_resources': expiring_soon_resources, }
    return render(request, 'it_admin/expiring_resources_page.html', context)


@login_required(login_url='account:login')
def view_resource(request, resid):
    selected_res = Resource.objects.get(id=resid)
    activity_entries = ActivityEntry.objects.filter(related_resource=selected_res)[:50]
    context = { 'selected_res': selected_res, 'activity_entries': activity_entries, }
    return render(request, 'it_admin/view_resource_page.html', context)


@login_required(login_url='account:login')
def resource_qr_image(request, resid):
    resource = Resource.objects.get(id=resid)
    # Encodes the absolute scan-action URL (not just the resource detail
    # page) so scanning with any phone's stock camera app -- not just an
    # in-app scanner -- lands directly on the check-in/out action with zero
    # extra taps.
    scan_url = request.build_absolute_uri(reverse('resources:scan_resource', args=[resource.asset_id]))
    img = qrcode.make(scan_url)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


@login_required(login_url='account:login')
def print_resource_label(request, resid):
    resource = Resource.objects.get(id=resid)
    return render(request, 'it_admin/print_resource_label.html', {'resource': resource})


@login_required(login_url='account:login')
def scan_resource(request, asset_id):
    """Router landed on after scanning a resource's QR tag. Deliberately
    reuses the existing ticket-driven complete_processing_request/
    mark_returned views rather than a standalone ad-hoc issue/return path,
    so every resource hand-off still traces back to a Ticket -- scanning
    just removes the manual asset-id typing/lookup step at either end.
    """
    from tickets.models import Ticket

    try:
        resource = Resource.objects.get(asset_id=asset_id, is_active=True)
    except Resource.DoesNotExist:
        return render(request, 'it_admin/scan_resource_readonly.html', {'resource': None, 'asset_id': asset_id})

    if resource.resource_availability == 'Available':
        matching_tickets = Ticket.objects.filter(
            is_active=True, request_status='Processing', requested_category=resource.resource_category,
        ).exclude(request_category='Support')
        return render(request, 'it_admin/scan_pick_ticket.html', {
            'resource': resource, 'matching_tickets': matching_tickets,
        })
    elif resource.resource_availability == 'Taken':
        resource_taken = ResourceTaken.objects.filter(
            asset_id=resource, resource_status='Taken', is_active=True).first()
        return render(request, 'it_admin/scan_return_confirm.html', {
            'resource': resource, 'resource_taken': resource_taken,
        })
    else:
        return render(request, 'it_admin/scan_resource_readonly.html', {'resource': resource, 'asset_id': asset_id})


@login_required(login_url='account:login')
def scan_camera_page(request):
    return render(request, 'it_admin/scan_camera.html')


@login_required(login_url='account:login')
def view_resource_categories(request):
    all_categories = Category.objects.all()
    category_count = all_categories.count()
    context = { 'all_categories': all_categories, 'category_count': category_count, }
    return render(request, 'it_admin/view_categories_page.html', context)


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


@login_required(login_url='account:login')
def edit_category_page(request, catid):
    get_cat = Category.objects.get(id=catid)
    context = { 'get_cat': get_cat, }
    return render(request, 'it_admin/edit_category_page.html', context)


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


@login_required(login_url='account:login')
def delete_category_warning(request, delcatid):
    get_cat = Category.objects.get(id=delcatid)
    context = { 'get_cat': get_cat, }
    return render(request, 'it_admin/warning_page.html', context)


@login_required(login_url='account:login')
def delete_resource(request, resid):
    if request.method == 'POST':
        delete_name = request.POST['delete_name']
        if delete_name == 'delete':
            deleting_res = Resource.objects.get(id=resid)
            # Logged before the delete -- see permanent_delete_device's comment above.
            log_activity(
                request.user, 'resource_deleted',
                f'{request.user} deleted {deleting_res.asset_id}',
                related_resource=deleting_res,
            )
            deleting_res.delete()
            message_alert.success(request, deleting_res.asset_id + ' - Resource was deleted successfully!')
    return redirect('resources:resources_listings_page')

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


@login_required(login_url='account:login')
def manager_returned_resources_list_table(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Returned', manager_peoplesoft_id=get_user_psid)
    context = { 'resources': resources, }
    return render(request, 'manager/view_returns_page.html', context)


@login_required(login_url='account:login')
def manager_taken_resources_list_table(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    resources = ResourceTaken.objects.all().filter(is_active=True, resource_status='Taken', manager_peoplesoft_id=get_user_psid)
    context = { 'resources': resources, }
    return render(request, 'manager/view_taken_page.html', context)


@login_required(login_url='account:login')
def employee_taken_resources_list_table(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    employee = account.employee_profile
    resources = ResourceTaken.objects.filter(
        is_active=True, resource_status='Taken', peoplesoft_id=employee) if employee else ResourceTaken.objects.none()
    context = { 'resources': resources, }
    return render(request, 'employee/my_resources.html', context)


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
