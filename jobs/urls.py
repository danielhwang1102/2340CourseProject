from django.urls import path
from .views import JobListView, JobDetailView

app_name = 'jobs'

urlpatterns = [
    path('', JobListView.as_view(), name='job_list'),
    path('<int:pk>/', JobDetailView.as_view(), name='job_detail'),
]