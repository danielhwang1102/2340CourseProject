from django import forms
from .models import Company

class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'website', 'logo', 'location', 'founded_year', 'employees_count']