from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('apply/<int:job_pk>/', views.ApplicationCreateView.as_view(), name='apply'),
    path('my-applications/', views.ApplicationListView.as_view(), name='my_applications'),
    path('<int:pk>/withdraw/', views.WithdrawApplicationView.as_view(), name='withdraw'),
    path('<int:pk>/update-status/', views.update_application_status, name='update_status'),

    path('job/<int:job_pk>/pipeline/', views.JobPipelineView.as_view(), name='job_pipeline'),
    path('<int:pk>/update-status-ajax/', views.update_application_status_ajax, name='update_status_ajax'),
    
    # Applicants map for recruiters
    path('applicants-map/', views.ApplicantsMapView.as_view(), name='applicants_map'),
]