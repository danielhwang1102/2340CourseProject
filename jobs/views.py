from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
import json

from django.db.models import Count, Q, Case, When, IntegerField, F
from profiles.models import Profile
from applications.models import Application
import math
import math

from .models import Job
from .forms import JobForm, JobFilterForm
from applications.models import Application

from profiles.models import Profile


class RecruiterRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'user_type', '') == 'recruiter'

    def handle_no_permission(self):
        messages.error(self.request, 'Only recruiters can access this page.')
        return redirect('home')


class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 12

    def get_queryset(self):
        qs = Job.objects.filter(is_active=True).select_related('posted_by').prefetch_related('required_skills')
        params = self.request.GET

        q = params.get('q') or ''
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(company_name__icontains=q)
            )

        location = params.get('location') or ''
        if location:
            qs = qs.filter(
                Q(city__icontains=location) |
                Q(state_province__icontains=location) |
                Q(country__icontains=location) |
                Q(street_address__icontains=location)
            )

        job_type = params.get('job_type') or ''
        if job_type:
            qs = qs.filter(job_type=job_type)

        location_type = params.get('location_type') or ''
        if location_type:
            qs = qs.filter(location_type=location_type)

        experience_level = params.get('experience_level') or ''
        if experience_level:
            qs = qs.filter(experience_level=experience_level)

        # Salary filters (inclusive)
        salary_min = params.get('salary_min')
        salary_max = params.get('salary_max')
        if salary_min:
            try:
                v = int(salary_min)
                qs = qs.filter(Q(salary_min__gte=v) | Q(salary_max__gte=v))
            except ValueError:
                pass
        if salary_max:
            try:
                v = int(salary_max)
                qs = qs.filter(Q(salary_max__lte=v) | Q(salary_min__lte=v))
            except ValueError:
                pass

        visa = params.get('visa_sponsorship')
        if visa == 'yes':
            qs = qs.filter(visa_sponsorship=True)
        elif visa == 'no':
            qs = qs.filter(visa_sponsorship=False)

        # Skills (list of IDs)
        skill_ids = params.getlist('skills')
        if skill_ids:
            qs = qs.filter(required_skills__in=skill_ids).distinct()

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = JobFilterForm(self.request.GET or None)
        context['filter_form'] = form

        # Preserve filters in pagination links
        qd = self.request.GET.copy()
        qd.pop('page', None)
        context['current_query'] = qd.urlencode()

        context['result_count'] = self.get_queryset().count()
        return context


class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and getattr(self.request.user, 'user_type', '') == 'job_seeker':
            context['user_has_applied'] = Application.objects.filter(
                job=self.object,
                applicant=self.request.user
            ).exists()
        else:
            context['user_has_applied'] = False
        return context


