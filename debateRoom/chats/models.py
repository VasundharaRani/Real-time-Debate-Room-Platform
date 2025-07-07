from django.db import models
from django.contrib.auth import get_user_model
from debates.models import DebateRoom

User = get_user_model()

class AudienceMessage(models.Model):
    room = models.ForeignKey(DebateRoom, on_delete=models.CASCADE, related_name='audience_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.message[:20]}'

