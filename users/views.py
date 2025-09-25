from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from profiles.models import Profile
from profiles.forms import ProfileCompletionForm
from django.views import View

class DashboardRedirectView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        user_type = getattr(request.user, 'user_type', '')
        if user_type == 'recruiter':
            return redirect('jobs:my_jobs')
        return redirect('jobs:job_list')

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
        # Save form and many-to-many data first so we can evaluate completeness
        self.object = form.save()
        try:
            form.save_m2m()
        except Exception:
            # Some forms may not have m2m data; ignore if not present
            pass

        # Decide completeness based on user type. Job seekers use Profile.is_complete,
        # recruiters only need basic fields (headline, bio, location).
        user_type = getattr(self.request.user, 'user_type', None)
        if user_type == 'job_seeker' or user_type is None:
            complete = form.instance.is_complete
        else:
            required_fields = [form.instance.headline, form.instance.bio, form.instance.location]
            complete = all(required_fields)

        if complete:
            # mark user and redirect to dashboard
            self.request.user.profile_completed = True
            self.request.user.save()
            messages.success(self.request, 'Profile completed successfully!')
            return redirect('dashboard')
        else:
            messages.warning(self.request, 'Please complete all required fields.')
            # Re-render the form with the warning (do not redirect)
            return self.render_to_response(self.get_context_data(form=form))

class JobSeekerProfileCompletionView(ProfileCompletionView):
    """Job seeker specific profile completion"""
    template_name = 'users/complete_job_seeker_profile.html'

class RecruiterProfileCompletionView(ProfileCompletionView):
    """Recruiter specific profile completion"""
    template_name = 'users/complete_recruiter_profile.html'