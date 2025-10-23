from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.db.models import Count
import csv
from .models import Job
from profiles.models import Skill

def export_jobs_csv(modeladmin, request, queryset):
    """Export selected jobs to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="jobs.csv"'
    
    writer = csv.writer(response, quoting=csv.QUOTE_ALL)  # ADD quoting parameter
    # Header row
    writer.writerow([
        'Job ID',
        'Title',
        'Company Name',
        'Description',
        'Requirements',
        'Location Type',
        'Street Address',
        'City',
        'State/Province',
        'Country',
        'Postal Code',
        'Job Type',
        'Experience Level',
        'Salary Min',
        'Salary Max',
        'Salary Currency',
        'Required Skills',
        'Benefits',
        'Application Deadline',
        'Visa Sponsorship',
        'Posted By (Username)',
        'Posted By (Email)',
        'Is Active',
        'Created At',
        'Updated At',
        'Total Applications',
        'Latitude',
        'Longitude',
    ])
    
    # Annotate queryset with application count
    queryset = queryset.annotate(app_count=Count('applications'))
    
    # Data rows
    for job in queryset.select_related('posted_by', 'company').prefetch_related('required_skills'):
        skills_list = ', '.join([skill.name for skill in job.required_skills.all()])
        company_name = job.company.name if job.company else job.company_name
        
        # Clean text fields - remove extra quotes and newlines
        description = job.description.replace('\r\n', ' ').replace('\n', ' ').strip() if job.description else ''
        requirements = job.requirements.replace('\r\n', ' ').replace('\n', ' ').strip() if job.requirements else ''
        benefits = job.benefits.replace('\r\n', ' ').replace('\n', ' ').strip() if job.benefits else ''
        
        writer.writerow([
            job.id,
            job.title,
            company_name,
            description,  # Full description, properly escaped
            requirements,  # Full requirements, properly escaped
            job.location_type,
            job.street_address or '',
            job.city or '',
            job.state_province or '',
            job.country or '',
            job.postal_code or '',
            job.job_type,
            job.experience_level,
            job.salary_min or '',
            job.salary_max or '',
            job.salary_currency,
            skills_list,
            benefits,  # Full benefits, properly escaped
            job.application_deadline.strftime('%Y-%m-%d') if job.application_deadline else '',
            'Yes' if job.visa_sponsorship else 'No',
            job.posted_by.username,
            job.posted_by.email,
            'Yes' if job.is_active else 'No',
            job.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            job.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            job.app_count,
            job.latitude or '',
            job.longitude or '',
        ])
    
    return response

export_jobs_csv.short_description = "Export selected jobs to CSV"


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'get_company_name', 
        'get_short_location',
        'job_type', 
        'posted_by', 
        'is_active_status',
        'application_count',
        'created_at'
    ]
    
    list_filter = [
        'is_active', 
        'job_type', 
        'location_type', 
        'experience_level',
        'visa_sponsorship',
        'created_at',
        'posted_by'
    ]
    
    search_fields = [
        'title', 
        'company__name', 
        'company_name', 
        'city',
        'state_province',
        'country',
        'posted_by__username',
        'posted_by__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'application_count', 'latitude', 'longitude']
    
    filter_horizontal = ['required_skills']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'requirements')
        }),
        ('Company & Location', {
            'fields': (
                'company', 
                'company_name', 
                'location_type',
                'street_address',
                'city',
                'state_province',
                'postal_code',
                'country',
                'latitude',
                'longitude'
            )
        }),
        ('Job Details', {
            'fields': ('job_type', 'experience_level', 'required_skills', 'benefits')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'salary_currency')
        }),
        ('Settings', {
            'fields': ('visa_sponsorship', 'is_active', 'application_deadline')
        }),
        ('Administrative', {
            'fields': ('posted_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_jobs', 'deactivate_jobs', 'mark_as_filled', export_jobs_csv]
    
    def get_company_name(self, obj):
        """Display company name with link if available"""
        if obj.company:
            return format_html(
                '<a href="/admin/companies/company/{}/change/">{}</a>',
                obj.company.id,
                obj.company.name
            )
        return obj.company_name or "No Company"
    get_company_name.short_description = "Company"
    get_company_name.admin_order_field = 'company__name'
    
    def get_short_location(self, obj):
        """Display short location format"""
        return obj.get_short_location()
    get_short_location.short_description = "Location"
    
    def is_active_status(self, obj):
        """Show active status with colors"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactive</span>'
        )
    is_active_status.short_description = "Status"
    is_active_status.admin_order_field = 'is_active'
    
    def application_count(self, obj):
        """Show number of applications"""
        count = obj.applications.count()
        if count > 0:
            return format_html(
                '<a href="/admin/applications/application/?job__id__exact={}">{} applications</a>',
                obj.id,
                count
            )
        return "0 applications"
    application_count.short_description = "Applications"
    
    def activate_jobs(self, request, queryset):
        """Bulk action to activate jobs"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} jobs have been activated.'
        )
    activate_jobs.short_description = "Activate selected jobs"
    
    def deactivate_jobs(self, request, queryset):
        """Bulk action to deactivate jobs"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} jobs have been deactivated.'
        )
    deactivate_jobs.short_description = "Deactivate selected jobs"
    
    def mark_as_filled(self, request, queryset):
        """Mark jobs as filled (inactive)"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} jobs have been marked as filled.'
        )
    mark_as_filled.short_description = "Mark as filled (deactivate)"
    
    def get_queryset(self, request):
        """Optimize queryset with related objects"""
        return super().get_queryset(request).select_related(
            'company', 'posted_by'
        ).prefetch_related('applications', 'required_skills')