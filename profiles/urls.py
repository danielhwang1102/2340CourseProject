from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('edit/', views.edit_profile, name='edit_profile'),
    path('view/', views.view_profile, name='view_profile'), 
    path('recommendations/', views.recommend_jobs, name='recommend_jobs'),
    
    # Privacy Settings (NEW)
    path('privacy-settings/', views.privacy_settings, name='privacy_settings'),
    
    # Recruiter candidate search
    path('search/', views.search_candidates, name='search_candidates'),
    path('candidate/<int:profile_id>/', views.candidate_detail, name='candidate_detail'),
]