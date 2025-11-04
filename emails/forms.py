from django import forms
from .models import EmailLog

class EmailCandidateForm(forms.ModelForm):
    """Form for emailing candidates (User Story #14)"""
    
    class Meta:
        model = EmailLog
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Subject',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Email Message...',
                'required': True
            })
        }
        labels = {
            'subject': 'Subject',
            'message': 'Message'
        }
    
    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        self.recipient = kwargs.pop('recipient', None)
        super().__init__(*args, **kwargs)