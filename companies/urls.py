from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
]
