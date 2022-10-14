from django.urls import path
from .import views


urlpatterns = [
    path('add_member/', views.add_member, name='add_member'),
    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('view_team_members/<int:userid>/', views.view_team_members, name='view_team_members'),
    path('manager_notes_page/', views.manager_notes_page, name='manager_notes_page'),
    # path('view_team_members_details/', views.view_team_members_details, name='view_team_members_details'),
    path('search_team_member/<int:userid>/', views.search_team_member, name='search_team_member'),
    path('view_team_members_details/<int:memid>/', views.view_team_members_details, name='view_team_members_details'),
    path('edit_team_member/<int:memid>/', views.edit_team_member, name='edit_team_member'),
    path('update_team_member/<int:memid>/', views.update_team_member, name='update_team_member'),
    path('allocate_device/<int:memid>/', views.allocate_device, name='allocate_device'),
    path('add_other_accessories/<int:memid>/', views.add_other_accessories, name='add_other_accessories'),
    path('edit_other_accessories/<int:memid>/', views.edit_other_accessories, name='edit_other_accessories'),
    path('update_other_accessories/<int:memid>/', views.update_other_accessories, name='update_other_accessories'),
    #path('edit_department/<int:depid>/', views.edit_department, name='edit_department'),
    #path('back_to_team_view/<int:temid>/', views.back_to_team_view, name='back_to_team_view'),
]