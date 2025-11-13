from django.db import models
from django.conf import settings
from django.core.validators import URLValidator
from django.urls import reverse

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

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinate (auto-filled from map)"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinate (auto-filled from map)"
    )

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
    
    # ADD THESE NEW PRIVACY FIELDS
    show_email = models.BooleanField(
        default=True, 
        verbose_name="Show Email to Recruiters",
        help_text="Allow recruiters to see your email address"
    )
    show_phone = models.BooleanField(
        default=True,
        verbose_name="Show Phone Number",
        help_text="Display your phone number on your profile (if provided)"
    )
    show_location = models.BooleanField(
        default=True,
        verbose_name="Show Location",
        help_text="Display your location to recruiters"
    )
    show_experience = models.BooleanField(
        default=True,
        verbose_name="Show Work Experience",
        help_text="Display your work history and current position"
    )
    show_education = models.BooleanField(
        default=True,
        verbose_name="Show Education",
        help_text="Display your educational background"
    )
    show_skills = models.BooleanField(
        default=True,
        verbose_name="Show Skills",
        help_text="Display your skills to recruiters"
    )
    show_links = models.BooleanField(
        default=True,
        verbose_name="Show External Links",
        help_text="Display your website, LinkedIn, and GitHub links"
    )
    show_certifications = models.BooleanField(
        default=True,
        verbose_name="Show Certifications",
        help_text="Display your professional certifications"
    )
    show_resume = models.BooleanField(
        default=True,
        verbose_name="Show Resume Download",
        help_text="Allow recruiters to download your resume"
    )
    
    # Preferences
    open_to_work = models.BooleanField(default=True)
    preferred_salary_min = models.PositiveIntegerField(blank=True, null=True)
    preferred_salary_max = models.PositiveIntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_all_fields(self):
        """
        Returns a dictionary of all field names and their values for this profile.
        Useful for debugging or dynamic display.
        """
        fields = {}
        for field in self._meta.fields:
            value = getattr(self, field.name)
            fields[field.name] = value
        # Add skills (ManyToMany)
        fields['skills'] = [skill.name for skill in self.skills.all()]
        return fields

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def is_complete(self):
        """Check if profile has minimum required information"""
        required_fields = [self.headline, self.bio, self.location]
        return all(field for field in required_fields) and self.skills.exists()

    def get_absolute_url(self):
        """Return URL to view this profile."""
        return reverse('profiles:view_profile_by_username', kwargs={'username': self.user.username})
    
class SavedSearch(models.Model):
    """
    Model to store recruiter's saved candidate searches
    User Story #15: Save candidate search criteria
    """
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='saved_searches',
        limit_choices_to={'user_type': 'recruiter'}
    )
    
    # Search metadata
    name = models.CharField(
        max_length=200,
        help_text="Name for this saved search (e.g., 'Senior Python Developers in Atlanta')"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of what you're looking for"
    )
    
    # Search criteria (stored as JSON)
    search_criteria = models.JSONField(
        help_text="JSON object containing all search filters"
    )
    
    # Notification settings
    notify_on_new_matches = models.BooleanField(
        default=True,
        verbose_name="Email me when new matches appear"
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_match_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Saved Search'
        verbose_name_plural = 'Saved Searches'
    
    def __str__(self):
        return f"{self.name} (by {self.recruiter.username})"
    
    def get_criteria_display(self):
        """Return human-readable version of search criteria"""
        criteria = self.search_criteria
        display = []
        
        if criteria.get('keywords'):
            display.append(f"Keywords: {criteria['keywords']}")
        if criteria.get('location'):
            display.append(f"Location: {criteria['location']}")
        if criteria.get('min_experience'):
            display.append(f"Min Experience: {criteria['min_experience']} years")
        if criteria.get('skills'):
            display.append(f"Skills: {', '.join(criteria['skills'])}")
        if criteria.get('education_keyword'):
            display.append(f"Education: {criteria['education_keyword']}")
        if criteria.get('certification_keyword'):
            display.append(f"Certification: {criteria['certification_keyword']}")
        if criteria.get('open_to_work'):
            display.append("Only open to work")
        
        return '; '.join(display) if display else 'No filters applied'
    
class NewMatchNotification(models.Model):
    """
    Notifications specifically for new candidate matches on saved searches
    User Story #15: Notify recruiters about new candidate matches
    """
    NOTIFICATION_TYPES = (
        ('new_match', 'New Candidate Match'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='new_match_notifications'
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='new_match'
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Link to the saved search results
    link_url = models.CharField(max_length=500, blank=True)
    
    # Reference to the saved search that triggered this notification
    related_saved_search = models.ForeignKey(
        SavedSearch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='match_notifications'
    )
    
    # Tracking
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"New Match Notification for {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_new_match_notification(cls, recruiter, saved_search, new_count, total_count):
        """
        Create a notification for new candidate matches
        """
        return cls.objects.create(
            user=recruiter,
            notification_type='new_match',
            title=f"New candidates match '{saved_search.name}'",
            message=f"{new_count} new candidate(s) match your saved search. You now have {total_count} total matches.",
            link_url=f"/profiles/saved-search/{saved_search.pk}/run/",
            related_saved_search=saved_search
        )
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user"""
        return cls.objects.filter(user=user, is_read=False).count()