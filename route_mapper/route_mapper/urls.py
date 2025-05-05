# route_mapper/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    # Include web application URLs (with namespace)
    path('', include('mapping.web_urls', namespace='mapping')), # Assuming mapping.web_urls exists

    # Include API URLs under the /api/ prefix
    path('api/', include('mapping.urls')), # Assuming mapping.urls contains only API router URLs
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
