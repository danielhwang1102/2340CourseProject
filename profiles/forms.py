from django import forms
from .models import Profile, Skill

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
            'education': forms.Textarea(attrs={  # ← Added education widget
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
        fields = ['bio', 'location', 'resume']  # Add your Profile fields here