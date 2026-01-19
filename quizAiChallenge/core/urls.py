from django.urls import path
from .views import homepage, public_home, root_redirect

urlpatterns = [
    path('', root_redirect),
    path('home/', homepage, name='homepage'),
    path('welcome/', public_home, name='public-home'),
]