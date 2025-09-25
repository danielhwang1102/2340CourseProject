from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q, Count

from .models import Job
from .forms import JobForm, JobFilterForm
from applications.models import Application


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
            qs = qs.filter(location__icontains=location)

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