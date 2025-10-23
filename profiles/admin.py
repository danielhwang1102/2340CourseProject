from django.contrib import admin
from django.http import HttpResponse
import csv
from .models import Profile, Skill

def export_profiles_csv(modeladmin, request, queryset):
    """Export selected job seeker profiles to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="job_seeker_profiles.csv"'
    
    writer = csv.writer(response)
    # Header row
    writer.writerow([
        'User ID',
        'Username',
        'Email',
        'User Type',
        'Headline',
        'Bio',
        'Location',
        'Skills',
        'Website',
        'LinkedIn',
        'GitHub',
        'Current Position',
        'Years Experience',
        'Education',
        'Certifications',
        'Open to Work',
        'Preferred Salary Min',
        'Preferred Salary Max',
        'Visibility',
        'Profile Complete',
    ])
    
    # Data rows
    for profile in queryset.select_related('user').prefetch_related('skills'):
        skills_list = ', '.join([skill.name for skill in profile.skills.all()])
        writer.writerow([
            profile.user.id,
            profile.user.username,
            profile.user.email,
            profile.user.user_type,
            profile.headline,
            profile.bio[:200] if profile.bio else '',  # Truncate long text
            profile.location,
            skills_list,
            profile.website,
            profile.linkedin,
            profile.github,
            profile.current_position,
            profile.years_experience,
            profile.education[:200] if profile.education else '',
            profile.certifications[:200] if profile.certifications else '',
            'Yes' if profile.open_to_work else 'No',
            profile.preferred_salary_min,
            profile.preferred_salary_max,
            profile.visibility,
            'Yes' if profile.is_complete else 'No',
        ])
    
    return response

export_profiles_csv.short_description = "Export selected profiles to CSV"


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name', 'category']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'headline', 'location', 'open_to_work', 'is_complete']
    list_filter = ['open_to_work', 'visibility']
    search_fields = ['user__username', 'user__email', 'headline', 'location']
    filter_horizontal = ['skills']
    actions = [export_profiles_csv]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('headline', 'bio', 'current_position', 'years_experience', 'education', 'certifications')
        }),
        ('Skills & Location', {
            'fields': ('skills', 'location')
        }),
        ('Contact & Links', {
            'fields': ('website', 'linkedin', 'github')
        }),
        ('Files', {
            'fields': ('resume', 'profile_picture')
        }),
        ('Preferences', {
            'fields': ('open_to_work', 'preferred_salary_min', 'preferred_salary_max', 'visibility')
        }),
    )