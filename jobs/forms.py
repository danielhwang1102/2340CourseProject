from django import forms
from django.utils import timezone
from .models import Job
from profiles.models import Skill


class JobForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text="Select skills required for this position"
    )

    application_deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'YYYY-MM-DD',
            'lang': 'en-US'
        }),
        input_formats=['%Y-%m-%d'],
        localize=False,
        help_text='Application deadline (optional, format: YYYY-MM-DD)'
    )

    salary_currency = forms.ChoiceField(
        choices=getattr(Job, 'CURRENCY_CHOICES', [('USD', 'US Dollar ($)')]),
        initial='USD',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select the currency for salary range'
    )

    # NEW: Hidden fields for coordinates (User Story #17)
    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_latitude'}),
        max_digits=9,
        decimal_places=6
    )
    
    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_longitude'}),
        max_digits=9,
        decimal_places=6
    )

    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'company_name',
            'street_address', 'city', 'state_province', 'postal_code', 'country',
            'location_type', 'job_type', 'experience_level',
            'salary_min', 'salary_max', 'salary_currency', 'benefits',
            'required_skills', 'visa_sponsorship', 'application_deadline',
            'latitude', 'longitude'  # NEW: Add coordinate fields
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
            'street_address': forms.TextInput(attrs={
                'placeholder': '123 Main Street',
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'placeholder': 'Atlanta',
                'class': 'form-control'
            }),
            'state_province': forms.TextInput(attrs={
                'placeholder': 'Georgia',
                'class': 'form-control'
            }),
            'postal_code': forms.TextInput(attrs={
                'placeholder': '30301',
                'class': 'form-control'
            }),
            'country': forms.TextInput(attrs={
                'placeholder': 'United States',
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
            'street_address': 'Leave blank for remote positions',
            'salary_min': 'Minimum annual salary',
            'salary_max': 'Maximum annual salary',
            'job_type': 'Employment type',
            'experience_level': 'Required experience level',
            'visa_sponsorship': 'Check if you provide visa sponsorship',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Required fields
        for f in ['title', 'description', 'company_name', 'city', 'country', 'job_type', 'location_type', 'experience_level']:
            if f in self.fields:
                self.fields[f].required = True

    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')
        if deadline and deadline < timezone.now().date():
            raise forms.ValidationError("Application deadline cannot be in the past.")
        return deadline

    def clean(self):
        cleaned = super().clean()
        location_type = cleaned.get('location_type')
        city = cleaned.get('city')
        
        # Require city for on-site and hybrid positions
        if location_type in ['onsite', 'hybrid'] and not city:
            raise forms.ValidationError('City is required for on-site and hybrid positions.')
        
        smin = cleaned.get('salary_min')
        smax = cleaned.get('salary_max')
        if smin and smax and smin >= smax:
            raise forms.ValidationError("Maximum salary must be greater than minimum salary.")
        return cleaned


class JobFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Keyword',
        widget=forms.TextInput(attrs={'placeholder': 'Title, company, or description', 'class': 'form-control'})
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'City or State', 'class': 'form-control'})
    )
    job_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Any')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Job Type'
    )
    location_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Any')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Work Location'
    )
    experience_level = forms.ChoiceField(
        required=False,
        choices=[('', 'Any')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Experience Level'
    )
    salary_min = forms.IntegerField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min'})
    )
    salary_max = forms.IntegerField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max'})
    )
    visa_sponsorship = forms.ChoiceField(
        required=False,
        choices=[('', 'Any'), ('yes', 'Yes'), ('no', 'No')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Visa Sponsorship'
    )
    skills = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Skill.objects.all().order_by('name'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job_type'].choices = [('', 'Any')] + list(getattr(Job, 'JOB_TYPE', []))
        self.fields['location_type'].choices = [('', 'Any')] + list(getattr(Job, 'LOCATION_TYPE', []))
        self.fields['experience_level'].choices = [('', 'Any')] + list(getattr(Job, 'EXPERIENCE_LEVEL', []))