from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class ProfileCompletionMiddleware:
    """Ensure users complete their profiles before accessing the app"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs that don't require profile completion
        exempt_urls = [
            reverse('account_login'),
            reverse('account_logout'),
            reverse('account_signup'),
            reverse('profile_completion'),
            reverse('complete_job_seeker_profile'),
            reverse('complete_recruiter_profile'),
            '/admin/',
            '/accounts/',
        ]

        if (request.user.is_authenticated and 
            not request.user.profile_completed and 
            request.path not in exempt_urls and
            not any(request.path.startswith(url) for url in exempt_urls)):
            
            messages.info(request, 'Please complete your profile to continue.')
            return redirect('profile_completion')

        response = self.get_response(request)
        return response