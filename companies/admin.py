from django.contrib import admin
from django.http import HttpResponse
import csv
from .models import Company

def export_companies_csv(modeladmin, request, queryset):
    """Export selected companies to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="companies.csv"'
    
    writer = csv.writer(response)
    # Header row
    writer.writerow([
        'Company ID',
        'Company Name',
        'Description',
        'Website',
        'Location',
        'Founded Year',
        'Employees Count',
        'Created By (Username)',
        'Created By (Email)',
        'Created By (User Type)',
        'Created At',
        'Updated At',
        'Total Jobs Posted',
    ])
    
    # Data rows
    for company in queryset.select_related('created_by').prefetch_related('job_set'):
        writer.writerow([
            company.id,
            company.name,
            company.description[:200] if company.description else '',  # Truncate long text
            company.website,
            company.location,
            company.founded_year,
            company.employees_count,
            company.created_by.username,
            company.created_by.email,
            company.created_by.user_type,
            company.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            company.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(company, 'updated_at') else '',
            company.job_set.count(),  # Total jobs posted by this company
        ])
    
    return response

export_companies_csv.short_description = "Export selected companies to CSV"


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'created_by', 'created_at')
    search_fields = ('name', 'location')
    list_filter = ('created_at',)
    actions = [export_companies_csv]  # ADD THIS LINE