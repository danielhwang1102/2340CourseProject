from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('apply/<int:job_pk>/', views.ApplicationCreateView.as_view(), name='apply'),
    path('my-applications/', views.ApplicationListView.as_view(), name='my_applications'),
    path('<int:pk>/withdraw/', views.WithdrawApplicationView.as_view(), name='withdraw'),
]