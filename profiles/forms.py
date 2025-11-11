from django import forms
from .models import Profile, Skill, SavedSearch

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
    class Meta:
        model = Profile
        fields = [
            'headline', 'bio', 'skills', 'location',
            'website', 'linkedin', 'github', 'resume', 'profile_picture',
            'current_position', 'years_experience', 'education', 'certifications',
            'visibility', 'open_to_work', 'preferred_salary_min', 'preferred_salary_max'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'education': forms.Textarea(attrs={'rows': 3}),
            'certifications': forms.Textarea(attrs={'rows': 3}),
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