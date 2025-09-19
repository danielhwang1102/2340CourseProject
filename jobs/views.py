from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django_filters.views import FilterView
from .models import Job
from .filters import JobFilter
from applications.models import Application

class JobListView(FilterView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    filterset_class = JobFilter
    paginate_by = 12
    
    def get_queryset(self):
        return Job.objects.filter(is_active=True).select_related('company', 'posted_by').prefetch_related('required_skills')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_jobs'] = self.get_queryset().count()
        if self.request.user.is_authenticated:
            applied_jobs = Application.objects.filter(
                applicant=self.request.user
            ).values_list('job_id', flat=True)
            context['applied_jobs'] = list(applied_jobs)
        return context

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return Job.objects.filter(is_active=True).select_related('company', 'posted_by').prefetch_related('required_skills')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            context['user_has_applied'] = Application.objects.filter(
                job=self.object,
                applicant=self.request.user
            ).exists()
            
            # Recommend similar jobs
            if self.request.user.user_type == 'job_seeker':
                user_skills = self.request.user.profile.skills.all()
                similar_jobs = Job.objects.filter(
                    is_active=True,
                    required_skills__in=user_skills
                ).exclude(
                    id=self.object.id
                ).distinct()[:3]
                context['similar_jobs'] = similar_jobs
        else:
            context['user_has_applied'] = False
        
        return context