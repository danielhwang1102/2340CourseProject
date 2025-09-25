from django.urls import path
from .views import (
    profile_completion_required,
    JobSeekerProfileCompletionView, 
    RecruiterProfileCompletionView
)
from django.urls import path, include

app_name = 'users'

urlpatterns = [
    path('profile-completion/', profile_completion_required, name='profile_completion'),
    path('complete-job-seeker-profile/', JobSeekerProfileCompletionView.as_view(), name='complete_job_seeker_profile'),
    path('complete-recruiter-profile/', RecruiterProfileCompletionView.as_view(), name='complete_recruiter_profile'),
    path('profiles/', include('profiles.urls')),
]