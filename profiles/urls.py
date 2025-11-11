from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('edit/', views.edit_profile, name='edit_profile'),
    path('view/', views.view_profile, name='view_profile'), 
    path('recommendations/', views.recommend_jobs, name='recommend_jobs'),
    
    # Privacy Settings
    path('privacy-settings/', views.privacy_settings, name='privacy_settings'),
    
    # Recruiter candidate search
    path('search/', views.search_candidates, name='search_candidates'),
    path('candidate/<int:profile_id>/', views.candidate_detail, name='candidate_detail'),
    
    # Saved Searches (NEW - User Story #15)
    path('saved-searches/', views.saved_searches, name='saved_searches'),
    path('save-search/', views.save_search, name='save_search'),
    path('saved-search/<int:search_id>/run/', views.run_saved_search, name='run_saved_search'),
    path('saved-search/<int:search_id>/edit/', views.edit_saved_search, name='edit_saved_search'),
    path('saved-search/<int:search_id>/delete/', views.delete_saved_search, name='delete_saved_search'),
]