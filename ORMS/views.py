from django.shortcuts import render

def home(request):
    return render(request, 'welcome_page.html')

def login_page(request):
    return render(request, 'account/login.html')