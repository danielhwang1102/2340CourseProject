from django import forms
from django.utils import timezone
from .models import Job
from profiles.models import Skill

class JobForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text="Select skills required for this position"
    )
    
    # Override the application_deadline field to force English format
    application_deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'YYYY-MM-DD',
            'lang': 'en-US'
        }),
        help_text='Application deadline (optional, format: YYYY-MM-DD)',
        input_formats=['%Y-%m-%d'],
        localize=False
    )
    
    # Override salary_currency to ensure proper display
    salary_currency = forms.ChoiceField(
        choices=Job.CURRENCY_CHOICES,
        initial='USD',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select the currency for salary range'
    )
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'company_name',
            'location', 'location_type', 'job_type', 'experience_level',
            'salary_min', 'salary_max', 'salary_currency', 'benefits',
            'required_skills', 'visa_sponsorship', 'application_deadline'
        ]
        
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the role, responsibilities, and what makes this position exciting...',
                'class': 'form-control'
            }),
            'requirements': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'List the required qualifications, skills, and experience...',
                'class': 'form-control'
            }),
            'benefits': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe benefits, perks, and company culture...',
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Senior Software Engineer',
                'class': 'form-control'
            }),
            'company_name': forms.TextInput(attrs={
                'placeholder': 'e.g. Tech Corp Inc.',
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'e.g. Atlanta, GA or Remote',
                'class': 'form-control'
            }),
            'salary_min': forms.NumberInput(attrs={
                'placeholder': '70000',
                'class': 'form-control',
                'step': '1000'
            }),
            'salary_max': forms.NumberInput(attrs={
                'placeholder': '90000',
                'class': 'form-control',
                'step': '1000'
            }),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'location_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'visa_sponsorship': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        help_texts = {
            'salary_min': 'Minimum annual salary',
            'salary_max': 'Maximum annual salary',
            'location': 'City, State or "Remote"',
            'job_type': 'Employment type',
            'experience_level': 'Required experience level',
            'visa_sponsorship': 'Check if you provide visa sponsorship',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields required
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['location'].required = True
        self.fields['company_name'].required = True
        self.fields['job_type'].required = True
        self.fields['location_type'].required = True
        self.fields['experience_level'].required = True
    
    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')
        if deadline and deadline < timezone.now().date():
            raise forms.ValidationError("Application deadline cannot be in the past.")
        return deadline
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        # Validate salary range
        if salary_min and salary_max:
            if salary_min >= salary_max:
                raise forms.ValidationError(
                    "Maximum salary must be greater than minimum salary."
                )
        
        return cleaned_data