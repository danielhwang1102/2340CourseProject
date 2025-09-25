from django.urls import path
from . import views

urlpatterns = [
    # ...existing code...
    path('edit/', views.edit_profile, name='edit_profile'),
    path('view/', views.view_profile, name='view_profile'), 
]