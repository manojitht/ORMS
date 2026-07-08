from django.shortcuts import render
from django.contrib import messages as message_alert
from django.shortcuts import redirect
from employees.models import Employee
from resources.models import Resource, ResourceTaken, Category
from department.models import Department
from account.models import Account
from tickets.models import Ticket
from team.models import Team
from django.utils import timezone
import random
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from sukhra.csv_utils import csv_response


def _send_ticket_email(subject, template_name, context, recipient_list):
    """Send a ticket-lifecycle notification with both a plain-text part (the
    existing account/<template_name> template) and a styled HTML part (its
    account/emails/<template_name> sibling) so real mail clients render the
    designed version while still degrading gracefully.
    """
    text_body = render_to_string(f'account/{template_name}', context)
    html_body = render_to_string(f'account/emails/{template_name}', context)
    email = EmailMultiAlternatives(subject, text_body, settings.EMAIL_HOST_USER, recipient_list)
    email.attach_alternative(html_body, 'text/html')
    email.send()

@login_required(login_url='account:login')
def list_requests_manager(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_requests_pending = Ticket.objects.all().filter(created_ps_id=get_user_psid, request_status='Pending', is_active=True).order_by('-id')
    get_requests_processing = Ticket.objects.all().filter(created_ps_id=get_user_psid, request_status='Processing', is_active=True).order_by('-id')
    context = { 'get_requests_pending': get_requests_pending, 'get_requests_processing': get_requests_processing, }
    return render(request, 'manager/view_requests_page.html', context)


@login_required(login_url='account:login')
def list_completed_requests_manager(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_requests_completed = Ticket.objects.all().filter(created_ps_id=get_user_psid, request_status='Completed', is_active=True).order_by('-id')
    context = { 'get_requests_completed': get_requests_completed, }
    return render(request, 'manager/view_requests_completed_page.html', context)


@login_required(login_url='account:login')
def export_manager_completed_requests_csv(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    tickets = Ticket.objects.filter(created_ps_id=get_user_id, request_status='Completed', is_active=True).order_by('-id')
    rows = (
        (t.request_id, t.resource_label, t.request_category, t.created_for, t.request_status, t.completed_on)
        for t in tickets
    )
    return csv_response('completed_requests.csv',
        ('Request Id', 'Resource', 'Category', 'Created For', 'Status', 'Completed On'), rows)


@login_required(login_url='account:login')
def create_request(request, userid):

    request_resource_list = Category.objects.filter(is_active=True)

    if request.method == 'POST':
        request_id = request.POST['request_id']
        created_for = request.POST['created_for']
        request_category = request.POST['request_category']
        request_decription = request.POST['request_decription']
        created_by = request.POST['created_by']
        created_ps_id = request.POST['created_ps_id']
        department = request.POST['department']
        team = request.POST['team']
        request_status = request.POST['request_status']
        request_response = request.POST['request_response']
        assigned_to = request.POST['assigned_to']
        manager_email = request.POST['manager_email']
        it_admin_email = request.POST['it_admin_email']
        it_admin_firstname = request.POST['it_admin_firstname']
        it_admin_lastname = request.POST['it_admin_lastname']

        if Employee.objects.filter(peoplesoft_id=created_for, manager_peoplesoft_id=created_ps_id, is_active=True).exists():
            get_team_member_email = Employee.objects.get(peoplesoft_id=created_for)
            team_member_email = get_team_member_email.email
        else:
            team_member_email = None

        if request_category == '--choose category--':
            message_alert.info(request, 'Please choose the request category!')
        elif not Employee.objects.filter(peoplesoft_id=created_for, manager_peoplesoft_id=created_ps_id, is_active=True).exists():
            message_alert.info(request, created_for + ' is not your team member, please check!')
        else:
            requested_category = None
            regarding_resource_taken = None

            if request_category == 'Support':
                regarding_resource_taken_id = request.POST.get('regarding_resource_taken')
                regarding_resource_taken = ResourceTaken.objects.filter(
                    id=regarding_resource_taken_id, peoplesoft_id__peoplesoft_id=created_for,
                    resource_status='Taken', is_active=True,
                ).first()
                if regarding_resource_taken is None:
                    message_alert.info(request, "Please choose one of this employee's currently assigned resources!")
                    return redirect('tickets:create_request', userid)
            else:
                requested_category_id = request.POST.get('requested_category')
                if not requested_category_id:
                    message_alert.info(request, 'Please choose a resource!')
                    return redirect('tickets:create_request', userid)
                requested_category = Category.objects.get(id=requested_category_id)

            ticket = Ticket(request_id=request_id, created_for=Employee.objects.get(peoplesoft_id=created_for),
            created_by=created_by, created_ps_id=created_ps_id, department=Department.objects.get(department_name=department)
            , team=Team.objects.get(team_name=team), requested_category=requested_category,
            regarding_resource_taken=regarding_resource_taken,
            request_category=request_category, request_status=request_status,
            request_decription=request_decription,
            request_response=request_response, assigned_to=assigned_to)
            ticket.save()

            resource_label = ticket.resource_label
            mail_head_subject = 'Request (' + request_id + ') Created For ' + resource_label
            recipient_list = [email for email in (it_admin_email, manager_email, team_member_email) if email]
            _send_ticket_email(mail_head_subject, 'request_creation_email.html', {
                'it_admin_firstname': it_admin_firstname,
                'it_admin_lastname': it_admin_lastname,
                'ticket': ticket,
                'request_id': request_id,
                'created_for': created_for,
                'resource_label': resource_label,
                'request_category': request_category,
                'created_by': created_by,
                'request_status': request_status,
                'department': department,
                'team': team,
            }, recipient_list)
            message_alert.success(request, request_id + ' request is created successfully!')

    generated_request_id = random.randrange(11111111111, 99999999999, 11)
    all_it_admins = list(Account.objects.filter(company=request.user.company, is_it_admin=True, is_active=True))
    assign_admin = random.sample(all_it_admins, 1)[0]
    context = { 'generated_request_id': generated_request_id, 'assign_admin': assign_admin, 'request_resource_list': request_resource_list, }
    return render(request, 'manager/create_request_form.html', context)


@login_required(login_url='account:login')
def view_selected_request(request, reqid):
    get_request_id = Ticket.objects.get(id=reqid)
    get_member_info = Employee.objects.get(peoplesoft_id=get_request_id.created_for)
    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, }
    return render(request, 'manager/open_request_page.html', context)


@login_required(login_url='account:login')
def view_manager_completed_request(request, reqid):
    get_request_id = Ticket.objects.get(id=reqid)
    get_member_info = Employee.objects.get(peoplesoft_id=get_request_id.created_for)
    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, }
    return render(request, 'manager/open_completed_request_manager.html', context)


@login_required(login_url='account:login')
def manager_requests_date_sort(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_result = None
    if request.method == 'POST':
        from_date = request.POST['from_req']
        to_date = request.POST['to_req']
        if from_date != '' and to_date != '':
            get_result =  Ticket.objects.filter(created_ps_id=get_user_psid, request_status='Completed',
            is_active=True).filter(created_on__gte=from_date, created_on__lte=to_date)
        else:
            message_alert.info(request, 'Please select the date fields properly!')

    context = { 'get_result': get_result, 'get_requests_completed': None, }
    return render(request, 'manager/view_requests_completed_page.html', context)


@login_required(login_url='account:login')
def cancel_request(request, reqid, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    try:
        # Scoped to the requesting manager's own tickets -- Ticket.objects is
        # already company-scoped via TenantManager, but that alone doesn't
        # stop one manager from cancelling another manager's ticket by id.
        get_request = Ticket.objects.get(id=reqid, created_ps_id=get_user_id)
    except Ticket.DoesNotExist:
        message_alert.error(request, 'You do not have permission to cancel this request.')
        return redirect('tickets:list_requests_manager', userid)
    get_request.request_status = 'Cancelled'
    resuest_status_r = 'Cancelled'

    mail_head_subject = 'Request (' + get_request.request_id + ') Was Cancelled For ' + get_request.resource_label
    _send_ticket_email(mail_head_subject, 'request_cancellation_manager_email.html', {
        'get_request': get_request,
        'resuest_status_r': resuest_status_r,
    }, [get_request.created_for.email,])
    get_request.save()
    message_alert.success(request, get_request.request_id +  ', was cancelled successfully!')
    return redirect('tickets:list_requests_manager', userid)


@login_required(login_url='account:login')
def delete_request(request, reqid, userid):
    get_request = Ticket.objects.get(id=reqid)
    get_request.is_active = False
    get_request.save()
    message_alert.success(request, get_request.request_id +  ', was deleted successfully!')
    return redirect('tickets:list_requests_manager', userid)


@login_required(login_url='account:login')
def list_pending_requests_it_admin(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_requests = Ticket.objects.all().filter(assigned_to=get_user_psid, request_status='Pending', is_active=True).order_by('-id')
    context = { 'get_requests': get_requests, }
    return render(request, 'it_admin/view_requests_it_admin.html', context)


@login_required(login_url='account:login')
def cancel_request_it_admin(request, reqid, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    try:
        # Scoped to tickets actually assigned to this IT admin -- see
        # cancel_request's comment above for why company-scoping alone
        # (via TenantManager) isn't sufficient here.
        get_request = Ticket.objects.get(id=reqid, assigned_to=get_user_id)
    except Ticket.DoesNotExist:
        message_alert.error(request, 'You do not have permission to cancel this request.')
        return redirect('tickets:list_pending_requests_it_admin', userid)
    get_request.request_status = 'Cancelled'
    resuest_status_r = 'Cancelled'

    mail_head_subject = 'Request (' + get_request.request_id + ') Was Cancelled For ' + get_request.resource_label
    _send_ticket_email(mail_head_subject, 'request_cancellation_it_admin_email.html', {
        'get_request': get_request,
        'resuest_status_r': resuest_status_r,
    }, [get_request.created_for.email,])
    get_request.save()
    message_alert.success(request, get_request.request_id +  ', was cancelled successfully!')
    return redirect('tickets:list_pending_requests_it_admin', userid)


@login_required(login_url='account:login')
def list_processing_requests_it_admin(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_requests = Ticket.objects.all().filter(assigned_to=get_user_psid, request_status='Processing', is_active=True).order_by('-id')
    context = { 'get_requests': get_requests, }
    return render(request, 'it_admin/view_processing_requests_it_admin.html', context)


@login_required(login_url='account:login')
def list_completed_requests_it_admin(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_requests = Ticket.objects.all().filter(assigned_to=get_user_psid, request_status='Completed').order_by('-id')
    context = { 'get_requests': get_requests, }
    return render(request, 'it_admin/view_completed_requests_it_admin.html', context)


@login_required(login_url='account:login')
def export_it_admin_completed_requests_csv(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    tickets = Ticket.objects.filter(assigned_to=get_user_id, request_status='Completed').order_by('-id')
    rows = (
        (t.request_id, t.resource_label, t.request_category, t.created_for, t.request_status, t.completed_on)
        for t in tickets
    )
    return csv_response('completed_requests.csv',
        ('Request Id', 'Resource', 'Category', 'Created For', 'Status', 'Completed On'), rows)


@login_required(login_url='account:login')
def view_selected_request_it_admin(request, reqid):
    get_request_id = Ticket.objects.get(id=reqid)
    get_member_info = Employee.objects.get(peoplesoft_id=get_request_id.created_for)
    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, }
    return render(request, 'it_admin/open_request_it_admin_page.html', context)


@login_required(login_url='account:login')
def approve_processing_request(request, reqid, userid):
    get_request = Ticket.objects.get(id=reqid)
    get_request.request_status = 'Processing'
    get_request.processing_started_on = timezone.now()
    resuest_status_r = 'Processing'

    mail_head_subject = 'Request Was Approved (' + get_request.request_id + ') For ' + get_request.resource_label
    _send_ticket_email(mail_head_subject, 'request_approval_email.html', {
        'get_request': get_request,
        'resuest_status_r': resuest_status_r,
    }, [get_request.created_for.email,])
    get_request.save()

    message_alert.success(request, get_request.request_id +  ', was approved successfully & assigned to your processing requests tab!')
    return redirect('tickets:list_pending_requests_it_admin', userid)


@login_required(login_url='account:login')
def view_selected_processing_request(request, reqid):
    get_request_id = Ticket.objects.get(id=reqid)
    get_member_info = Employee.objects.get(peoplesoft_id=get_request_id.created_for)
    assign_resource = 0

    if get_request_id.request_category == 'Support':
        # Nothing to suggest -- Support tickets resolve against the resource
        # they already reference (regarding_resource_taken), not a fresh pick.
        pass
    else:
        available_resources = list(Resource.objects.filter(
            resource_category=get_request_id.requested_category, resource_availability='Available', is_active=True))
        if available_resources:
            assign_resource = random.sample(available_resources, 1)[0]
        else:
            message_alert.error(request, 'For this request, there is no resource available for this requested resource!')

    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, 'assign_resource': assign_resource, }
    return render(request, 'it_admin/open_processing_request.html', context)


@login_required(login_url='account:login')
def view_selected_completed_request(request, reqid):
    get_request_id = Ticket.objects.get(id=reqid)
    get_member_info = Employee.objects.get(peoplesoft_id=get_request_id.created_for)
    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, }
    return render(request, 'it_admin/open_completed_request.html', context)


@login_required(login_url='account:login')
def complete_processing_request(request, reqid, userid):
    update_req = Ticket.objects.get(id=reqid)
    get_user  = Account.objects.get(id=userid, company=request.user.company)
    get_user_fullname = get_user.first_name + ' ' + get_user.last_name

    if request.method == 'POST':
        update_req.request_response = request.POST['request_response']
        update_req.request_status = 'Completed'
        resuest_status_r = "completed"
        update_req.completed_on = timezone.now()

        if update_req.request_category == 'Support':
            resource_taken = update_req.regarding_resource_taken
            resource = resource_taken.asset_id
            # Populated automatically from the already-assigned resource --
            # no more manually re-typing a credential value at completion time.
            update_req.asset_id = resource.asset_id
            update_req.save()

            resource_attributes = [
                {'label': attr['label'], 'value': resource.attribute_values.get(attr['key'], '')}
                for attr in resource.resource_category.attribute_schema
            ]
            mail_head_subject = 'Request Was Completed (' + update_req.request_id + ') For ' + resource.resource_category.resource_category
            _send_ticket_email(mail_head_subject, 'request_completed_email.html', {
                'update_req': update_req,
                'resuest_status_r': resuest_status_r,
                'resource': resource,
                'resource_attributes': resource_attributes,
            }, [update_req.created_for.email,])
            message_alert.success(request, update_req.request_id + ', was completed successfully!')
        else:
            update_req.asset_id = request.POST['asset_id']
            category = update_req.requested_category

            if not category.tracks_physical_asset:
                # This category doesn't track a physical, asset-id'd unit
                # (e.g. a software-license type category) -- complete
                # without allocating any Resource/ResourceTaken row.
                update_req.save()
                mail_head_subject = 'Request Was Completed (' + update_req.request_id + ') For ' + category.resource_category
                _send_ticket_email(mail_head_subject, 'request_completed_email.html', {
                    'update_req': update_req,
                    'resuest_status_r': resuest_status_r,
                }, [update_req.created_for.email,])
                message_alert.success(request, update_req.request_id + ', was completed successfully!')
            else:
                get_resource = Resource.objects.get(asset_id=update_req.asset_id)

                if get_resource.resource_category_id == category.id and get_resource.resource_availability == 'Available':
                    get_resource.resource_availability = 'Taken'
                    get_resource.save()
                    update_req.save()
                    ResourceTaken.objects.create(
                        asset_id=get_resource, peoplesoft_id=Employee.objects.get(peoplesoft_id=update_req.created_for),
                        department=Department.objects.get(department_name=update_req.department),
                        team=Team.objects.get(team_name=update_req.team), added_by=update_req.created_by,
                        assigned_by=get_user_fullname, resource_status='Taken',
                        manager_peoplesoft_id=update_req.created_ps_id,
                    )

                    mail_head_subject = 'Request Was Completed (' + update_req.request_id + ') For ' + category.resource_category
                    _send_ticket_email(mail_head_subject, 'request_completed_email.html', {
                        'update_req': update_req,
                        'resuest_status_r': resuest_status_r,
                    }, [update_req.created_for.email,])

                    message_alert.success(request, update_req.request_id + ', was completed successfully!')
                else:
                    message_alert.info(request,'OOPS!, ' + get_resource.resource_category.resource_category + ' (' + update_req.asset_id + '), was under '+ get_resource.resource_availability + ' status (or) please check resource correctly!')
                    redirect('tickets:view_selected_processing_request', reqid)

    return redirect('tickets:list_processing_requests_it_admin', userid)


@login_required(login_url='account:login')
def ajax_load_employee_resources(request):
    peoplesoft_id = request.GET.get('peoplesoft_id')
    resources_taken = ResourceTaken.objects.filter(
        peoplesoft_id__peoplesoft_id=peoplesoft_id, resource_status='Taken', is_active=True,
    )
    return render(request, 'manager/employee_resources_dropdownlist_options.html', {'resources_taken': resources_taken})


@login_required(login_url='account:login')
def it_admin_completed_requests_date_sort(request, userid):
    get_user_id = Account.objects.get(id=userid, company=request.user.company)
    get_user_psid = get_user_id
    get_result, from_date, to_date, result_count = None, None, None, 0
    if request.method == 'POST':
        from_date = request.POST['from_req']
        to_date = request.POST['to_req']
        if from_date != '' and to_date != '':
            get_result =  Ticket.objects.filter(assigned_to=get_user_psid, request_status='Completed').filter(completed_on__gte=from_date, completed_on__lte=to_date)
            result_count = get_result.count()
        else:
            message_alert.info(request, 'Please select the date fields properly!')

    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, 'get_requests': None, }
    return render(request, 'it_admin/view_completed_requests_it_admin.html', context)

# Employee self-service requests -- thin, dedicated views mirroring the
# manager equivalents (create_request/list_requests_manager/etc.), matching
# this codebase's existing convention of one view per role for the same
# conceptual action (see cancel_request vs cancel_request_it_admin). Kept
# separate rather than branching inside the manager views so neither path
# risks regressing the other.

@login_required(login_url='account:login')
def create_request_employee(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    employee = account.employee_profile
    request_resource_list = Category.objects.filter(is_active=True)
    own_resources_taken = ResourceTaken.objects.filter(
        peoplesoft_id=employee, resource_status='Taken', is_active=True) if employee else []

    if request.method == 'POST' and employee is not None:
        request_id = request.POST['request_id']
        request_category = request.POST['request_category']
        request_decription = request.POST['request_decription']

        if request_category == '--choose category--':
            message_alert.info(request, 'Please choose the request category!')
        else:
            requested_category = None
            regarding_resource_taken = None

            if request_category == 'Support':
                regarding_resource_taken_id = request.POST.get('regarding_resource_taken')
                regarding_resource_taken = ResourceTaken.objects.filter(
                    id=regarding_resource_taken_id, peoplesoft_id=employee,
                    resource_status='Taken', is_active=True,
                ).first()
                if regarding_resource_taken is None:
                    message_alert.info(request, 'Please choose one of your currently assigned resources!')
                    return redirect('tickets:create_request_employee', userid)
            else:
                requested_category_id = request.POST.get('requested_category')
                if not requested_category_id:
                    message_alert.info(request, 'Please choose a resource!')
                    return redirect('tickets:create_request_employee', userid)
                requested_category = Category.objects.get(id=requested_category_id)

            all_it_admins = list(Account.objects.filter(company=request.user.company, is_it_admin=True, is_active=True))
            assign_admin = random.sample(all_it_admins, 1)[0] if all_it_admins else None

            ticket = Ticket(
                request_id=request_id, created_for=employee, created_by=f'{account.first_name} {account.last_name}',
                created_ps_id=account.peoplesoft_id, department=employee.department, team=employee.team,
                requested_category=requested_category, regarding_resource_taken=regarding_resource_taken,
                request_category=request_category, request_status='Pending Manager Approval',
                request_decription=request_decription,
                assigned_to=assign_admin.peoplesoft_id if assign_admin else '',
            )
            ticket.save()

            manager_account = Account.objects.filter(
                company=request.user.company, peoplesoft_id=employee.manager_peoplesoft_id).first()
            if manager_account and manager_account.email:
                mail_head_subject = f'Approval needed: request ({ticket.request_id}) from {employee.fullname}'
                _send_ticket_email(mail_head_subject, 'request_needs_manager_approval_email.html', {
                    'ticket': ticket, 'manager_account': manager_account,
                }, [manager_account.email])

            message_alert.success(request, f'{request_id} request submitted -- waiting on your manager\'s approval.')
            return redirect('tickets:list_requests_employee', userid)

    generated_request_id = random.randrange(11111111111, 99999999999, 11)
    context = {
        'generated_request_id': generated_request_id,
        'request_resource_list': request_resource_list,
        'own_resources_taken': own_resources_taken,
    }
    return render(request, 'employee/create_request_employee.html', context)


@login_required(login_url='account:login')
def list_requests_employee(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    get_requests_pending = Ticket.objects.filter(
        created_ps_id=account, request_status='Pending Manager Approval', is_active=True).order_by('-id')
    get_requests_processing = Ticket.objects.filter(
        created_ps_id=account, request_status__in=['Pending', 'Processing'], is_active=True).order_by('-id')
    context = { 'get_requests_pending': get_requests_pending, 'get_requests_processing': get_requests_processing, }
    return render(request, 'employee/my_requests.html', context)


@login_required(login_url='account:login')
def list_completed_requests_employee(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    get_requests_completed = Ticket.objects.filter(
        created_ps_id=account, request_status__in=['Completed', 'Cancelled'], is_active=True).order_by('-id')
    context = { 'get_requests_completed': get_requests_completed, }
    return render(request, 'employee/my_requests_completed.html', context)


@login_required(login_url='account:login')
def view_selected_request_employee(request, reqid):
    get_request_id = Ticket.objects.get(id=reqid, created_ps_id=request.user)
    context = { 'get_request_id': get_request_id }
    return render(request, 'employee/open_request_employee.html', context)


@login_required(login_url='account:login')
def cancel_request_employee(request, reqid, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    try:
        get_request = Ticket.objects.get(id=reqid, created_ps_id=account)
    except Ticket.DoesNotExist:
        message_alert.error(request, 'You do not have permission to cancel this request.')
        return redirect('tickets:list_requests_employee', userid)
    get_request.request_status = 'Cancelled'
    get_request.save()
    message_alert.success(request, get_request.request_id + ', was cancelled successfully!')
    return redirect('tickets:list_requests_employee', userid)

# Manager-side approval queue for employee-submitted requests.

@login_required(login_url='account:login')
def list_requests_from_team_manager(request, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    get_requests_awaiting = Ticket.objects.filter(
        created_for__manager_peoplesoft_id=account, request_status='Pending Manager Approval', is_active=True
    ).order_by('-id')
    context = { 'get_requests_awaiting': get_requests_awaiting }
    return render(request, 'manager/view_requests_from_employees.html', context)


@login_required(login_url='account:login')
def approve_employee_request_manager(request, reqid, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    try:
        get_request = Ticket.objects.get(
            id=reqid, request_status='Pending Manager Approval', created_for__manager_peoplesoft_id=account)
    except Ticket.DoesNotExist:
        message_alert.error(request, 'You do not have permission to approve this request.')
        return redirect('tickets:list_requests_from_team_manager', userid)

    get_request.request_status = 'Pending'
    get_request.save()

    employee_account = Account.objects.filter(
        company=request.user.company, employee_profile=get_request.created_for).first()
    if employee_account and employee_account.email:
        mail_head_subject = f'Your manager approved request ({get_request.request_id})'
        _send_ticket_email(mail_head_subject, 'request_manager_decision_email.html', {
            'get_request': get_request, 'decision': 'approved',
        }, [employee_account.email])

    message_alert.success(request, get_request.request_id + ', was approved and sent to IT for processing!')
    return redirect('tickets:list_requests_from_team_manager', userid)


@login_required(login_url='account:login')
def deny_employee_request_manager(request, reqid, userid):
    account = Account.objects.get(id=userid, company=request.user.company)
    try:
        get_request = Ticket.objects.get(
            id=reqid, request_status='Pending Manager Approval', created_for__manager_peoplesoft_id=account)
    except Ticket.DoesNotExist:
        message_alert.error(request, 'You do not have permission to deny this request.')
        return redirect('tickets:list_requests_from_team_manager', userid)

    get_request.request_status = 'Cancelled'
    if request.method == 'POST':
        get_request.request_response = request.POST.get('denial_reason', '')
    get_request.save()

    employee_account = Account.objects.filter(
        company=request.user.company, employee_profile=get_request.created_for).first()
    if employee_account and employee_account.email:
        mail_head_subject = f'Your manager denied request ({get_request.request_id})'
        _send_ticket_email(mail_head_subject, 'request_manager_decision_email.html', {
            'get_request': get_request, 'decision': 'denied',
        }, [employee_account.email])

    message_alert.success(request, get_request.request_id + ', was denied.')
    return redirect('tickets:list_requests_from_team_manager', userid)
