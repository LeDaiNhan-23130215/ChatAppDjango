from django.shortcuts import render

# Create your views here.
def homepage(request):
    """Trang chủ chính của web"""
    return render(request, "core/home.html")