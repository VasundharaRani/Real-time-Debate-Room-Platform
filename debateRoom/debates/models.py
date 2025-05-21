from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL
# Create your models here.
class DebateRoom(models.Model):
    Format_Choice = [
        ('1v1', '1v1'),
        ('panel','panel'),
    ]
    title = models.CharField(max_length = 255)
    description = models.TextField(blank = True)
    topic = models.CharField(max_length=255)
    created_by = models.ForeignKey(User,on_delete = models.CASCADE, related_name = "participants")
    is_private = models.BooleanField(default = True)
    format = models.CharField(max_length=10, choices = Format_Choice,default = "1v1")
    timer_per_round = models.IntegerField(default = 120)
    allow_entry = models.BooleanField(default=True)
    is_live = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "f{self.title} ({self.topic})"

class RoomParticipant(models.Model):
    ROLE_CHOICES = [
        ("moderator","Moderator"),
        ("debator","Debator"),
        ("audience","Audience")
    ]
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    room = models.ForeignKey(DebateRoom, on_delete=models.CASCADE, related_name="participants")
    role = models.CharField(max_length=10,choices = ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_muted = models.BooleanField(default=False)
    is_kicked = models.BooleanField(default = False)


    class Meta:
        unique_together = ('user', 'room')

    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.room.title}"

    
class DebateRound(models.Model):
    room = models.ForeignKey(DebateRoom,on_delete=models.CASCADE, related_name="rounds")
    round_number = models.PositiveIntegerField()
    start_time = models.DateTimeField
    end_time = models.DateTimeField
    current_speaker = models.ForeignKey(User,on_delete=models.SET_NULL, null = True,blank = True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['round_number']

    def __str__self(self):
        return f"Round {self.round_number} in {self.room_title}"