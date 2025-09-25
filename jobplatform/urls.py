from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from users.views import profile_completion_required
from users.views import DashboardRedirectView  

urlpatterns = [
    path('dashboard/', DashboardRedirectView.as_view(), name='dashboard'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('jobs/', include('jobs.urls')),
    path('applications/', include('applications.urls')),
    path('users/', include('users.urls')),
    path('profile-completion/', profile_completion_required, name='profile_completion'),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('profiles/', include(('profiles.urls', 'profiles'), namespace='profiles')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)