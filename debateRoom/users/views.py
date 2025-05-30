from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import CustomUser
from django.views.decorators.cache import never_cache,cache_control


# Create your views here.
@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect("login")
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm = request.POST["confirm"]

        if password != confirm:
            return render(request, "users/register.html", {
                "message" : "Passwords do not match"
            })

        try:
            user = CustomUser.objects.create_user(username = username,email= email,password=password)
            user.save()
        except:
            return render(request, "users/register.html", {
                "message" : "Username is already taken"
            })
        login(request,user)
        return redirect("dashboard")
    return render(request,"users/register.html")

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard") # already logged in
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password = password)
        if user is not None:
            login(request,user)
            return redirect("dashboard")
        else:
            return render(request,"users/login.html", {
                "message" : "Invalid Credentials"
            })
    return render(request,"users/login.html",)

def logout_view(request):
    logout(request)
    return render(request, "users/login.html", {
        "message":"Logged out"
    })