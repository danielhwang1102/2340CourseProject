from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import Q, Count
from .models import Job
from .forms import JobForm
from applications.models import Application

class RecruiterRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'recruiter'
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only recruiters can access this page.')
        return redirect('home')

# Existing views (updated)
class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 12
    
    def get_queryset(self):
        return Job.objects.filter(is_active=True).select_related('posted_by').prefetch_related('required_skills')

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has already applied
        if self.request.user.is_authenticated and self.request.user.user_type == 'job_seeker':
            context['user_has_applied'] = Application.objects.filter(
                job=self.object,
                applicant=self.request.user
            ).exists()
        else:
            context['user_has_applied'] = False
            
        return context

# NEW: Recruiter-specific views
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
        # Only allow editing own jobs
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
        # Only allow deleting own jobs
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