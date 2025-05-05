# mapping/web_urls.py

from django.urls import path
from . import views

app_name = 'mapping' # Namespace for the web URLs

urlpatterns = [
    path('', views.homepage_view, name='homepage'),
    path('add-background-image/', views.add_background_image_view, name='add_background_image'),
    path('on/<slug:image_slug>/', views.routes_on_image_view, name='routes_on_image'),

    # New URL for listing all routes for the user
    path('routes/', views.user_routes_list_view, name='user_routes_list'), # <-- Add this line

    # ... potentially more web URLs later ...
]