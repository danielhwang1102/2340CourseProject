from django import forms
from allauth.account.forms import SignupForm
from .models import CustomUser
from companies.models import Company

class CustomSignupForm(SignupForm):
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES, 
        label='I am a:',
        widget=forms.RadioSelect
    )
    
    # Additional field for recruiters
    company_name = forms.CharField(
        max_length=200, 
        required=False,
        help_text="Enter your company name (recruiters only)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].label = "Email:"  # Remove "(optional)"

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        company_name = cleaned_data.get('company_name')
        
        if user_type == 'recruiter' and not company_name:
            raise forms.ValidationError("Company name is required for recruiters.")
        
        return cleaned_data

    def save(self, request):
        user = super().save(request)
        user.user_type = self.cleaned_data['user_type']
        user.save()
        
        # Create company if recruiter
        if user.user_type == 'recruiter' and self.cleaned_data.get('company_name'):
            Company.objects.get_or_create(
                name=self.cleaned_data['company_name'],
                defaults={'created_by': user}
            )
        
        return user