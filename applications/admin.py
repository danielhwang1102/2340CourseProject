from django.contrib import admin
from django.utils.html import format_html
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'applicant_name',
        'job_title', 
        'company_name',
        'status_badge',
        'applied_date',
        'last_updated'
    ]
    
    list_filter = [
        'status',
        'applied_date',
        'last_updated',
        'job__job_type',
        'job__location_type'
    ]
    
    search_fields = [
        'applicant__username',
        'applicant__email', 
        'job__title',
        'job__company__name',
        'job__company_name'
    ]
    
    readonly_fields = ['applied_date', 'last_updated']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('job', 'applicant', 'status')
        }),
        ('Content', {
            'fields': ('cover_letter', 'notes')
        }),
        ('Timestamps', {
            'fields': ('applied_date', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_under_review', 'mark_interviewed', 'mark_rejected']
    
    def applicant_name(self, obj):
        """Show applicant with profile link"""
        return format_html(
            '<a href="/admin/users/customuser/{}/change/">{}</a>',
            obj.applicant.id,
            obj.applicant.get_full_name() or obj.applicant.username
        )
    applicant_name.short_description = "Applicant"
    applicant_name.admin_order_field = 'applicant__username'
    
    def job_title(self, obj):
        """Show job title with link"""
        return format_html(
            '<a href="/admin/jobs/job/{}/change/">{}</a>',
            obj.job.id,
            obj.job.title
        )
    job_title.short_description = "Job"
    job_title.admin_order_field = 'job__title'
    
    def company_name(self, obj):
        """Show company name"""
        return obj.job.get_company_name()
    company_name.short_description = "Company"
    company_name.admin_order_field = 'job__company__name'
    
    def status_badge(self, obj):
        """Show status with color coding"""
        colors = {
            'applied': '#17a2b8',      # info blue
            'review': '#ffc107',       # warning yellow
            'interview_scheduled': '#fd7e14',  # orange
            'interview_completed': '#6f42c1',  # purple
            'offer': '#28a745',        # success green
            'accepted': '#20c997',     # teal
            'rejected': '#dc3545',     # danger red
            'withdrawn': '#6c757d',    # secondary gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = 'status'
    
    def mark_under_review(self, request, queryset):
        updated = queryset.update(status='review')
        self.message_user(request, f'{updated} applications marked as under review.')
    mark_under_review.short_description = "Mark as under review"
    
    def mark_interviewed(self, request, queryset):
        updated = queryset.update(status='interview_completed')
        self.message_user(request, f'{updated} applications marked as interviewed.')
    mark_interviewed.short_description = "Mark as interviewed"
    
    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} applications marked as rejected.')
    mark_rejected.short_description = "Mark as rejected"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'job', 'job__company', 'applicant'
        )