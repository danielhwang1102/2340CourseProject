from django import forms
from .models import Company

class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'  # This includes all fields in the Company model