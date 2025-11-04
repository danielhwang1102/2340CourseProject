from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as flash_messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import EmailLog
from .forms import EmailCandidateForm

User = get_user_model()


@login_required
def email_candidate(request, username):
    """
    Send email to a candidate.
    User Story #14: Recruiters can email candidates
    """
    # Check if user is a recruiter
    if request.user.user_type != 'recruiter':
        flash_messages.error(request, 'Only recruiters can send emails through the platform.')
        return redirect('home')
    
    # Get the candidate
    recipient = get_object_or_404(User, username=username)
    
    # Check if recipient is a job seeker
    if recipient.user_type != 'job_seeker':
        flash_messages.error(request, 'You can only email job seekers.')
        return redirect('profiles:search_candidates')
    
    if request.method == 'POST':
        form = EmailCandidateForm(request.POST, sender=request.user, recipient=recipient)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Create email log
            email_log = form.save(commit=False)
            email_log.sender = request.user
            email_log.recipient = recipient
            
            try:
                # Render email template
                context = {
                    'sender_name': request.user.get_full_name() or request.user.username,
                    'sender_email': request.user.email,
                    'recipient_name': recipient.get_full_name() or recipient.username,
                    'subject': subject,
                    'message': message,
                    'site_name': 'JobPlatform',
                    'site_url': 'http://localhost:8000',
                }
                
                html_message = render_to_string('emails/candidate_email.html', context)
                plain_message = render_to_string('emails/candidate_email.txt', context)
                
                # Send email
                send_mail(
                    subject=f"[JobPlatform] {subject}",
                    message=plain_message,
                    from_email=settings.EMAIL_HOST_USER or 'noreply@jobplatform.com',
                    recipient_list=[recipient.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                email_log.was_successful = True
                flash_messages.success(request, f'Email sent successfully to {recipient.get_full_name() or recipient.username}!')
                
            except Exception as e:
                email_log.was_successful = False
                email_log.error_message = str(e)
                flash_messages.error(request, f'Failed to send email: {str(e)}')
            
            finally:
                email_log.save()
            
            # Redirect back to candidate profile
            try:
                return redirect('profiles:candidate_detail', pk=recipient.candidateprofile.id)
            except:
                return redirect('profiles:search_candidates')
    else:
        form = EmailCandidateForm(sender=request.user, recipient=recipient)
    
    context = {
        'form': form,
        'recipient': recipient,
    }
    
    return render(request, 'emails/email_form.html', context)


@login_required
def email_history(request):
    """
    View email history (sent and received).
    User Story #14: Track email communications
    """
    sent_emails = EmailLog.objects.filter(sender=request.user).select_related('recipient')
    received_emails = EmailLog.objects.filter(recipient=request.user).select_related('sender')
    
    context = {
        'sent_emails': sent_emails,
        'received_emails': received_emails,
    }
    
    return render(request, 'emails/email_history.html', context)