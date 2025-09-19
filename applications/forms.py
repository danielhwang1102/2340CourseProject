from django import forms
from .models import Application

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Write a personalized message to the employer...',
                'class': 'form-control'
            })
        }
        labels = {
            'cover_letter': 'Cover Letter / Personal Message'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_letter'].required = False  # Make it optional