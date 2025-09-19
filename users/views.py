from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from profiles.models import Profile
from profiles.forms import ProfileCompletionForm

@login_required
def profile_completion_required(request):
    """Redirect users to complete their profile if incomplete"""
    if request.user.profile_completed:
        return redirect('home')
    
    if request.user.user_type == 'job_seeker':
        return redirect('users:complete_job_seeker_profile')
    else:
        return redirect('users:complete_recruiter_profile')

class ProfileCompletionView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileCompletionForm
    template_name = 'users/complete_profile.html'
    success_url = reverse_lazy('home')

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mark profile as completed
        if form.instance.is_complete:
            self.request.user.profile_completed = True
            self.request.user.save()
            messages.success(self.request, 'Profile completed successfully!')
        else:
            messages.warning(self.request, 'Please complete all required fields.')
        return response

class JobSeekerProfileCompletionView(ProfileCompletionView):
    """Job seeker specific profile completion"""
    template_name = 'users/complete_job_seeker_profile.html'

class RecruiterProfileCompletionView(ProfileCompletionView):
    """Recruiter specific profile completion"""
    template_name = 'users/complete_recruiter_profile.html'