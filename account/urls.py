from django.urls import path
from .import views


urlpatterns = [
    #path('register_superadmin/', views.register_superadmin, name='register_superadmin'),
    path('login_page', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    #path('home', views.home, name='home'),
    path('superadmin_portal', views.superadmin_portal, name='superadmin_portal'),
    path('superadmin_add_user', views.superadmin_add_user, name='superadmin_add_user'),
    path('add_user_page', views.add_user_page, name='add_user_page'),
    path('view_user_details/<int:uid>/', views.view_user_details, name='view_user_details'),
    path('edit_user/<int:uid>/', views.edit_user, name='edit_user'),
    path('update_user/<int:uid>/', views.update_user, name='update_user'),
    path('remove_user_access/<int:uid>/', views.remove_user_access, name='remove_user_access'),
    path('restore_user/<int:uid>/', views.restore_user, name='restore_user'),
    path('permanent_delete_user/<int:uid>/', views.permanent_delete_user, name='permanent_delete_user'),
    path('it_admin_portal/<int:userid>/', views.it_admin_portal, name='it_admin_portal'),
    path('manager_portal/<int:userid>/', views.manager_portal, name='manager_portal'),
    path('superadmin_users_date_sort/', views.superadmin_users_date_sort, name='superadmin_users_date_sort'),
    path('users_deletion_history/', views.users_deletion_history, name='users_deletion_history'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('reset_password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('manager_user_profile/<int:userid>/', views.manager_user_profile, name='manager_user_profile'),
    path('manager_edit_user_profile/', views.manager_edit_user_profile, name='manager_edit_user_profile'),
    path('manager_update_user_profile/<int:userid>/', views.manager_update_user_profile, name='manager_update_user_profile'),
    path('it_admin_user_profile/<int:userid>/', views.it_admin_user_profile, name='it_admin_user_profile'),
    path('it_admin_edit_user_profile/', views.it_admin_edit_user_profile, name='it_admin_edit_user_profile'),
    path('it_admin_update_user_profile/<int:userid>/', views.it_admin_update_user_profile, name='it_admin_update_user_profile'),
    path('superadmin_user_profile/', views.superadmin_user_profile, name='superadmin_user_profile'),
    path('superadmin_edit_user_profile/', views.superadmin_edit_user_profile, name='superadmin_edit_user_profile'),
    path('superadmin_update_user_profile/<int:userid>/', views.superadmin_update_user_profile, name='superadmin_update_user_profile'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password_activity/', views.reset_password_activity, name='reset_password_activity'),


    path('load_teams/', views.load_teams, name='ajax_load_teams'),
]