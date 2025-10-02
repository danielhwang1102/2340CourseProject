from django.shortcuts import render

import companies
from .forms import ProfileForm
from companies.forms import CompanyProfileForm
from companies.models import Company


# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Count, Q

from jobs.models import Job

@login_required
def edit_profile(request):
    user = request.user
    if user.user_type == 'recruiter':
        form_class = CompanyProfileForm
        # Assuming one company per recruiter:
        company = Company.objects.filter(created_by=user).first()
        profile_instance = company
    else:
        form_class = ProfileForm
        profile_instance = getattr(user, 'profile', None)

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=profile_instance)
        if form.is_valid():
            form.save()
            return redirect('profiles:view_profile')
    else:
        form = form_class(instance=profile_instance)

    return render(request, 'profiles/edit_profile.html', {'form': form})
@login_required
def view_profile(request):
    user = request.user
    if user.user_type == 'recruiter':
        company = Company.objects.filter(created_by=user).first()
        profile_instance = company
    else:
        profile_instance = getattr(user, 'profile', None)
    return render(request, 'profiles/view_profile.html', {'profile': profile_instance})


@login_required
def recommend_jobs(request):
    """Recommend jobs to the current job seeker based on their profile skills.

    Algorithm:
    - Get the authenticated user's profile and their skills.
    - Find active jobs that require any of those skills.
    - Annotate each job with the number of matching skills (match_count).
    - Order by match_count desc then most recent.
    """
    user = request.user
    # Only job seekers should receive recommendations here
    if getattr(user, 'user_type', '') != 'job_seeker':
        # For simplicity redirect non-job-seekers to their profile view
        return redirect('profiles:view_profile')

    profile = getattr(user, 'profile', None)
    if not profile:
        # If no profile, return an empty list with a notice
        return render(request, 'profiles/recommendations.html', {'jobs': [], 'profile': None})

    skill_ids = list(profile.skills.values_list('id', flat=True))
    if not skill_ids:
        # No skills -> no recommendations
        return render(request, 'profiles/recommendations.html', {'jobs': [], 'profile': profile})

    # Annotate jobs with how many of the user's skills they require
    jobs_qs = (
        Job.objects.filter(is_active=True)
        .annotate(match_count=Count('required_skills', filter=Q(required_skills__in=skill_ids)))
        .filter(match_count__gt=0)
        .select_related('posted_by')
        .prefetch_related('required_skills')
        .order_by('-match_count', '-created_at')
    )

    return render(request, 'profiles/recommendations.html', {'jobs': jobs_qs, 'profile': profile})