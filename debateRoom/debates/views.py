from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Min
from .models import DebateRoom, RoomParticipant
from .forms import DebateRoomForm
from django.contrib import messages

User = get_user_model()

# Create your views here.
@login_required
def dashboard(request):
    # get all rooms where this user is a participant
    my_participations = RoomParticipant.objects.select_related('room').filter(user=request.user)
    
    upcoming_rooms = my_participations.filter(room__is_live = True)
    past_rooms = my_participations.filter(room__is_live = False)

    featured_rooms = DebateRoom.objects.filter(is_featured = True)
    return render(request, 'debates/dashboard.html',{
        'upcoming_rooms': upcoming_rooms,
        'past_rooms' : past_rooms,
        'featured_rooms' : featured_rooms,
    })

@login_required
def create_debate_room(request):
    # only moderators can create debate 
    if not request.user.is_approved:
        return HttpResponseForbidden("You are not approved by admin yet.")
    if request.user.role != 'moderator':
        return HttpResponseForbidden("Only moderators can create debate rooms.")
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

@login_required
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

@login_required
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

@login_required
def toggle_room_entry(request,room_id):
    room = get_object_or_404(DebateRoom,id=room_id)

    if request.user != room.created_by and not RoomParticipant.objects.filter(room=room,user=request.user,role='moderator').exists():
        return HttpResponseForbidden("Only the host or moderator can do this")

    room.allow_entry = not room.allow_entry
    room.save()
    return redirect('debate_room_detail',room_id=room.id)

@login_required
def debate_room_list(request):
    now = timezone.now()
    
    live_rooms = DebateRoom.objects.filter(is_private=False,is_live=True).order_by('start_time')
    upcoming_rooms = DebateRoom.objects.filter(is_private = False,is_live=False).order_by('start_time')
    
    return render(request,'debates/room_list.html',{
        'live_rooms' : live_rooms,
        'upcoming_rooms' : upcoming_rooms
    })

@login_required
def start_debate(request,room_id):
    room = get_object_or_404(DebateRoom, id = room_id)

    # only moderator or creator can start the debate
    if request.user != room.created_by and not RoomParticipant.objects.filter(room=room, user=request.user,role="moderator").exists():
        return HttpResponseForbidden("Only the moderator or creator can start the debate")

    if room.is_live:
        messages.info(request,"Debate is already live")
    else:
        room.is_live = True
        room.start_time = timezone.now()
        room.save()
        messages.success(request,"Debate started successfully.")

    return redirect("debate_room_detail",room_id=room.id)