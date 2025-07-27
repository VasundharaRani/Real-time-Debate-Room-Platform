from django.contrib.auth import authenticate, login, logout, get_user_model
from django.conf import settings
from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth.views import LoginView
from .models import CustomUser
from .forms import CustomUserCreationForm,CustomAuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache,cache_control
from django.contrib import messages
from .models import LoginApprovalRequest

# Create your views here.
def landing_page(request):
    return render(request,"users/landing.html")
    
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = False
            user.role="audience"
            user.save()
            request.session['pending_user_id'] = user.id  # Save user ID to track status
            return redirect('registration_pending') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@staff_member_required
def pending_users_view(request):
    pending_users = CustomUser.objects.filter(is_approved=False)
    login_requests = LoginApprovalRequest.objects.select_related('user')
    return render(request, 'users/pending_users.html', {
        'pending_users': pending_users,
        'login_requests': login_requests
    })
    
def registration_pending_view(request):
    user_id = request.session.get('pending_user_id')
    context = {}

    if not user_id:
        context['status'] = 'unknown'
    else:
        try:
            user = CustomUser.objects.get(id=user_id)
            if user.is_approved:
                context['status'] = 'approved'
            elif not user.is_active:  # You can use this if denied users are deactivated
                context['status'] = 'denied'
            else:
                context['status'] = 'pending'
        except CustomUser.DoesNotExist:
            context['status'] = 'unknown'

    return render(request, 'users/registration_pending.html', context)

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")  # Redirect if already logged in
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_approved:
            LoginApprovalRequest.objects.get_or_create(user=user)

            messages.error(self.request, "Your account is not approved. Admin has been notified.")
            return redirect('registration_pending')
        login(self.request, user)
        return redirect("dashboard")

def logout_view(request):
    logout(request)
    return redirect("landing_page")