from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.contrib import messages
from django.utils import timezone
import json

User = get_user_model()

from .forms import ProfileForm, CandidateSearchForm, PrivacySettingsForm, SaveSearchForm
from .models import Profile, Skill, SavedSearch, NewMatchNotification
from django.http import JsonResponse
from companies.forms import CompanyProfileForm
from companies.models import Company
from jobs.models import Job

def view_profile_by_username(request, username):
    """
    View any user's profile by their username.
    Shows public information only.
    """
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    
    # Check if profile is public or if viewer is the owner
    if profile.visibility == 'private' and request.user != user:
        return render(request, 'profiles/profile_private.html', {
            'viewed_user': user
        })
    
    context = {
        'viewed_user': user,
        'profile': profile,
        'is_own_profile': request.user == user,
        'skills': profile.skills.all(),
    }
    
    return render(request, 'profiles/view_profile.html', context)


@login_required
def edit_profile(request):
    user = request.user
    
    if user.user_type == 'recruiter':
        form_class = CompanyProfileForm
        company = Company.objects.filter(created_by=user).first()
        profile_instance = company
    else:
        form_class = ProfileForm
        profile_instance = getattr(user, 'profile', None)

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=profile_instance)
        if form.is_valid():
            profile = form.save(commit=False)
            
            # ✅ SAVE COORDINATES FROM HIDDEN FIELDS (for job seekers)
            if user.user_type == 'job_seeker':
                profile.latitude = form.cleaned_data.get('latitude')
                profile.longitude = form.cleaned_data.get('longitude')
            
            profile.save()
            form.save_m2m()  # Save many-to-many relationships (skills)
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profiles:view_profile')
    else:
        form = form_class(instance=profile_instance)

    return render(request, 'profiles/edit_profile.html', {
        'form': form,
        'is_recruiter': user.user_type == 'recruiter'
    })


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
def privacy_settings(request):
    """Privacy settings page for job seekers - User Story #5"""
    
    if request.user.user_type != 'job_seeker':
        messages.error(request, "Only job seekers can access privacy settings.")
        return redirect('profiles:view_profile')
    
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
    """Recommend jobs to the current job seeker based on their profile skills."""
    user = request.user
    if getattr(user, 'user_type', '') != 'job_seeker':
        return redirect('profiles:view_profile')

    profile = getattr(user, 'profile', None)
    if not profile:
        return render(request, 'profiles/recommendations.html', {'jobs': [], 'profile': None})

    skill_ids = list(profile.skills.values_list('id', flat=True))
    if not skill_ids:
        return render(request, 'profiles/recommendations.html', {'jobs': [], 'profile': profile})

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
    """Allow recruiters to search for candidates - User Story #11"""
    if request.user.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can search for candidates.')
        return redirect('profiles:view_profile')
    
    form = CandidateSearchForm(request.GET or None)
    profiles = Profile.objects.none()
    
    if request.GET:
        profiles = Profile.objects.filter(
            visibility='public',
            user__user_type='job_seeker'
        ).select_related('user').prefetch_related('skills')
        
        if form.is_valid():
            keywords = form.cleaned_data.get('keywords')
            if keywords:
                profiles = profiles.filter(
                    Q(headline__icontains=keywords) |
                    Q(bio__icontains=keywords) |
                    Q(current_position__icontains=keywords)
                )
            
            skills = form.cleaned_data.get('skills')
            if skills:
                skill_ids = [skill.id for skill in skills]
                profiles = profiles.annotate(
                    skill_match_count=Count('skills', filter=Q(skills__in=skill_ids))
                ).filter(skill_match_count__gt=0).order_by('-skill_match_count')
            
            location = form.cleaned_data.get('location')
            if location:
                profiles = profiles.filter(location__icontains=location)
            
            min_experience = form.cleaned_data.get('min_experience')
            if min_experience is not None:
                profiles = profiles.filter(years_experience__gte=min_experience)
            
            open_to_work = form.cleaned_data.get('open_to_work')
            if open_to_work:
                profiles = profiles.filter(open_to_work=True)
            
            education_keyword = form.cleaned_data.get('education_keyword')
            if education_keyword:
                profiles = profiles.filter(education__icontains=education_keyword)
            
            certification_keyword = form.cleaned_data.get('certification_keyword')
            if certification_keyword:
                profiles = profiles.filter(certifications__icontains=certification_keyword)
        
        profiles = profiles.order_by('-updated_at')
    
    context = {
        'form': form,
        'profiles': profiles,
        'total_results': profiles.count() if profiles else 0,
    }
    
    return render(request, 'profiles/search_candidates.html', context)


@login_required
def candidate_detail(request, profile_id):
    """View detailed profile of a candidate - Only accessible to recruiters"""
    if request.user.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can view candidate profiles.')
        return redirect('profiles:view_profile')
    
    profile = get_object_or_404(
        Profile.objects.select_related('user').prefetch_related('skills'),
        id=profile_id,
        visibility='public',
        user__user_type='job_seeker'
    )
    
    context = {'profile': profile}
    return render(request, 'profiles/candidate_detail.html', context)


