from django.urls import path
from .import views


urlpatterns = [
    #path('register_superadmin/', views.register_superadmin, name='register_superadmin'),
    path('', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    #path('home', views.home, name='home'),
    path('superadmin_portal', views.superadmin_portal, name='superadmin_portal'),
    path('superadmin_add_user', views.superadmin_add_user, name='superadmin_add_user'),
    path('it_admin_portal', views.it_admin_portal, name='it_admin_portal'),
    path('manager_portal', views.manager_portal, name='manager_portal'),
]