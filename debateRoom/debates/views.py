from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DateTimeField, DurationField, Count
from django.utils import timezone
from django.db.models.functions import Now
from django.db.models.expressions import RawSQL
from django.db import models
from django.db.models import Min
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import DebateRoom, RoomParticipant,Vote
from .forms import DebateRoomForm
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Count
import datetime
import json
User = get_user_model()

# Create your views here.
@login_required
def dashboard(request):
    # get all rooms where this user is a participant
    my_participations = RoomParticipant.objects.select_related('room').filter(user=request.user)
    
    live_rooms = my_participations.filter(room__is_live = True).filter(
        room__start_time__isnull=False  # Not started yet
    )
    upcoming_rooms = my_participations.filter(room__is_live = False).filter(
        room__start_time__isnull=True  # Not started yet
    )
    past_rooms = my_participations.filter(room__is_live = False).exclude(
        room__start_time__isnull=True  # to make sure it's a finished debate
    )

    # Public live rooms (user may not be a participant)
    public_live_rooms = DebateRoom.objects.filter(is_private=False, is_live=True, winner_declared=False)

    featured_rooms = DebateRoom.objects.filter(is_featured = True)
    return render(request, 'debates/dashboard.html',{
        'live_rooms' : live_rooms,
        'upcoming_rooms': upcoming_rooms,
        'past_rooms' : past_rooms,
        'featured_rooms' : featured_rooms,
        'public_live_rooms' : public_live_rooms
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
def assign_roles(request, room_id):
    room = get_object_or_404(DebateRoom, id=room_id)

    # Only moderators can assign roles
    if not RoomParticipant.objects.filter(room=room, user=request.user, role='moderator').exists():
        return HttpResponseForbidden("Only moderators can assign roles")
    
    if not room.allow_entry:
        return HttpResponseForbidden("Cannot assign roles after the debate has started")

    if request.method == "POST":
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        user = get_object_or_404(User, id=user_id)

        if role == "debater":
            debater_count = RoomParticipant.objects.filter(room=room, role='debater').count()

            if room.debate_format == "1v1" and debater_count >= 2:
                messages.error(request, "Cannot assign more than 2 debaters for a 1v1 format.")
                return redirect('assign_roles', room_id=room.id)

            if room.debate_format == "panel" and debater_count >= 5:
                messages.error(request, "Cannot assign more than 5 debaters for a panel format.")
                return redirect('assign_roles', room_id=room.id)


        # Safe to assign
        participant, created = RoomParticipant.objects.get_or_create(user=user, room=room)
        participant.role = role
        participant.save()
        messages.success(request, f"{user.username} assigned as {role}.")
        return redirect('assign_roles', room_id=room.id)

    participants = RoomParticipant.objects.filter(room=room).select_related('user')
    all_users = User.objects.exclude(id__in=participants.values_list('user_id', flat=True))

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
        if not room.is_private and request.user.is_approved:
            RoomParticipant.objects.create(user=request.user,room=room,role='audience')

    is_moderator_or_host = (
        request.user == room.created_by or
        RoomParticipant.objects.filter(user=request.user, room=room,role='moderator').exists()
    )

    debater_ids = participants.filter(role='debater').values_list('user__id', flat=True)
    debaters = User.objects.filter(id__in=debater_ids)
    my_role = participants.filter(user=request.user).first().role


    if room.is_live and room.is_debate_over and not room.winner_declared:
        room.is_live = False
        room.winner_declared = True

        # Auto-declare winner
        top_vote = Vote.objects.filter(room=room).values('voted_for') \
                        .annotate(count=Count('id')).order_by('-count').first()
        if top_vote:
            winner_user = get_object_or_404(User, id=top_vote['voted_for'])
            room.winner = winner_user
        room.save()


    return render(request, 'debates/room_detail.html',{
        'room' : room,
        'participants' : participants,
        'is_moderator_or_host' : is_moderator_or_host,
        'debater_ids' : debater_ids,
        'debaters' : debaters,
        'my_role' : my_role,
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

    # LIVE ROOMS with annotated end_time
    live_rooms = DebateRoom.objects.annotate(
        end_time=RawSQL(
            "start_time + (timer_per_round || ' minutes')::interval", []
        )
    ).filter(
        is_private=False,
        is_live=True,
        start_time__isnull=False,
        end_time__gt=now
    ).order_by('start_time')

    # UPCOMING ROOMS
    upcoming_rooms = DebateRoom.objects.filter(
        is_private=False,
        is_live=False
    ).order_by('start_time')

    return render(request, 'debates/room_list.html', {
        'live_rooms': live_rooms,
        'upcoming_rooms': upcoming_rooms
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

    return redirect('debate_room_detail', room_id=room.id)

@login_required
def submit_vote(request,room_id):
    room = get_object_or_404(DebateRoom,id=room_id)

    if not room.is_live or room.winner_declared:
        return JsonResponse({'error': 'Voting not allowed'}, status=403)

    # Only audience can vote
    try:
        participant = RoomParticipant.objects.get(room=room, user=request.user)
        if participant.role != 'audience':
            return JsonResponse({'error': 'Only audience can vote'}, status=403)
    except RoomParticipant.DoesNotExist:
        return JsonResponse({'error': 'User not in room'}, status=403)

    voted_for_id = request.POST.get('voted_for')
    voted_for = get_object_or_404(User, id=voted_for_id)

    # Save or update vote
    vote, created = Vote.objects.update_or_create(
        room=room,
        voter=request.user,
        defaults={'voted_for': voted_for}
    )

    return JsonResponse({'success': True})

@login_required
def vote_stats(request, room_id):
    room = get_object_or_404(DebateRoom, id=room_id)
    total_votes = Vote.objects.filter(room=room).count()

    vote_counts = Vote.objects.filter(room=room).values('voted_for__username').annotate(count=Count('id'))
    results = []
    for vote in vote_counts:
        percentage = round((vote['count'] / total_votes) * 100) if total_votes else 0
        results.append({
            'name': vote['voted_for__username'],
            'count': vote['count'],
            'percentage': percentage
        })

    winner_name = None
    if room.winner:
        winner_name = room.winner.username
    elif room.winner_declared:
        # Check if tie exists
        grouped_votes = Vote.objects.filter(room=room).values('voted_for', 'voted_for__username').annotate(count=Count('id')).order_by('-count')
        if grouped_votes:
            max_count = grouped_votes[0]['count']
            top_users = [v['voted_for__username'] for v in grouped_votes if v['count'] == max_count]
            if len(top_users) > 1:
                winner_name = "Tie between: " + ", ".join(top_users)

    return JsonResponse({
        'votes': results,
        'winner_name': winner_name
    })

@login_required
def declare_winner(request, room_id):
    room = get_object_or_404(DebateRoom, id=room_id)

    if not RoomParticipant.objects.filter(room=room, user=request.user, role='moderator').exists():
        return HttpResponseForbidden("Only moderators can declare the winner.")

    if not room.is_debate_over:
        return HttpResponseBadRequest("Cannot declare winner before the debate ends.")

    if room.winner_declared:
        return HttpResponseBadRequest("Winner has already been declared.")

    # Count votes
    vote_counts = Vote.objects.filter(room=room).values('voted_for').annotate(count=Count('id'))
    if not vote_counts:
        return HttpResponseBadRequest("No votes to declare winner.")

    max_count = max(v['count'] for v in vote_counts)
    top_voted = [v['voted_for'] for v in vote_counts if v['count'] == max_count]

    if len(top_voted) == 1:
        winner_user = get_object_or_404(User, id=top_voted[0])
        room.winner = winner_user
    else:
        room.winner = None  # Tie: no single winner

    room.winner_declared = True
    room.is_live = False
    room.save()

    return redirect('debate_room_detail', room_id=room.id)

@login_required
@require_POST
def auto_declare_winner(request, room_id):
    room = get_object_or_404(DebateRoom, id=room_id)

    if not room.is_debate_over or room.winner_declared:
        return JsonResponse({'success': False, 'error': 'Cannot declare winner now'}, status=400)

    vote_counts = Vote.objects.filter(room=room) \
        .values('voted_for') \
        .annotate(count=Count('id')) \
        .order_by('-count')

    if not vote_counts:
        return JsonResponse({'success': False, 'error': 'No votes found'})

    top_count = vote_counts[0]['count']
    top_ids = [v['voted_for'] for v in vote_counts if v['count'] == top_count]

    if len(top_ids) > 1:
        tied_users = User.objects.filter(id__in=top_ids)
        tied_usernames = [user.username for user in tied_users]

        room.winner = None
        room.winner_declared = True
        room.is_live = False
        room.save()

        return JsonResponse({'success': True, 'winner_name': f"Tie between: {', '.join(tied_usernames)}"})

    winner_user = get_object_or_404(User, id=top_ids[0])
    room.winner = winner_user
    room.winner_declared = True
    room.is_live = False
    room.save()

    response_data = {
    'votes': results,
    }

    if room.winner:
        response_data["winner_name"] = room.winner.username
    elif room.winner_declared:
        # Check if tie was declared
        top_votes = Vote.objects.filter(room=room).values('voted_for').annotate(count=Count('id')).order_by('-count')
        if top_votes:
            top_count = top_votes[0]['count']
            top_ids = [v['voted_for'] for v in top_votes if v['count'] == top_count]
            if len(top_ids) > 1:
                tied_users = User.objects.filter(id__in=top_ids)
                response_data["winner_name"] = "Tie between: " + ", ".join(user.username for user in tied_users)

    return JsonResponse(response_data)


def moderator_control(request):
    if request.method == "POST":
        data = json.loads(request.body)
        action = data.get("action")
        target_user_id = str(data.get("target_user_id"))
        room_id = str(data.get("room_id"))

        # Send WebSocket control message
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"debate_room_{room_id}",
            {
                "type": "moderator-control",
                "action": action,
                "target_user_id": target_user_id,
            }
        )

        return JsonResponse({"success": True, "message": f"{action.title()} sent to user {target_user_id}."})

@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'debates/room_detail.html', {
        'room': room,
        'username': request.user.username
    })