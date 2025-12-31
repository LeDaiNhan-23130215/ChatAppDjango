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

            # kiểm tra profile sau khi login
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

            # bắt buộc hoàn thiện profile sau khi đăng ký
            return redirect('complete-profile')

    return render(req, 'accounts/register.html')

def logout_view(req):
    logout(req)
    return redirect('login')

@login_required
def complete_view(req):
    # nếu profile đã hoàn thiện thì không cho vào lại trang này
    if req.user.is_profile_completed():
        return redirect('homepage')

    if req.method == 'POST':
        form = CompleteProfileForm(req.POST, instance=req.user)
        if form.is_valid():
            form.save()
            return redirect('homepage')
    else:
        form = CompleteProfileForm(instance=req.user)

    return render(req, 'accounts/complete_profile.html', {'form': form})
