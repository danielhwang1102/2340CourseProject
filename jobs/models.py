from django.db import models
from django.conf import settings
from django.urls import reverse
from companies.models import Company
from profiles.models import Skill

class Job(models.Model):
    JOB_TYPE = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    )
    LOCATION_TYPE = (
        ('remote', 'Remote'),
        ('onsite', 'On-Site'),
        ('hybrid', 'Hybrid'),
    )
    EXPERIENCE_LEVEL = (
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('lead', 'Lead/Principal'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(help_text="Job requirements and qualifications")
    
    # Company can be either a Company object or just a string for flexibility
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    company_name = models.CharField(max_length=200, help_text="Use if company not in database")
    
    location = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL, default='mid')
    
    # Compensation
    salary_min = models.PositiveIntegerField(blank=True, null=True)
    salary_max = models.PositiveIntegerField(blank=True, null=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    
    # Skills and Benefits
    required_skills = models.ManyToManyField(Skill, blank=True, related_name='jobs_requiring_skill')
    benefits = models.TextField(blank=True)
    
    # Administrative
    visa_sponsorship = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    application_deadline = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_company_name(self):
        """Return company name whether from Company object or string field"""
        return self.company.name if self.company else self.company_name

    def get_absolute_url(self):
        return reverse('job_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f"{self.title} at {self.get_company_name()}"

    class Meta:
        ordering = ['-created_at']