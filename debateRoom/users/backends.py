from django.contrib.auth.backends import ModelBackend

class ApprovedUserBackend(ModelBackend):
    def user_can_authenticate(self, user):
        # Default checks: is_active
        is_active = super().user_can_authenticate(user)
        return is_active and user.is_approved
