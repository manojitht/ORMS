from django.urls import path
from .import views


urlpatterns = [
    path('add_member/', views.add_member, name='add_member'),
    path('view_team_members/<int:userid>/', views.view_team_members, name='view_team_members'),
    path('manager_notes_page/', views.manager_notes_page, name='manager_notes_page'),
    # path('view_team_members_details/', views.view_team_members_details, name='view_team_members_details'),
    path('search_team_member/<int:userid>/', views.search_team_member, name='search_team_member'),
    path('view_team_members_details/<int:memid>/', views.view_team_members_details, name='view_team_members_details'),
    path('edit_team_member/<int:memid>/', views.edit_team_member, name='edit_team_member'),
    path('update_team_member/<int:memid>/', views.update_team_member, name='update_team_member'),
    # path('allocate_device/<int:memid>/', views.allocate_device, name='allocate_device'),
    path('add_other_notes/<int:memid>/', views.add_other_notes, name='add_other_notes'),
    path('edit_other_notes/<int:memid>/', views.edit_other_notes, name='edit_other_notes'),
    path('update_other_notes/<int:memid>/<int:psid>/', views.update_other_notes, name='update_other_notes'),
    path('view_member_resource_info/<int:memid>/<int:resid>/', views.view_member_resource_info, name='view_member_resource_info'),
    path('mark_returned/<int:resid>/<int:memid>/', views.mark_returned, name='mark_returned'),
    path('view_history_resources/<int:memid>/', views.view_history_resources, name='view_history_resources'),


    path('delete_team_member/<int:memid>/<int:userid>/', views.delete_team_member, name='delete_team_member'),
]