from django import forms
from .models import Profile, Skill, SavedSearch
from companies.models import Company

class ProfileCompletionForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Profile
        fields = ['headline', 'bio', 'location', 'skills', 'current_position', 
                    'years_experience', 'education', 'open_to_work']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'headline': forms.TextInput(attrs={'placeholder': 'e.g., Senior Software Engineer'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Atlanta, GA'}),
            'education': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'e.g., Bachelor of Computer Science, University of California (2020)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class ProfileForm(forms.ModelForm):
    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )
    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Profile
        fields = [
            'headline', 'bio', 'skills', 'location',
            'latitude', 'longitude',
            'website', 'linkedin', 'github', 'resume', 'profile_picture',
            'current_position', 'years_experience', 'education', 'certifications',
            'visibility', 'open_to_work', 'preferred_salary_min', 'preferred_salary_max'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'education': forms.Textarea(attrs={'rows': 3}),
            'certifications': forms.Textarea(attrs={'rows': 3}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'location-input',
                'placeholder': 'Atlanta, GA'
            }),
        }


# ADD THIS NEW FORM
class PrivacySettingsForm(forms.ModelForm):
    """Form for job seekers to manage privacy settings"""
    
    class Meta:
        model = Profile
        fields = [
            'show_email',
            'show_phone',
            'show_location',
            'show_experience',
            'show_education',
            'show_skills',
            'show_links',
            'show_certifications',
            'show_resume',
            'open_to_work',
            'visibility',
        ]
        widgets = {
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_location': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_experience': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_education': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_skills': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_links': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_certifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_resume': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'open_to_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
        }


class CandidateSearchForm(forms.Form):
    """Form for recruiters to search for candidates"""
    
    # Search by keywords
    keywords = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by headline, bio, or position...'
        }),
        label='Keywords'
    )
    
    # Filter by skills
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Required Skills'
    )
    
    # Filter by location
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Atlanta, GA'
        }),
        label='Location'
    )
    
    # Filter by experience level
    min_experience = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum years'
        }),
        label='Minimum Years of Experience'
    )
    
    # Filter by availability
    open_to_work = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Only show candidates open to work',
        initial=True
    )
    
    # Filter by education
    education_keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Computer Science, MBA'
        }),
        label='Education'
    )
    
    # Filter by certifications
    certification_keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., AWS, PMP'
        }),
        label='Certifications'
    )

class SaveSearchForm(forms.ModelForm):
    """Form to save a candidate search"""
    
    class Meta:
        model = SavedSearch
        fields = ['name', 'description', 'notify_on_new_matches']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Python Developers in Atlanta',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional: Describe what you\'re looking for...'
            }),
            'notify_on_new_matches': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Search Name',
            'description': 'Description (Optional)',
            'notify_on_new_matches': 'Email me when new candidates match this search'
        }

# ADD THIS NEW FORM
class CompanyProfileForm(forms.ModelForm):
    """Form for recruiters to edit company profile"""
    
    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )
    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = Company
        fields = [
            'name',
            'description',
            'website',
            'logo',
            'location',
            'founded_year',
            'employees_count',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Tech Solutions Inc.',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Tell job seekers about your company, mission, culture, and what makes you unique...'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.yourcompany.com'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'location-input',
                'placeholder': 'e.g., Atlanta, GA'
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2010',
                'min': 1800,
                'max': 2025
            }),
            'employees_count': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 50-100'
            }),
        }
        labels = {
            'name': 'Company Name *',
            'description': 'Company Description *',
            'website': 'Company Website',
            'logo': 'Company Logo',
            'location': 'Company Location *',
            'founded_year': 'Founded Year',
            'employees_count': 'Number of Employees',
        }
        help_texts = {
            'name': 'Official name of your company',
            'description': 'Describe your company, products/services, culture, and mission (at least 100 characters)',
            'website': 'Your company\'s official website URL',
            'logo': 'Upload your company logo (recommended: square image, at least 200x200px)',
            'location': 'City and state/country where your company is headquartered',
            'founded_year': 'Year your company was established',
            'employees_count': 'Approximate number of employees (e.g., "1-10", "50-100", "500+")',
        }
    
    def clean_description(self):
        """Ensure description is substantial"""
        description = self.cleaned_data.get('description', '')
        if description and len(description.strip()) < 100:
            raise forms.ValidationError(
                'Company description must be at least 100 characters. '
                f'Current length: {len(description.strip())} characters.'
            )
        return description
    
    def clean_founded_year(self):
        """Validate founded year is reasonable"""
        from datetime import datetime
        founded_year = self.cleaned_data.get('founded_year')
        if founded_year:
            current_year = datetime.now().year
            if founded_year < 1800:
                raise forms.ValidationError('Founded year cannot be before 1800.')
            if founded_year > current_year:
                raise forms.ValidationError(f'Founded year cannot be in the future (current year: {current_year}).')
        return founded_year