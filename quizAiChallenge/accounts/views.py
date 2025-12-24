from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import CompleteProfileForm

User = get_user_model()

def login_view(req):
    if req.method == 'POST':
        username = req.POST.get('username')
        password = req.POST.get('password')

        user = authenticate(req, username=username, password=password)
        if user:
            login(req, user)
            if not user.is_profile_completed():
                return redirect('complete-profile')
            return redirect('homepage')
        else:
            messages.error(req, 'Sai tài khoản hoặc mật khẩu')

    return render(req, 'accounts/login.html')


def register_view(req):
    if req.method == 'POST':
        username = req.POST.get('username')
        email = req.POST.get('email')
        password = req.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(req, 'Username đã tồn tại')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            login(req, user)
            return redirect('homepage')

    return render(req, 'accounts/register.html')

def logout_view(req):
    logout(req)
    return redirect('login')

def homepage(request):
    """Trang chủ chính của web"""
    return render(request, "accounts/home.html")

@login_required
def complete_view(req):
    if req.method == 'POST':
        form = CompleteProfileForm(req.POST, instance=req.user)
        if form.is_valid():
            form.save()
            return redirect('homepage')
    else:
        form = CompleteProfileForm(instance=req.user)

    return render(req, 'accounts/complete_profile.html', {'form': form})
