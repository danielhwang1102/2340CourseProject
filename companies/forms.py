from django import forms
from .models import Company

class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'website', 'logo', 'location', 'founded_year', 'employees_count']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Tech Solutions Inc.'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about your company, your mission, and what makes you unique...'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.yourcompany.com'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Atlanta, GA'
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2020',
                'min': 1800,
                'max': 2025
            }),
            'employees_count': forms.Select(
                choices=[
                    ('', 'Select company size'),
                    ('1-10', '1-10 employees'),
                    ('11-50', '11-50 employees'),
                    ('51-200', '51-200 employees'),
                    ('201-500', '201-500 employees'),
                    ('501-1000', '501-1000 employees'),
                    ('1001+', '1001+ employees'),
                ],
                attrs={'class': 'form-select'}
            ),
        }
        labels = {
            'name': 'Company Name*',
            'description': 'Company Description*',
            'website': 'Company Website',
            'logo': 'Company Logo',
            'location': 'Location*',
            'founded_year': 'Founded Year',
            'employees_count': 'Company Size*',
        }
        help_texts = {
            'name': 'Enter your company\'s official name',
            'description': 'Provide a compelling description to attract top talent',
            'website': 'Your company\'s official website (optional)',
            'logo': 'Upload your company logo (PNG, JPG, max 2MB)',
            'location': 'Primary office location or headquarters',
            'founded_year': 'Year your company was established',
            'employees_count': 'Approximate number of employees',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark required fields
        self.fields['name'].required = True
        self.fields['description'].required = True
        self.fields['location'].required = True
        self.fields['employees_count'].required = True