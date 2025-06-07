from django.contrib import admin
from django.urls import path
from . import views #to access views.py from the current directory
from users.admin import custom_admin_site

urlpatterns = [
    path("",views.landing_page,name="landing_page"),
    path('admin/pending-users/', views.pending_users_view, name="pending_users"),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('registration-pending/', views.registration_pending_view, name='registration_pending'),
    path("logout/",views.logout_view,name="logout"),
    path("register/",views.register_view,name="register")
]
