# mapping_tool/urls_api.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api

router = DefaultRouter()
router.register(r'maps', views_api.MapViewSet, basename='map')
router.register(r'boards', views_api.BoardViewSet, basename='board') # Dodajemy BoardViewSet

urlpatterns = [
    path('', include(router.urls)),
]