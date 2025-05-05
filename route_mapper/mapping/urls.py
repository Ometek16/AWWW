# mapping/urls.py (This file contains only API URLs)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Import the ViewSets
from .views import RouteViewSet, RoutePointViewSet

# Create a router for top-level API endpoints (like /routes/)
router = DefaultRouter()
router.register(r'routes', RouteViewSet, basename='route')

# Manually define the nested URL patterns for RoutePointViewSet
# Use .as_view() to map HTTP methods to ViewSet actions for specific paths
urlpatterns = [
    # Include the router URLs first (e.g., /routes/, /routes/{id}/)
    *router.urls, # Uses iterable unpacking for Python 3.5+

    # URL pattern for listing points on a route and creating a new point
    # GET /api/routes/{route_pk}/points/ -> list
    # POST /api/routes/{route_pk}/points/ -> create
    path('routes/<int:route_pk>/points/',
         RoutePointViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='route-points-list'),

    # URL pattern for retrieving, updating, or deleting a specific point
    # GET /api/routes/{route_pk}/points/{pk}/ -> retrieve
    # PUT /api/routes/{route_pk}/points/{pk}/ -> update
    # PATCH /api/routes/{route_pk}/points/{pk}/ -> partial_update
    # DELETE /api/routes/{route_pk}/points/{pk}/ -> destroy
    path('routes/<int:route_pk>/points/<int:pk>/', # 'pk' is the default lookup field name for detail views
         RoutePointViewSet.as_view({'get': 'retrieve',
                                    'put': 'update',
                                    'patch': 'partial_update',
                                    'delete': 'destroy'}),
         name='route-point-detail'),
]

# Note: mapping/web_urls.py contains the web application URL patterns.
# Both are included in the project's route_mapper/urls.py under /api/ and / respectively.