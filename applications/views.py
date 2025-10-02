from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, DeleteView  # ← Add DeleteView import
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from jobs.models import Job
from .models import Application
from .forms import ApplicationForm
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render

class JobSeekerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'job_seeker'
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only job seekers can access this page.')
        return redirect('home')

class ApplicationCreateView(LoginRequiredMixin, JobSeekerRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'applications/apply.html'

    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(Job, pk=kwargs['job_pk'], is_active=True)
        
        # Check if already applied
        if Application.objects.filter(job=self.job, applicant=request.user).exists():
            messages.error(request, 'You have already applied to this job.')
            return redirect('jobs:job_detail', pk=self.job.pk)
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.job
        return context

    def form_valid(self, form):
        form.instance.applicant = self.request.user
        form.instance.job = self.job
        
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'Successfully applied to {self.job.title}!')
            return response
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('jobs:job_detail', kwargs={'pk': self.job.pk})

class ApplicationListView(LoginRequiredMixin, JobSeekerRequiredMixin, ListView):
    model = Application
    template_name = 'applications/my_applications.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        return Application.objects.filter(
            applicant=self.request.user
        ).select_related('job', 'job__company').order_by('-applied_date')

class WithdrawApplicationView(LoginRequiredMixin, JobSeekerRequiredMixin, DeleteView):
    model = Application
    template_name = 'applications/withdraw_confirm.html'
    success_url = reverse_lazy('applications:my_applications')
    
    def get_queryset(self):
        # Only allow users to withdraw their own applications
        return Application.objects.filter(applicant=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Your application has been withdrawn.')
        return super().delete(request, *args, **kwargs)


@require_POST
def update_application_status(request, pk):
    """Allow a recruiter who posted the job to update an application's status.

    Expects POST with 'status' and optional 'notes'.
    """
    application = get_object_or_404(Application, pk=pk)
    job = application.job

    # Only the recruiter who posted the job (or users of type 'recruiter') can update
    user = request.user
    if not user.is_authenticated or getattr(user, 'user_type', '') != 'recruiter':
        return HttpResponseForbidden('Only recruiters can update application status.')

    # Ensure the recruiter owns the job
    if job.posted_by != user:
        return HttpResponseForbidden('You do not have permission to modify this application.')

    status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    if status and status in dict(Application.STATUS_CHOICES):
        application.status = status
        application.notes = notes
        application.save()

    # Redirect back to the job applications page using named URL
    return redirect('jobs:job_applications', pk=job.pk)