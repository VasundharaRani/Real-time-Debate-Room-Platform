from django.urls import path
from . import views #to access views.py from the current directory

urlpatterns = [
    path('dashboard/',views.dashboard, name="dashboard"),
    path('create/',views.create_debate_room, name="create_debate_room"),
    path('room/',views.debate_room_list,name="debate_room_list"),
    path('room/<int:room_id>/',views.debate_room_detail,name="debate_room_detail"),
    path('room/<int:room_id>/assign-roles/',views.assign_roles,name="assign_roles"),
    path('room/<int:room_id>/start/',views.start_debate, name="start_debate"),
    path('room/<int:room_id>/toogle-entry/',views.toggle_room_entry,name="toggle_room_entry")
]
