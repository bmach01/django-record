from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, RegisterForm

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Zalogowany jako {username}")
                return redirect('home')
            else:
                messages.error(request, "Zła nazwa użytkownika lub hasło.")
    else:
        form = LoginForm()
    
    return render(request, 'record_app/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Rejestracja udana! Teraz się zaloguj.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
    
    return render(request, 'record_app/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "Wylogowany pomyślnie.")
    return redirect('login')


@login_required(login_url='login')
def home_view(request):
    return render(request, 'record_app/home.html')