@login_required
def save_search(request):
    """Save current candidate search - User Story #15"""
    
    if request.user.user_type != 'recruiter':
        messages.error(request, "Only recruiters can save searches.")
        return redirect('profiles:search_candidates')
    
    if request.method == 'POST':
        form = SaveSearchForm(request.POST)
        
        if form.is_valid():
            saved_search = form.save(commit=False)
            saved_search.recruiter = request.user
            
            search_criteria = {}
            
            # Handle simple text fields - ONLY save non-empty values
            for key in ['keywords', 'location', 'min_experience', 'education_keyword', 'certification_keyword']:
                value = request.POST.get(key) or request.GET.get(key)
                if value and str(value).strip() and str(value).strip() != '':
                    search_criteria[key] = str(value).strip()
            
            # Handle checkbox (open_to_work)
            open_to_work = request.POST.get('open_to_work') or request.GET.get('open_to_work')
            if open_to_work in ['on', 'true', True]:
                search_criteria['open_to_work'] = True
            
            # Handle skills (multiple selection)
            skill_ids = request.POST.getlist('skills')
            if not skill_ids:
                skill_ids = request.GET.getlist('skills')
            
            try:
                skill_ids = [int(sid) for sid in skill_ids if sid and str(sid).strip() and str(sid).strip() != '']
                
                if skill_ids:
                    skills = Skill.objects.filter(id__in=skill_ids)
                    search_criteria['skills'] = [skill.name for skill in skills]
                    search_criteria['skill_ids'] = skill_ids
            except (ValueError, TypeError) as e:
                messages.warning(request, "Some skills could not be processed.")
                print(f"Error processing skills: {e}")
            
            saved_search.search_criteria = search_criteria
            saved_search.save()
            
            messages.success(request, f"Search '{saved_search.name}' saved successfully!")
            return redirect('profiles:saved_searches')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SaveSearchForm(initial={'notify_on_new_matches': True})
    
    # Get current search criteria for display
    current_criteria = {}
    for key in request.GET:
        values = request.GET.getlist(key)
        values = [v for v in values if v and str(v).strip()]
        if values:
            # FIX: Always store skills as a list (even if single value)
            if key == 'skills':
                current_criteria[key] = values  # Always a list
            else:
                # For other fields, single value = string, multiple = list
                current_criteria[key] = values[0] if len(values) == 1 else values
    
    context = {
        'form': form,
        'current_criteria': current_criteria,
    }
    
    return render(request, 'profiles/save_search.html', context)


@login_required
def saved_searches(request):
    """List all saved searches for current recruiter - User Story #15"""
    
    if request.user.user_type != 'recruiter':
        messages.error(request, "Only recruiters can access saved searches.")
        return redirect('profiles:view_profile')
    
    searches = SavedSearch.objects.filter(recruiter=request.user)
    
    context = {'searches': searches}
    return render(request, 'profiles/saved_searches.html', context)


