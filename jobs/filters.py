import django_filters
from django import forms
from .models import Job
from profiles.models import Skill

class JobFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        lookup_expr='icontains', 
        label='Job Title',
        widget=forms.TextInput(attrs={'placeholder': 'Search job titles...'})
    )
    company_name = django_filters.CharFilter(
        lookup_expr='icontains', 
        label='Company',
        widget=forms.TextInput(attrs={'placeholder': 'Company name...'})
    )
    location = django_filters.CharFilter(
        lookup_expr='icontains', 
        label='Location',
        widget=forms.TextInput(attrs={'placeholder': 'City, State...'})
    )
    salary_min = django_filters.NumberFilter(
        field_name='salary_min',
        lookup_expr='gte',
        label='Minimum Salary'
    )
    required_skills = django_filters.ModelMultipleChoiceFilter(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Required Skills'
    )

    class Meta:
        model = Job
        fields = ['job_type', 'location_type', 'experience_level', 'visa_sponsorship']