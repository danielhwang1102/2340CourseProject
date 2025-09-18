from django.db import models
from django.conf import settings
from jobs.models import Job

class Application(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_completed', 'Interview Completed'),
        ('offer', 'Offer Extended'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True, help_text="Optional cover letter")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    
    # Tracking
    applied_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal notes from recruiter")

    class Meta:
        unique_together = ['job', 'applicant']
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"