class JobCreateView(LoginRequiredMixin, RecruiterRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Job "{self.object.title}" has been posted successfully!')
        return response

    def get_success_url(self):
        return reverse_lazy('jobs:my_jobs')


class JobUpdateView(LoginRequiredMixin, RecruiterRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Job "{self.object.title}" has been updated successfully!')
        return response

    def get_success_url(self):
        return reverse_lazy('jobs:job_detail', kwargs={'pk': self.object.pk})


class JobDeleteView(LoginRequiredMixin, RecruiterRequiredMixin, DeleteView):
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('jobs:my_jobs')

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Job "{self.get_object().title}" has been deleted.')
        return super().delete(request, *args, **kwargs)


class MyJobsView(LoginRequiredMixin, RecruiterRequiredMixin, ListView):
    model = Job
    template_name = 'jobs/my_jobs.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        return Job.objects.filter(
            posted_by=self.request.user
        ).annotate(
            application_count=Count('applications')
        ).order_by('-created_at')


class JobApplicationsView(LoginRequiredMixin, RecruiterRequiredMixin, DetailView):
    model = Job
    template_name = 'jobs/job_applications.html'
    context_object_name = 'job'

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['applications'] = Application.objects.filter(
            job=self.object
        ).select_related('applicant').order_by('-applied_date')
        return context
    
class JobMapView(TemplateView):
    template_name = 'jobs/job_map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get jobs with coordinates
        jobs_with_coords = Job.objects.filter(
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('posted_by')[:200]

        # Prepare data for JavaScript
        job_data = []
        for job in jobs_with_coords:
            job_data.append({
                'id': job.id,
                'title': job.title,
                'company': job.get_company_name(),
                'short_location': job.get_short_location(),  # CHANGED: Use get_short_location()
                'latitude': float(job.latitude),
                'longitude': float(job.longitude),
                'job_type': job.get_job_type_display(),
                'location_type': job.get_location_type_display(),
                'salary': job.get_salary_display(),
                'url': job.get_absolute_url(),
            })

        context['jobs_json'] = json.dumps(job_data)
        context['total_jobs'] = len(job_data)
        
        # Calculate center point
        if job_data:
            avg_lat = sum(j['latitude'] for j in job_data) / len(job_data)
            avg_lng = sum(j['longitude'] for j in job_data) / len(job_data)
            context['center_lat'] = avg_lat
            context['center_lng'] = avg_lng
        else:
            context['center_lat'] = 37.7749
            context['center_lng'] = -122.4194
        
        return context


class JobMapDataAPIView(LoginRequiredMixin, View):
    """AJAX endpoint for filtering jobs on map by distance"""
    
    def get(self, request):
        user_lat = request.GET.get('lat')
        user_lng = request.GET.get('lng')
        radius_km = request.GET.get('radius', 25)  # Default 25km
        
        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
            radius_km = float(radius_km)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid coordinates'}, status=400)
        
        # Get all jobs with coordinates
        jobs = Job.objects.filter(
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Filter by distance
        filtered_jobs = []
        for job in jobs:
            distance = job.get_distance_from(user_lat, user_lng)
            if distance and distance <= radius_km:
                filtered_jobs.append({
                    'id': job.id,
                    'title': job.title,
                    'company': job.get_company_name(),
                    'location': job.location,
                    'latitude': float(job.latitude),
                    'longitude': float(job.longitude),
                    'distance': round(distance, 2),
                    'url': job.get_absolute_url(),
                })
        
        return JsonResponse({'jobs': filtered_jobs})
    
class ApplicantMapView(LoginRequiredMixin, RecruiterRequiredMixin, DetailView):
    """
    User Story #18: Show applicants on a map with clustering.
    Only accessible by the recruiter who posted the job.
    """
    model = Job
    template_name = 'jobs/applicant_map.html'
    context_object_name = 'job'

    def get_queryset(self):
        # Only allow viewing applicants for own jobs
        return Job.objects.filter(posted_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all applications for this job
        applications = Application.objects.filter(
            job=self.object
        ).select_related('applicant', 'applicant__profile').order_by('-applied_date')
        
        # Prepare applicant data with locations
        applicant_data = []
        total_applicants = 0
        applicants_with_location = 0
        
        for app in applications:
            total_applicants += 1
            profile = getattr(app.applicant, 'profile', None)
            
            # Only include applicants with location data
            if profile and profile.latitude and profile.longitude:
                applicants_with_location += 1
                applicant_data.append({
                    'id': app.id,
                    'applicant_id': app.applicant.id,
                    'name': app.applicant.get_full_name() or app.applicant.username,
                    'username': app.applicant.username,
                    'location': profile.location or 'Location not specified',
                    'latitude': float(profile.latitude),
                    'longitude': float(profile.longitude),
                    'status': app.status,
                    'status_display': app.get_status_display(),
                    'applied_date': app.applied_date.strftime('%b %d, %Y'),
                    'profile_url': profile.get_absolute_url(),
                    'headline': profile.headline or 'No headline',
                    'years_experience': profile.years_experience,
                })
        
        context['applicants_json'] = json.dumps(applicant_data)
        context['total_applicants'] = total_applicants
        context['applicants_with_location'] = applicants_with_location
        context['applicants_without_location'] = total_applicants - applicants_with_location
        
        # Calculate map center
        if applicant_data:
            avg_lat = sum(a['latitude'] for a in applicant_data) / len(applicant_data)
            avg_lng = sum(a['longitude'] for a in applicant_data) / len(applicant_data)
            context['center_lat'] = avg_lat
            context['center_lng'] = avg_lng
            context['default_zoom'] = 6
        elif self.object.latitude and self.object.longitude:
            # Center on job location if no applicants with location
            context['center_lat'] = float(self.object.latitude)
            context['center_lng'] = float(self.object.longitude)
            context['default_zoom'] = 10
        else:
            # Default to US center
            context['center_lat'] = 39.8283
            context['center_lng'] = -98.5795
            context['default_zoom'] = 4
        
        # Add job location for reference
        if self.object.latitude and self.object.longitude:
            context['job_location'] = {
                'latitude': float(self.object.latitude),
                'longitude': float(self.object.longitude),
                'name': self.object.get_short_location(),
            }
        
        return context
    
class JobCandidateRecommendationsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display recommended candidates for a specific job posting.
    Only accessible to the recruiter who posted the job.
    """
    model = Job
    template_name = 'jobs/job_recommendations.html'
    context_object_name = 'job'
    
    def test_func(self):
        """Ensure only the job poster (recruiter) can view recommendations"""
        job = self.get_object()
        return (
            self.request.user == job.posted_by and 
            self.request.user.user_type == 'recruiter'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        
        # Get filter parameters from request
        min_match = int(self.request.GET.get('min_match', 60))
        max_distance = int(self.request.GET.get('max_distance', 100))
        open_to_work_only = self.request.GET.get('open_to_work', '') == 'true'
        sort_by = self.request.GET.get('sort', 'match')  # match, distance, experience
        
        # Get job's required skills
        job_skill_ids = list(job.required_skills.values_list('id', flat=True))
        
        # Get candidates who haven't applied yet
        applied_user_ids = Application.objects.filter(job=job).values_list('applicant_id', flat=True)
        
        # Base queryset: public profiles, job seekers, haven't applied
        candidates = Profile.objects.filter(
            user__user_type='job_seeker',
            visibility='public'
        ).exclude(
            user_id__in=applied_user_ids
        ).select_related('user').prefetch_related('skills')
        
        # Filter by open_to_work if requested
        if open_to_work_only:
            candidates = candidates.filter(open_to_work=True)
        
        # Calculate match scores for each candidate
        recommendations = []
        
        for profile in candidates:
            # Calculate match score
            match_data = self.calculate_match_score(job, profile, job_skill_ids)
            
            # Skip if below minimum match threshold
            if match_data['total_score'] < min_match:
                continue
            
            # Skip if beyond maximum distance (if both have locations)
            if match_data['distance'] is not None and match_data['distance'] > max_distance:
                continue
            
            recommendations.append({
                'profile': profile,
                'user': profile.user,
                'match_score': match_data['total_score'],
                'skill_score': match_data['skill_score'],
                'location_score': match_data['location_score'],
                'experience_score': match_data['experience_score'],
                'matched_skills': match_data['matched_skills'],
                'missing_skills': match_data['missing_skills'],
                'distance': match_data['distance'],
                'distance_km': match_data['distance'],
                'distance_miles': round(match_data['distance'] * 0.621371, 1) if match_data['distance'] else None,
            })
        
        # Sort recommendations
        if sort_by == 'distance' and job.latitude:
            recommendations.sort(key=lambda x: x['distance'] if x['distance'] is not None else 999999)
        elif sort_by == 'experience':
            recommendations.sort(key=lambda x: x['profile'].years_experience or 0, reverse=True)
        else:  # default: sort by match score
            recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Limit to top 20 candidates
        recommendations = recommendations[:20]
        
        # Add to context
        context['recommendations'] = recommendations
        context['total_candidates'] = len(recommendations)
        context['min_match'] = min_match
        context['max_distance'] = max_distance
        context['open_to_work_only'] = open_to_work_only
        context['sort_by'] = sort_by
        
        return context
    
    def calculate_match_score(self, job, profile, job_skill_ids):
        """
        Calculate match score between job and candidate profile.
        Returns score from 0-100 based on skills, location, and experience.
        """
        total_score = 0
        skill_score = 0
        location_score = 0
        experience_score = 0
        distance = None
        
        # 1. SKILLS MATCH (50 points max)
        matched_skills = []
        missing_skills = []
        
        if job_skill_ids:
            candidate_skill_ids = set(profile.skills.values_list('id', flat=True))
            job_skills_set = set(job_skill_ids)
            
            matched_skill_ids = job_skills_set & candidate_skill_ids
            missing_skill_ids = job_skills_set - candidate_skill_ids
            
            # Get skill objects for display
            matched_skills = list(profile.skills.filter(id__in=matched_skill_ids))
            missing_skills = list(job.required_skills.filter(id__in=missing_skill_ids))
            
            # Calculate skill match percentage
            if len(job_skill_ids) > 0:
                skill_match_ratio = len(matched_skill_ids) / len(job_skill_ids)
                skill_score = skill_match_ratio * 50
                total_score += skill_score
        
        # 2. LOCATION MATCH (30 points max)
        if job.latitude and job.longitude and profile.latitude and profile.longitude:
            try:
                # Calculate distance using haversine formula
                distance = self.calculate_distance(
                    float(job.latitude), float(job.longitude),
                    float(profile.latitude), float(profile.longitude)
                )
                
                # Score: 30 points at 0km, linearly decreasing to 0 at 100km
                if distance <= 100:
                    location_score = 30 * (1 - distance / 100)
                    total_score += location_score
            except (ValueError, TypeError):
                pass
        
        # 3. EXPERIENCE MATCH (20 points max)
        if profile.years_experience is not None:
            candidate_exp = profile.years_experience
            
            # Map experience_level to approximate years
            exp_ranges = {
                'entry': (0, 2),
                'mid': (2, 5),
                'senior': (5, 10),
                'lead': (10, 999),
            }
            
            if job.experience_level in exp_ranges:
                min_exp, max_exp = exp_ranges[job.experience_level]
                
                if min_exp <= candidate_exp <= max_exp:
                    # Perfect match
                    experience_score = 20
                else:
                    # Calculate penalty based on distance from range
                    if candidate_exp < min_exp:
                        diff = min_exp - candidate_exp
                    else:
                        diff = candidate_exp - max_exp
                    
                    # Deduct 2 points per year difference
                    experience_score = max(0, 20 - (diff * 2))
                
                total_score += experience_score
        
        return {
            'total_score': round(total_score, 1),
            'skill_score': round(skill_score, 1),
            'location_score': round(location_score, 1),
            'experience_score': round(experience_score, 1),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'distance': round(distance, 1) if distance else None,
        }
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two coordinates using Haversine formula.
        Returns distance in kilometers.
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance