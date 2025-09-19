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

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('JPY', 'Japanese Yen (¥)'),
    ]
    
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
    salary_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
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

    def get_job_type_display(self):
        """Return human-readable job type"""
        return dict(self.JOB_TYPE).get(self.job_type, self.job_type.title())

    def get_location_type_display(self):
        """Return human-readable location type"""
        return dict(self.LOCATION_TYPE).get(self.location_type, self.location_type.title())

    def get_experience_level_display(self):
        """Return human-readable experience level"""
        return dict(self.EXPERIENCE_LEVEL).get(self.experience_level, self.experience_level.title())
    
    def get_salary_display(self):
        """Return formatted salary with currency symbol"""
        if self.salary_min and self.salary_max:
            currency_symbols = {
                'USD': '$',
                'EUR': '€',
                'GBP': '£',
                'CAD': 'C$',
                'AUD': 'A$',
                'JPY': '¥',
            }
            symbol = currency_symbols.get(self.salary_currency, self.salary_currency)
            return f"{symbol}{self.salary_min:,} - {symbol}{self.salary_max:,}"
        return "Salary not specified"

    def get_currency_symbol(self):
        """Return currency symbol"""
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'CAD': 'C$',
            'AUD': 'A$',
            'JPY': '¥',
        }
        return currency_symbols.get(self.salary_currency, self.salary_currency)