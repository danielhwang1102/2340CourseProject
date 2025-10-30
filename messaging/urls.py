from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:conversation_id>/', views.conversation_thread, name='conversation_thread'),
    path('compose/', views.compose_message, name='compose'),
    path('compose/<str:username>/', views.compose_message, name='compose_to_user'),
    path('<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
]