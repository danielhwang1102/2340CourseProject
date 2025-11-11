from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib import messages

import companies
from .forms import ProfileForm, CandidateSearchForm, PrivacySettingsForm  # ADD PrivacySettingsForm
from .models import Profile, Skill
from companies.forms import CompanyProfileForm
from companies.models import Company
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


# ADD THIS NEW VIEW
@login_required
def privacy_settings(request):
    """Privacy settings page for job seekers - User Story #5"""
    
    # Only job seekers can access privacy settings
    if request.user.user_type != 'job_seeker':
        messages.error(request, "Only job seekers can access privacy settings.")
        return redirect('profiles:view_profile')
    
    # Get or create profile
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PrivacySettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Privacy settings updated successfully!")
            return redirect('profiles:privacy_settings')
    else:
        form = PrivacySettingsForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'profiles/privacy_settings.html', context)


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


@login_required
def search_candidates(request):
    """
    Allow recruiters to search for candidates by skills, location, and other criteria.
    User Story #11: As a Recruiter, I want to search for candidates by skills, 
    location, and projects so I can find talent that fits my positions.
    """
    # Only recruiters can search for candidates
    if request.user.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can search for candidates.')
        return redirect('profiles:view_profile')
    
    form = CandidateSearchForm(request.GET or None)
    profiles = Profile.objects.none()  # Start with empty queryset
    
    if request.GET:
        # Start with all public profiles of users who are open to work
        profiles = Profile.objects.filter(
            visibility='public',
            user__user_type='job_seeker'
        ).select_related('user').prefetch_related('skills')
        
        if form.is_valid():
            # Filter by keywords (search in headline, bio, current_position)
            keywords = form.cleaned_data.get('keywords')
            if keywords:
                profiles = profiles.filter(
                    Q(headline__icontains=keywords) |
                    Q(bio__icontains=keywords) |
                    Q(current_position__icontains=keywords)
                )
            
            # Filter by skills
            skills = form.cleaned_data.get('skills')
            if skills:
                skill_ids = [skill.id for skill in skills]
                # Annotate with matching skill count and filter
                profiles = profiles.annotate(
                    skill_match_count=Count('skills', filter=Q(skills__in=skill_ids))
                ).filter(skill_match_count__gt=0).order_by('-skill_match_count')
            
            # Filter by location
            location = form.cleaned_data.get('location')
            if location:
                profiles = profiles.filter(location__icontains=location)
            
            # Filter by minimum experience
            min_experience = form.cleaned_data.get('min_experience')
            if min_experience is not None:
                profiles = profiles.filter(years_experience__gte=min_experience)
            
            # Filter by open to work status
            open_to_work = form.cleaned_data.get('open_to_work')
            if open_to_work:
                profiles = profiles.filter(open_to_work=True)
            
            # Filter by education keywords
            education_keyword = form.cleaned_data.get('education_keyword')
            if education_keyword:
                profiles = profiles.filter(education__icontains=education_keyword)
            
            # Filter by certification keywords
            certification_keyword = form.cleaned_data.get('certification_keyword')
            if certification_keyword:
                profiles = profiles.filter(certifications__icontains=certification_keyword)
        
        # Order by most recently updated
        profiles = profiles.order_by('-updated_at')
    
    context = {
        'form': form,
        'profiles': profiles,
        'total_results': profiles.count() if profiles else 0,
    }
    
    return render(request, 'profiles/search_candidates.html', context)


@login_required
def candidate_detail(request, profile_id):
    """
    View detailed profile of a candidate.
    Only accessible to recruiters.
    """
    # Only recruiters can view candidate details
    if request.user.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can view candidate profiles.')
        return redirect('profiles:view_profile')
    
    # Get the profile (must be public and belong to a job seeker)
    profile = get_object_or_404(
        Profile.objects.select_related('user').prefetch_related('skills'),
        id=profile_id,
        visibility='public',
        user__user_type='job_seeker'
    )
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'profiles/candidate_detail.html', context)