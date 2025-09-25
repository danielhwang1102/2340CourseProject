from django.contrib import admin
from django.utils.html import format_html
from .models import Job
from profiles.models import Skill

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'get_company_name', 
        'location', 
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
        'location',
        'posted_by__username',
        'posted_by__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'application_count']
    
    filter_horizontal = ['required_skills']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'requirements')
        }),
        ('Company & Location', {
            'fields': ('company', 'company_name', 'location', 'location_type')
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
    
    actions = ['activate_jobs', 'deactivate_jobs', 'mark_as_filled']
    
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