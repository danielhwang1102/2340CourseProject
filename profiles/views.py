from django.shortcuts import render

import companies
from .forms import ProfileForm
from companies.forms import CompanyProfileForm
from companies.models import Company


# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

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