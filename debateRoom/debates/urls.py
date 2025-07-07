from django.urls import path
from . import views #to access views.py from the current directory

urlpatterns = [
    path('dashboard/',views.dashboard, name="dashboard"),
    path('create/',views.create_debate_room, name="create_debate_room"),
    path('room/',views.debate_room_list,name="debate_room_list"),
    path('room/<int:room_id>/',views.debate_room_detail,name="debate_room_detail"),
    path('room/<int:room_id>/assign-roles/',views.assign_roles,name="assign_roles"),
    path('room/<int:room_id>/start/',views.start_debate, name="start_debate"),
    path('room/<int:room_id>/toogle-entry/',views.toggle_room_entry,name="toggle_room_entry"),
    path('room/<int:room_id>/vote/', views.submit_vote, name='submit_vote'),
    path('room/<int:room_id>/vote-stats/', views.vote_stats, name='vote_stats'),
    path('debates/<int:room_id>/declare-winner/', views.declare_winner, name='declare_winner'),
    path('debates/auto-declare-winner/<int:room_id>/', views.auto_declare_winner, name='auto_declare_winner'),
    path('moderator/control/<int:room_id>/', views.moderator_control, name='moderator_control')
]
