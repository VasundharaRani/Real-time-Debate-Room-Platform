from django.urls import path
from . import views #to access views.py from the current directory

urlpatterns = [
    path('create/',views.create_debate_room, name="create_debate_room")
]
