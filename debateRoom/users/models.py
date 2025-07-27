from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("moderator","Moderator"),
        ("debater","Debater"),
        ("audience","Audience")
    ]

    # user = models.OnetoOneField(user, on_delete=CASCADE)
    role = models.CharField(max_length=64, choices = ROLE_CHOICES, default='audience')
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username}"

class LoginApprovalRequest(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Login approval requested for {self.user.username}"