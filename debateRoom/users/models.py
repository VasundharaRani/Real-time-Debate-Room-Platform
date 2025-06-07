from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("moderator","Moderator"),
        ("debator","Debator"),
        ("audience","Audience")
    ]

    # user = models.OnetoOneField(user, on_delete=CASCADE)
    role = models.CharField(max_length=64, choices = ROLE_CHOICES, default='audience')
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username}"