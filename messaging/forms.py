from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    """Form for composing and sending messages"""
    
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Type your message here...',
                'required': True
            })
        }
        labels = {
            'content': 'Message'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True


class ComposeMessageForm(forms.Form):
    """Form for starting a new conversation"""
    recipient_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        }),
        label='Recipient Username'
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Type your message here...'
        }),
        label='Message'
    )