from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from .models import DebateRoom, RoomParticipant
from .forms import DebateRoomForm

User = get_user_model()

# Create your views here.
# @login_required
def create_debate_room(request):
    if request.method == 'POST':
        form = DebateRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit = False)
            room.created_by = request.user
            room.save()
    
            RoomParticipant.objects.create(user = request.user,room = room, role = 'moderator')
            return redirect('assign_roles',room_id = room.id)
    else : 
        form = DebateRoomForm()
    return render(request, 'debates/create_room.html',{'form':form})

def assign_roles(request,room_id):
    room = get_object_or_404(DebateRoom, id=room_id)
    # only moderator can assign roles
    if not RoomParticipant.objects.filter(room=room,user=request.user, role='moderator'):
        return HttpResponseForbidden("Only moderators can assign roles")
    if not room.allow_entry:
        return HttpResponseForbidden("Cannot assign roles after the debate has started")

    if request.method == "POST":
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        user = get_object_or_404(User, id=user_id)
        # To avoid duplicate entries
        participant, created = RoomParticipant.objects.get_or_create(user=user,room=room)
        participant.role = role
        participant.save()

        return redirect('assign_roles',room_id=room.id)

    participants = RoomParticipant.objects.filter(room = room).select_related('user')
    # to get users not in the room
    all_users = User.objects.exclude(id__in = participants.values_list('user_id',flat=True))

    return render(request, 'debates/assign_roles.html', {
        'room': room,
        'participants': participants,
        'all_users': all_users,
    })

def debate_room_detail(request, room_id):
    room = get_object_or_404(DebateRoom, id=room_id)

    # check entry permission
    if not room.allow_entry and not RoomParticipant.objects.filter(user=request.user, room=room).exists():
        return HttpResponseForbidden("Room entry is disabled")

    participants = room.participants.select_related('user')

    # Auto-assign audience role if not already a participant
    if not participants.filter(user=request.user).exists():
        RoomParticipant.objects.create(user=request.user,room=room,role='audience')

    is_moderator_or_host = (
        request.user == room.created_by or
        RoomParticipant.objects.filter(user=request.user, room=room,role='moderator').exists()
    )

    return render(request, 'debates/room_detail.html',{
        'room' : room,
        'participants' : participants,
        'is_moderator_or_host' : is_moderator_or_host
    })

def toggle_room_entry(request,room_id):
    room = get_object_or_404(DebateRoom,id=room_id)

    if request.user != room.created_by and not RoomParticipant.objects.filter(room=room,user=request.user,role='moderator').exists():
        return HttpResponseForbidden("Only the host or moderator can do this")

    room.allow_entry = not room.allow_entry
    room.save()
    return redirect('debate_room_detail',room_id=room.id)