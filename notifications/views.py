from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Notification


@login_required(login_url='account:login')
def unread_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required(login_url='account:login')
def panel(request):
    notifications = Notification.objects.filter(recipient=request.user)[:15]
    unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
    context = {'notifications': notifications, 'unread_count': unread}
    return render(request, 'notifications/_dropdown_panel.html', context)


@login_required(login_url='account:login')
def open_notification(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    return redirect(notification.link_url or 'notifications:list_page')


@login_required(login_url='account:login')
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now())
    return JsonResponse({'ok': True})


@login_required(login_url='account:login')
def list_page(request):
    notification_list = Notification.objects.filter(recipient=request.user)
    paginator = Paginator(notification_list, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'notifications/list_page.html', {'page_obj': page_obj})
