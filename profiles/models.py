from django.db import models
from django.conf import settings
from django.core.validators import URLValidator

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    headline = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True, validators=[URLValidator()])
    linkedin = models.URLField(blank=True, validators=[URLValidator()])
    github = models.URLField(blank=True, validators=[URLValidator()])
    resume = models.FileField(upload_to='resumes/', blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    
    # Professional Information
    current_position = models.CharField(max_length=200, blank=True)
    years_experience = models.PositiveIntegerField(blank=True, null=True)
    education = models.TextField(blank=True, help_text="Education background")
    certifications = models.TextField(blank=True, help_text="Professional certifications")
    
    # Privacy Settings
    VISIBILITY_CHOICES = (('public', 'Public'), ('private', 'Private'))
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    
    # Preferences
    open_to_work = models.BooleanField(default=True)
    preferred_salary_min = models.PositiveIntegerField(blank=True, null=True)
    preferred_salary_max = models.PositiveIntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def is_complete(self):
        """Check if profile has minimum required information"""
        required_fields = [self.headline, self.bio, self.location]
        return all(field for field in required_fields) and self.skills.exists()