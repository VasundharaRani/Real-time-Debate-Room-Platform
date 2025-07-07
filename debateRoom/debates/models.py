from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
 

# Create your models here.
class DebateRoom(models.Model):
    Format_Choice = [
        ('1v1', '1v1'),
        ('panel','panel'),
    ]
    title = models.CharField(max_length = 255)
    description = models.TextField(blank = True)
    topic = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete = models.CASCADE, related_name = "participants")
    is_private = models.BooleanField(default = True)
    debate_format = models.CharField(max_length=10, choices = Format_Choice,default = "1v1")
    timer_per_round = models.IntegerField(default = 180)
    allow_entry = models.BooleanField(default=True)
    is_live = models.BooleanField(default = False)
    start_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default = False)
    winner_declared = models.BooleanField(default=False)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='won_debates')

    @property
    def is_debate_over(self):
        if not self.start_time:
            return False
        elapsed = (timezone.now() - self.start_time).total_seconds()
        return elapsed >= self.timer_per_round
        
    def __str__(self):
        return f"{self.title} ({self.topic})"

class RoomParticipant(models.Model):
    ROLE_CHOICES = [
        ("moderator","Moderator"),
        ("debater","Debater"),
        ("audience","Audience")
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE)
    room = models.ForeignKey(DebateRoom, on_delete=models.CASCADE, related_name="participants")
    role = models.CharField(max_length=10,choices = ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_muted = models.BooleanField(default=False)
    is_kicked = models.BooleanField(default = False)


    class Meta:
        unique_together = ('user', 'room')

    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.room.title}"

class Vote(models.Model) :
    room = models.ForeignKey(DebateRoom,on_delete=models.CASCADE,related_name='voters')
    voter = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    voted_for = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='received_votes')

    class Meta:
        unique_together = ('room','voter')
    