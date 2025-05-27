from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import DebateRoom, RoomParticipant
from .forms import DebateRoomForm

# Create your views here.
# @login_required
def create_debate_room(request):
    if request.POST == 'POST':
        form = DebateRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit = False)
            room.created_by = request.user
            room.save()
            RoomParticipant.objects.create(user = request.user,room = room, role = moderator)
            return redirect('debate_room_detail',room_id = room.id)
    else : 
        form = DebateRoomForm()
    return render(request, 'debates/create_room.html',{'form':form})