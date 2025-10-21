from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.db import IntegrityError
from .forms import ProfileForm
from .models import Profile
from companies.forms import CompanyProfileForm
from companies.models import Company
from jobs.models import Job


@login_required
def edit_profile(request):
    user = request.user
    
    if user.user_type == 'recruiter':
        # Recruiter: Edit company profile
        form_class = CompanyProfileForm
        
        # Get or create the company profile
        try:
            company = Company.objects.get(created_by=user)
        except Company.DoesNotExist:
            company = None
        
        if request.method == 'POST':
            form = form_class(request.POST, request.FILES, instance=company)
            if form.is_valid():
                try:
                    company_profile = form.save(commit=False)
                    company_profile.created_by = user
                    company_profile.save()
                    messages.success(request, 'Company profile saved successfully!')
                    return redirect('profiles:view_profile')
                except IntegrityError as e:
                    messages.error(request, f'Error saving profile: {str(e)}')
                    print(f"IntegrityError: {e}")
                except Exception as e:
                    messages.error(request, f'Error saving profile: {str(e)}')
                    print(f"Error: {e}")
            else:
                print("Form errors:", form.errors)
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            form = form_class(instance=company)
        
        # Use company-specific template for recruiters
        return render(request, 'companies/edit_profile.html', {
            'form': form,
            'is_recruiter': True
        })
    
    else:
        # Job Seeker: Edit user profile
        form_class = ProfileForm
        
        # Get or create the profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        if request.method == 'POST':
            form = form_class(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                try:
                    user_profile = form.save(commit=False)
                    user_profile.user = user
                    user_profile.save()
                    form.save_m2m()
                    messages.success(request, 'Profile saved successfully!')
                    return redirect('profiles:view_profile')
                except Exception as e:
                    messages.error(request, f'Error saving profile: {str(e)}')
                    print(f"Error: {e}")
            else:
                print("Form errors:", form.errors)
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            form = form_class(instance=profile)
        
        # Use profiles template for job seekers
        return render(request, 'profiles/edit_profile.html', {
            'form': form,
            'is_recruiter': False
        })