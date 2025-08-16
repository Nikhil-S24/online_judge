import re
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def is_valid_password(pwd):
    return len(pwd) >= 8 and re.match(r'^[a-zA-Z0-9]+$', pwd)

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('topics')  

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('topics')  
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('topics')

    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif not is_valid_password(password1):
            messages.error(request, 'Password must be at least 8 characters and alphanumeric.')
        else:
            user = User.objects.create_user(username=username, password=password1, email=email, first_name=name)
            login(request, user)
            messages.success(request, 'Account created and logged in successfully.')
            return redirect('topics')

    return render(request, 'accounts/signup.html')


def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


@login_required
def home(request):
    return redirect('topics') 
