# board_crafter/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from mapping_tool import views as global_mapping_views
# Dodajemy import dla DRF UI login/logout (opcjonalne, ale przydatne)
from rest_framework.authtoken import views as authtoken_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', global_mapping_views.signup_view, name='signup'),

    path('app/', include('mapping_tool.urls')), # URL-e aplikacji (UI)

    # API URLs
    path('api/', include('mapping_tool.urls_api')), # Nasze główne API
    path('api-auth/', include('rest_framework.urls')), # Dla logowania/wylogowania w DRF Browsable API
    path('api-token-auth/', authtoken_views.obtain_auth_token, name='api_token_auth'), # Endpoint do uzyskiwania tokena

    path('', global_mapping_views.home_view, name='home'), # Strona główna na końcu, aby nie kolidowała
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)