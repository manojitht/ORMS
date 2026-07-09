from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('unread_count/', views.unread_count, name='unread_count'),
    path('panel/', views.panel, name='panel'),
    path('open/<int:notif_id>/', views.open_notification, name='open'),
    path('mark_all_read/', views.mark_all_read, name='mark_all_read'),
    path('', views.list_page, name='list_page'),
]
