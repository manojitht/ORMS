from django.shortcuts import render
from django.contrib import messages as message_alert, auth
from django.shortcuts import redirect, render
from django.db.models import Q
from members.models import Members
from resource.models import Resource, ResourceTaken, Category
from department.models import Department
from account.models import Account
from requests.models import Requests
from team.models import Team
import os
from datetime import date
import random
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Create your views here.

def list_requests_manager(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    get_requests_pending = Requests.objects.all().filter(created_ps_id=get_user_psid, request_status='Pending', is_active=True).order_by('-id')
    get_requests_processing = Requests.objects.all().filter(created_ps_id=get_user_psid, request_status='Processing', is_active=True).order_by('-id')
    context = { 'get_requests_pending': get_requests_pending, 'get_requests_processing': get_requests_processing, }
    return render(request, 'manager/view_requests_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def list_completed_requests_manager(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    get_requests_completed = Requests.objects.all().filter(created_ps_id=get_user_psid, request_status='Completed', is_active=True).order_by('-id')
    context = { 'get_requests_completed': get_requests_completed, }
    return render(request, 'manager/view_requests_completed_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def create_request(request, userid):

    request_resource_list = Category.objects.all()
    
    if request.method == 'POST':
        request_id = request.POST['request_id']
        created_for = request.POST['created_for']
        request_resource = request.POST['request_resource']
        request_category = request.POST['request_category']
        request_decription = request.POST['request_decription']
        created_by = request.POST['created_by']
        created_ps_id = request.POST['created_ps_id']
        department = request.POST['department']
        team = request.POST['team']
        asset_id = request.POST['asset_id']
        request_status = request.POST['request_status']
        request_response = request.POST['request_response']
        assigned_to = request.POST['assigned_to']
        manager_email = request.POST['manager_email']
        it_admin_email = request.POST['it_admin_email']
        it_admin_firstname = request.POST['it_admin_firstname']
        it_admin_lastname = request.POST['it_admin_lastname']
        get_team_member_email = Members.objects.get(peoplesoft_id=created_for)
        team_member_email = get_team_member_email.email

        
        if request_resource == '--select resource--':
            message_alert.info(request, 'Please choose a resource!')
        elif request_category == '--choose category--':
            message_alert.info(request, 'Please choose the request category!')
        else:
            if Members.objects.filter(peoplesoft_id=created_for, manager_peoplesoft_id=created_ps_id, is_active=True).exists():
                requests = Requests(request_id=request_id, created_for=Members.objects.get(peoplesoft_id=created_for), 
                created_by=created_by, created_ps_id=created_ps_id, department=Department.objects.get(department_name=department)
                , team=Team.objects.get(team_name=team), request_resource=request_resource, 
                asset_id=asset_id, request_category=request_category, request_status=request_status, 
                request_decription=request_decription,
                request_response=request_response, assigned_to=assigned_to)
                
                #send email functionality for request creation
                mail_head_subject = 'Resource Request (' + request_id + ') Created For ' + request_resource + ''
                message = render_to_string('account/request_creation_email.html', {
                    'it_admin_firstname': it_admin_firstname,
                    'it_admin_lastname': it_admin_lastname,
                    'request_id': request_id,
                    'created_for': created_for,
                    'request_resource': request_resource,
                    'request_category': request_category,
                    'created_by': created_by,
                    'request_status': request_status,
                    'department': department,
                    'team': team,
                })
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [it_admin_email,manager_email, team_member_email,]
                send_mail(mail_head_subject, message, email_from, recipient_list)
                requests.save()
                message_alert.success(request, request_id + ' request is created successfully!')
            else:
                message_alert.info(request, created_for + ' is not your team member, please check!')
    
    generated_request_id = random.randrange(11111111111, 99999999999, 11)
    all_it_admins = list(Account.objects.filter(role='IT Administrator', is_active=True))
    assign_admin = random.sample(all_it_admins, 1)[0]
    context = { 'generated_request_id': generated_request_id, 'assign_admin': assign_admin, 'request_resource_list': request_resource_list, }
    return render(request, 'manager/create_request_form.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_selected_request(request, reqid):
    get_request_id = Requests.objects.get(id=reqid)
    get_member_info = Members.objects.get(peoplesoft_id=get_request_id.created_for)
    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, }
    return render(request, 'manager/open_request_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_manager_completed_request(request, reqid):
    get_request_id = Requests.objects.get(id=reqid)
    get_member_info = Members.objects.get(peoplesoft_id=get_request_id.created_for)
    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, }
    return render(request, 'manager/open_completed_request_manager.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def manager_requests_date_sort(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    if request.method == 'POST':
        from_date = request.POST['from_req']
        to_date = request.POST['to_req']
        if from_date != '' and to_date != '':
            get_result =  Requests.objects.filter(created_ps_id=get_user_psid, request_status='Completed', 
            is_active=True).filter(created_on__gte=from_date, created_on__lte=to_date)
        else:
            message_alert.info(request, 'Please select the date fields properly!')

    context = { 'get_result': get_result, }
    return render(request, 'manager/view_requests_completed_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def cancel_request(request, reqid, userid):
    get_request = Requests.objects.get(id=reqid)
    get_request.request_status = 'Cancelled'
    get_request.save()
    message_alert.success(request, get_request.request_id +  ', was cancelled successfully!')
    return redirect(list_requests_manager, userid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def delete_request(request, reqid, userid):
    get_request = Requests.objects.get(id=reqid)
    get_request.is_active = False
    get_request.save()
    message_alert.success(request, get_request.request_id +  ', was deleted successfully!')
    return redirect(list_requests_manager, userid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def list_pending_requests_it_admin(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    get_requests = Requests.objects.all().filter(assigned_to=get_user_psid, request_status='Pending', is_active=True).order_by('-id')
    context = { 'get_requests': get_requests, }
    return render(request, 'it_admin/view_requests_it_admin.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def cancel_request_it_admin(request, reqid, userid):
    get_request = Requests.objects.get(id=reqid)
    get_request.request_status = 'Cancelled'
    get_request.save()
    message_alert.success(request, get_request.request_id +  ', was cancelled successfully!')
    return redirect(list_pending_requests_it_admin, userid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def list_processing_requests_it_admin(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    get_requests = Requests.objects.all().filter(assigned_to=get_user_psid, request_status='Processing', is_active=True).order_by('-id')
    context = { 'get_requests': get_requests, }
    return render(request, 'it_admin/view_processing_requests_it_admin.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def list_completed_requests_it_admin(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    get_requests = Requests.objects.all().filter(assigned_to=get_user_psid, request_status='Completed').order_by('-id')
    context = { 'get_requests': get_requests, }
    return render(request, 'it_admin/view_completed_requests_it_admin.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_selected_request_it_admin(request, reqid):
    get_request_id = Requests.objects.get(id=reqid)
    get_member_info = Members.objects.get(peoplesoft_id=get_request_id.created_for)
    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, }
    return render(request, 'it_admin/open_request_it_admin_page.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def approve_processing_request(request, reqid, userid):
    get_request = Requests.objects.get(id=reqid)
    get_request.request_status = 'Processing'
    resuest_status_r = 'Processing'

    #send email functionality for request approval process
    mail_head_subject = 'Resource Request Was Approved (' + get_request.request_id + ') For ' + get_request.request_resource + ''
    message = render_to_string('account/request_approval_email.html', {
        'get_request': get_request,
        'resuest_status_r': resuest_status_r,
    })
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [get_request.created_for.email,]
    send_mail(mail_head_subject, message, email_from, recipient_list)
    get_request.save()

    message_alert.success(request, get_request.request_id +  ', was approved successfully & assigned to your processing requests tab!')
    return redirect(list_pending_requests_it_admin, userid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_selected_processing_request(request, reqid):
    global assign_resource
    get_request_id = Requests.objects.get(id=reqid)
    get_member_info = Members.objects.get(peoplesoft_id=get_request_id.created_for)
    resource_count = Resource.objects.filter(resource_category=Category.objects.get(resource_category=get_request_id.request_resource), resource_availability='Available', is_active=True)
    if resource_count.count() > 0:
        get_all_resources = list(Resource.objects.filter(resource_category=Category.objects.get(resource_category=get_request_id.request_resource), resource_availability='Available', is_active=True))
        assign_resource = random.sample(get_all_resources, 1)[0]
    else:
        assign_resource = 0
        message_alert.error(request, 'For this request, there is no resource available for this requested resource!')

    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, 'assign_resource': assign_resource, }
    return render(request, 'it_admin/open_processing_request.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def view_selected_completed_request(request, reqid):
    get_request_id = Requests.objects.get(id=reqid)
    get_member_info = Members.objects.get(peoplesoft_id=get_request_id.created_for)
    context = { 'get_request_id': get_request_id, 'get_member_info': get_member_info, }
    return render(request, 'it_admin/open_completed_request.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def complete_processing_request(request, reqid, userid):
    update_req = Requests.objects.get(id=reqid)
    get_user  = Account.objects.get(id=userid)
    get_user_fullname = get_user.first_name + ' ' + get_user.last_name
    
    if request.method == 'POST':
        update_req.asset_id = request.POST['asset_id']
        update_req.request_response = request.POST['request_response']
        update_req.request_status = 'Completed'
        resuest_status_r = "completed"
        update_req.completed_on = date.today()

        if update_req.request_category == 'Bitlocker':
            update_req.save()
            message_alert.success(request, update_req.request_id + ', was completed successfully!')
        else:
            get_resource = Resource.objects.get(asset_id=update_req.asset_id)
            allocate_resource = ResourceTaken(asset_id=Resource.objects.get(asset_id= update_req.asset_id), peoplesoft_id=Members.objects.get(peoplesoft_id= update_req.created_for), resource_category=update_req.request_resource, department=Department.objects.get(department_name=update_req.department),
            team=Team.objects.get(team_name=update_req.team), added_by=update_req.created_by, assigned_by=get_user_fullname,  resource_status='Taken', manager_peoplesoft_id=update_req.created_ps_id)
            # Resource.objects.get(resource_category=get_resource.resource_category)

            if update_req.request_resource == get_resource.resource_category.resource_category and get_resource.resource_availability == 'Available':
                get_resource.resource_availability = 'Taken'
                get_resource.save()
                update_req.save()
                allocate_resource.save()

                #send email functionality for request completion process
                mail_head_subject = 'Resource Request Was Completed (' + update_req.request_id + ') For ' + update_req.request_resource + ''
                message = render_to_string('account/request_completed_email.html', {
                    'update_req': update_req,
                    'resuest_status_r': resuest_status_r,
                })
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [update_req.created_for.email,]
                send_mail(mail_head_subject, message, email_from, recipient_list)

                message_alert.success(request, update_req.request_id + ', was completed successfully!')
            else:
                message_alert.info(request,'OOPS!, ' + get_resource.resource_category.resource_category + ' (' + update_req.asset_id + '), was under '+ get_resource.resource_availability + ' status (or) please check resource correctly!')
                redirect(view_selected_processing_request, reqid)

    return redirect(list_processing_requests_it_admin, userid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def complete_processing_request_bitlocker(request, reqid, userid):
    update_req = Requests.objects.get(id=reqid)  
    
    if request.method == 'POST':
        update_req.asset_id = request.POST['asset_id']
        update_req.request_response = request.POST['request_response']
        update_req.request_status = 'Completed'
        update_req.completed_on = date.today()

        if update_req.request_category == 'Bitlocker':
            update_req.save()
            message_alert.success(request, update_req.request_id + ', was completed successfully!')
        else:
            message_alert.error(request, update_req.request_id + ', Something went wrong on this request!')

    return redirect(list_processing_requests_it_admin, userid)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def it_admin_completed_requests_date_sort(request, userid):
    get_user_id = Account.objects.get(id=userid)
    get_user_psid = Account.objects.get(peoplesoft_id=get_user_id.peoplesoft_id)
    if request.method == 'POST':
        from_date = request.POST['from_req']
        to_date = request.POST['to_req']
        if from_date != '' and to_date != '':
            get_result =  Requests.objects.filter(assigned_to=get_user_psid, request_status='Completed').filter(completed_on__gte=from_date, completed_on__lte=to_date)
            result_count = get_result.count()
        # elif from_date.date < to_date.date:
        #     message_alert.info(request, 'The from date should be greater than to date!')
        else:
            message_alert.info(request, 'Please select the date fields properly!')

    context = { 'get_result': get_result, 'from_date': from_date, 'to_date': to_date, 'result_count': result_count, }
    return render(request, 'it_admin/view_completed_requests_it_admin.html', context)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------