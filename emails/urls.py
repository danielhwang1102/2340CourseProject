from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    path('send/<str:username>/', views.email_candidate, name='email_candidate'),
    path('history/', views.email_history, name='email_history'),
]