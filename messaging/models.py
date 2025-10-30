from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

class Conversation(models.Model):
    """Represents a conversation between two users"""
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='conversations_as_participant1'
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='conversations_as_participant2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['participant1', 'participant2']),
        ]
    
    def __str__(self):
        return f"Conversation between {self.participant1.username} and {self.participant2.username}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participant2 if self.participant1 == user else self.participant1
    
    def get_last_message(self):
        """Get the most recent message"""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count(self, user):
        """Get count of unread messages for a user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get existing conversation or create new one between two users"""
        # Ensure consistent ordering to avoid duplicates
        if user1.id > user2.id:
            user1, user2 = user2, user1
        
        conversation, created = cls.objects.get_or_create(
            participant1=user1,
            participant2=user2
        )
        return conversation
    
    @classmethod
    def get_user_conversations(cls, user):
        """Get all conversations for a user"""
        return cls.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ).select_related('participant1', 'participant2').prefetch_related('messages')


class Message(models.Model):
    """Individual message in a conversation"""
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['conversation', '-created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])