from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Public job browsing
    path('', views.JobListView.as_view(), name='job_list'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    
    # Recruiter job management
    path('post/', views.JobCreateView.as_view(), name='job_create'),
    path('<int:pk>/edit/', views.JobUpdateView.as_view(), name='job_edit'),
    path('<int:pk>/delete/', views.JobDeleteView.as_view(), name='job_delete'),
    path('my-jobs/', views.MyJobsView.as_view(), name='my_jobs'),
    path('<int:pk>/applications/', views.JobApplicationsView.as_view(), name='job_applications'),
]