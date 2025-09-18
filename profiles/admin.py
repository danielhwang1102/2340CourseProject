from django.contrib import admin
from .models import Profile, Skill

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'headline', 'location', 'open_to_work', 'is_complete')
    search_fields = ('user__username', 'headline', 'location')
    list_filter = ('open_to_work', 'visibility', 'created_at')
    filter_horizontal = ('skills',)