@login_required
def run_saved_search(request, search_id):
    """Run a saved search and show results - User Story #15"""
    
    if request.user.user_type != 'recruiter':
        messages.error(request, "Only recruiters can run saved searches.")
        return redirect('profiles:view_profile')
    
    saved_search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    
    saved_search.last_run_at = timezone.now()
    
    criteria = saved_search.search_criteria
    
    profiles = Profile.objects.filter(
        visibility='public',
        user__user_type='job_seeker'
    ).select_related('user').prefetch_related('skills')
    
    # Apply filters - WITH VALIDATION
    if criteria.get('keywords'):
        keywords = str(criteria['keywords']).strip()
        if keywords:
            profiles = profiles.filter(
                Q(headline__icontains=keywords) |
                Q(bio__icontains=keywords) |
                Q(current_position__icontains=keywords)
            )
    
    if criteria.get('location'):
        location = str(criteria['location']).strip()
        if location:
            profiles = profiles.filter(location__icontains=location)
    
    if criteria.get('min_experience'):
        try:
            min_exp = criteria['min_experience']
            if isinstance(min_exp, str):
                min_exp = min_exp.strip()
                if min_exp:
                    min_exp = int(min_exp)
                    profiles = profiles.filter(years_experience__gte=min_exp)
            elif isinstance(min_exp, (int, float)):
                profiles = profiles.filter(years_experience__gte=int(min_exp))
        except (ValueError, TypeError):
            pass
    
    if criteria.get('open_to_work') in ['on', 'true', True]:
        profiles = profiles.filter(open_to_work=True)
    
    if criteria.get('education_keyword'):
        edu = str(criteria['education_keyword']).strip()
        if edu:
            profiles = profiles.filter(education__icontains=edu)
    
    if criteria.get('certification_keyword'):
        cert = str(criteria['certification_keyword']).strip()
        if cert:
            profiles = profiles.filter(certifications__icontains=cert)
    
    if criteria.get('skill_ids'):
        try:
            skill_ids = criteria['skill_ids']
            if isinstance(skill_ids, str):
                skill_ids = [int(sid) for sid in skill_ids.split(',') if sid.strip()]
            elif isinstance(skill_ids, list):
                skill_ids = [int(sid) for sid in skill_ids if sid]
            
            if skill_ids:
                profiles = profiles.annotate(
                    skill_match_count=Count('skills', filter=Q(skills__id__in=skill_ids))
                ).filter(skill_match_count__gt=0).order_by('-skill_match_count')
        except (ValueError, TypeError):
            pass
    
    profiles = profiles.order_by('-updated_at')
    
    saved_search.last_match_count = profiles.count()
    saved_search.save()
    
    form_data = {
        'keywords': criteria.get('keywords', ''),
        'location': criteria.get('location', ''),
        'min_experience': criteria.get('min_experience', ''),
        'open_to_work': criteria.get('open_to_work', False),
        'education_keyword': criteria.get('education_keyword', ''),
        'certification_keyword': criteria.get('certification_keyword', ''),
    }
    
    if criteria.get('skill_ids'):
        try:
            skill_ids = criteria['skill_ids']
            if isinstance(skill_ids, str):
                skill_ids = [int(sid) for sid in skill_ids.split(',') if sid.strip()]
            elif isinstance(skill_ids, list):
                skill_ids = [int(sid) for sid in skill_ids if sid]
            
            if skill_ids:
                form_data['skills'] = Skill.objects.filter(id__in=skill_ids)
        except (ValueError, TypeError):
            pass
    
    form = CandidateSearchForm(initial=form_data)
    
    context = {
        'form': form,
        'profiles': profiles,
        'total_results': profiles.count(),
        'saved_search': saved_search,
        'is_saved_search': True,
    }
    
    return render(request, 'profiles/search_candidates.html', context)


@login_required
def delete_saved_search(request, search_id):
    """Delete a saved search - User Story #15"""
    
    if request.user.user_type != 'recruiter':
        messages.error(request, "Only recruiters can delete saved searches.")
        return redirect('profiles:view_profile')
    
    saved_search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    
    search_name = saved_search.name
    saved_search.delete()
    
    messages.success(request, f"Saved search '{search_name}' deleted successfully!")
    return redirect('profiles:saved_searches')


@login_required
def edit_saved_search(request, search_id):
    """Edit a saved search - User Story #15"""
    
    if request.user.user_type != 'recruiter':
        messages.error(request, "Only recruiters can edit saved searches.")
        return redirect('profiles:view_profile')
    
    saved_search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    
    if request.method == 'POST':
        form = SaveSearchForm(request.POST, instance=saved_search)
        if form.is_valid():
            form.save()
            messages.success(request, f"Search '{saved_search.name}' updated successfully!")
            return redirect('profiles:saved_searches')
    else:
        form = SaveSearchForm(instance=saved_search)
    
    context = {
        'form': form,
        'saved_search': saved_search,
        'is_edit': True,
    }
    
    return render(request, 'profiles/save_search.html', context)

@login_required
def notifications(request):
    """View all new match notifications for current user"""
    user_notifications = NewMatchNotification.objects.filter(user=request.user)
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        user_notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        messages.success(request, "All notifications marked as read.")
        return redirect('profiles:notifications')
    
    context = {
        'notifications': user_notifications,
        'unread_count': user_notifications.filter(is_read=False).count(),
    }
    return render(request, 'profiles/notifications.html', context)


@login_required
def notification_mark_read(request, notification_id):
    """Mark a single notification as read and redirect to its link"""
    notification = get_object_or_404(NewMatchNotification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    # Redirect to the notification's link or back to notifications
    if notification.link_url:
        return redirect(notification.link_url)
    else:
        return redirect('profiles:notifications')


@login_required
def notification_unread_count(request):
    """API endpoint to get unread notification count (JSON)"""
    count = NewMatchNotification.get_unread_count(request.user)
    return JsonResponse({'unread_count': count})


@login_required
def notification_latest(request):
    """API endpoint to get latest notifications (JSON)"""
    notifications = NewMatchNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    data = {
        'unread_count': NewMatchNotification.get_unread_count(request.user),
        'notifications': [
            {
                'id': n.pk,
                'title': n.title,
                'message': n.message,
                'link_url': n.link_url,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%b %d, %Y %I:%M %p'),
                'type': n.notification_type,
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)


@login_required
def notification_delete(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(NewMatchNotification, id=notification_id, user=request.user)
    notification.delete()
    messages.success(request, "Notification deleted.")
    return redirect('profiles:notifications')