from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('job_seeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='job_seeker')
    email_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.user_type not in dict(self.USER_TYPE_CHOICES):
            raise ValidationError({'user_type': 'Invalid user type selected.'})

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"