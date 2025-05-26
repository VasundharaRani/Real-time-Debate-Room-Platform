from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import DebateRoom, RoomParticipant
from .forms import DebateRoomForm

# Create your views here.
def create_debate_room(request):
    if request.POST == 'POST':
        form = DebateRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit = False)