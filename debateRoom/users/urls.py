from django.urls import path
from . import views #to access views.py from the current directory

urlpatterns = [
    path("",views.login_view,name="login"),
    path("logout/",views.logout_view,name="logout"),
    path("register/",views.register_view,name="register")
]
