from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your models here.
class CustomAdminSite(AdminSite):
    site_header = "Debate Platform Admin"

    def each_context(self, request):
        context = super().each_context(request)
        context['pending_users_count'] = CustomUser.objects.filter(is_approved=False).count()
        return context
    
custom_admin_site = CustomAdminSite(name='custom_admin')

class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_approved","is_staff", "is_active","date_joined") 
    list_filter = ("role", "is_staff","is_active","is_approved")
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    list_editable = ('is_approved','role','is_active') 
custom_admin_site.register(CustomUser, CustomUserAdmin)