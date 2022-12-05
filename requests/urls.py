from django.urls import path
from .import views


urlpatterns = [
    path('list_requests_manager/<int:userid>/', views.list_requests_manager, name='list_requests_manager'),
    path('list_completed_requests_manager/<int:userid>/', views.list_completed_requests_manager, name='list_completed_requests_manager'),
    path('create_request/', views.create_request, name='create_request'),
    path('view_selected_request/<int:reqid>/', views.view_selected_request, name='view_selected_request'),
    path('view_manager_completed_request/<int:reqid>/', views.view_manager_completed_request, name='view_manager_completed_request'),
    path('manager_requests_date_sort/<int:userid>/', views.manager_requests_date_sort, name='manager_requests_date_sort'),
    path('cancel_request/<int:reqid>/<int:userid>/', views.cancel_request, name='cancel_request'),
    path('delete_request/<int:reqid>/<int:userid>/', views.delete_request, name='delete_request'),
    path('list_pending_requests_it_admin/<int:userid>/', views.list_pending_requests_it_admin, name='list_pending_requests_it_admin'),
    path('list_processing_requests_it_admin/<int:userid>/', views.list_processing_requests_it_admin, name='list_processing_requests_it_admin'),
    path('list_completed_requests_it_admin/<int:userid>/', views.list_completed_requests_it_admin, name='list_completed_requests_it_admin'),
    path('view_selected_request_it_admin/<int:reqid>/', views.view_selected_request_it_admin, name='view_selected_request_it_admin'),
    path('approve_processing_request/<int:reqid>/<int:userid>/', views.approve_processing_request, name='approve_processing_request'),
    path('view_selected_processing_request/<int:reqid>/', views.view_selected_processing_request, name='view_selected_processing_request'),
    path('view_selected_completed_request/<int:reqid>/', views.view_selected_completed_request, name='view_selected_completed_request'),
    path('complete_processing_request/<int:reqid>/<int:userid>/', views.complete_processing_request, name='complete_processing_request'),
    path('it_admin_completed_requests_date_sort/<int:userid>/', views.it_admin_completed_requests_date_sort, name='it_admin_completed_requests_date_sort'),
]