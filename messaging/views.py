from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as flash_messages
from django.db.models import Q, Count, Max
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .forms import MessageForm, ComposeMessageForm
from notifications.models import Notification

User = get_user_model()


@login_required
def inbox(request):
    """
    Display all conversations for the current user.
    User Story #13: Internal messaging inbox
    """
    conversations = Conversation.get_user_conversations(request.user)
    
    # Annotate with unread count and last message time
    conversations_data = []
    for conv in conversations:
        other_participant = conv.get_other_participant(request.user)
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(request.user)
        
        conversations_data.append({
            'conversation': conv,
            'other_participant': other_participant,
            'last_message': last_message,
            'unread_count': unread_count,
        })
    
    context = {
        'conversations_data': conversations_data,
        'total_unread': sum(c['unread_count'] for c in conversations_data),
    }
    
    return render(request, 'messaging/inbox.html', context)


@login_required
def conversation_thread(request, conversation_id):
    """
    Display a specific conversation thread and handle message sending.
    User Story #13: View and send messages in a conversation
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is part of this conversation
    if request.user not in [conversation.participant1, conversation.participant2]:
        flash_messages.error(request, 'You do not have access to this conversation.')
        return redirect('messaging:inbox')
    
    # Get the other participant
    other_participant = conversation.get_other_participant(request.user)
    
    # Mark all messages from other participant as read
    Message.objects.filter(
        conversation=conversation,
        sender=other_participant,
        is_read=False
    ).update(is_read=True)
    
    # Handle message sending
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            # Update conversation timestamp
            conversation.save()  # This updates 'updated_at'
            
            # Create notification for recipient
            Notification.objects.create(
                recipient=other_participant,  # ← Changed from 'user' to 'recipient'
                notification_type='message',
                title='New Message',
                message=f'{request.user.get_full_name() or request.user.username} sent you a message'
                # ← Removed 'link' field (doesn't exist in your model)
            )
            
            flash_messages.success(request, 'Message sent successfully!')
            return redirect('messaging:conversation_thread', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    # Get all messages in conversation (ordered newest first, then reverse for display)
    messages_list = conversation.messages.select_related('sender').order_by('created_at')
    
    context = {
        'conversation': conversation,
        'other_participant': other_participant,
        'messages': messages_list,
        'form': form,
    }
    
    return render(request, 'messaging/thread.html', context)


@login_required
def compose_message(request, username=None):
    """
    Compose a new message to a user.
    User Story #13: Start a new conversation
    """
    recipient = None
    if username:
        recipient = get_object_or_404(User, username=username)
        
        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            Q(participant1=request.user, participant2=recipient) |
            Q(participant1=recipient, participant2=request.user)
        ).first()
        
        if existing_conversation:
            return redirect('messaging:conversation_thread', conversation_id=existing_conversation.id)
    
    if request.method == 'POST':
        form = ComposeMessageForm(request.POST)
        if form.is_valid():
            recipient_username = form.cleaned_data['recipient_username']
            content = form.cleaned_data['content']
            
            try:
                recipient = User.objects.get(username=recipient_username)
                
                if recipient == request.user:
                    flash_messages.error(request, 'You cannot send a message to yourself.')
                    return redirect('messaging:compose')
                
                # Create or get conversation
                conversation = Conversation.get_or_create_conversation(request.user, recipient)
                
                # Create message
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content
                )
                
                # Create notification
                Notification.objects.create(
                    recipient=recipient,  # ← Changed from 'user' to 'recipient'
                    notification_type='message',
                    title='New Message',
                    message=f'{request.user.get_full_name() or request.user.username} sent you a message'
                    # ← Removed 'link' field (doesn't exist in your model)
                )
                
                flash_messages.success(request, f'Message sent to {recipient.username}!')
                return redirect('messaging:conversation_thread', conversation_id=conversation.id)
                
            except User.DoesNotExist:
                flash_messages.error(request, f'User "{recipient_username}" not found.')
    else:
        initial_data = {}
        if recipient:
            initial_data['recipient_username'] = recipient.username
        form = ComposeMessageForm(initial=initial_data)
    
    context = {
        'form': form,
        'recipient': recipient,
    }
    
    return render(request, 'messaging/compose.html', context)


@login_required
def delete_conversation(request, conversation_id):
    """
    Delete a conversation (only for the current user's view).
    In a real app, you might want to implement soft delete.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is part of this conversation
    if request.user not in [conversation.participant1, conversation.participant2]:
        flash_messages.error(request, 'You do not have access to this conversation.')
        return redirect('messaging:inbox')
    
    if request.method == 'POST':
        conversation.delete()
        flash_messages.success(request, 'Conversation deleted successfully!')
        return redirect('messaging:inbox')
    
    return render(request, 'messaging/confirm_delete.html', {'conversation': conversation})


@login_required
def get_unread_count(request):
    """
    API endpoint to get unread message count (for AJAX requests).
    """
    conversations = Conversation.get_user_conversations(request.user)
    total_unread = sum(conv.get_unread_count(request.user) for conv in conversations)
    
    return JsonResponse({'unread_count': total_unread})