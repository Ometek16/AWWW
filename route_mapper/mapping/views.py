from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.db import models

from .models import BackgroundImage, Route, RoutePoint
from .forms import BackgroundImageForm
from .serializers import RouteSerializer, RoutePointSerializer

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

import random


# --- Keep your existing homepage_view here ---
def homepage_view(request):
    """
    Displays a list of random background images on the homepage.
    """
    all_images = BackgroundImage.objects.all()
    image_list = list(all_images) # Evaluate queryset before shuffling
    random_images = random.sample(image_list, min(len(image_list), 9)) # Get up to 9

    context = {
        'random_images': random_images,
    }
    return render(request, 'mapping/homepage.html', context)
# --------------------------------------------


@login_required # Ensures only logged-in users can access this view
def add_background_image_view(request):
    """
    Handles displaying and processing the form for uploading a new background image.
    Sets the uploader to the current logged-in user.
    """
    if request.method == 'POST':
        form = BackgroundImageForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the form data to create a BackgroundImage instance,
            # but don't commit to the database yet.
            background_image = form.save(commit=False)
            # Set the uploader field to the current logged-in user
            background_image.uploader = request.user
            # Now save the instance to the database
            # The model's save method will handle slug generation here
            background_image.save()

            # Redirect to a success page or another relevant page
            # Using reverse_lazy is preferred for redirects within views/forms
            return redirect(reverse_lazy('mapping:homepage')) # Redirect to homepage for now

    else: # GET request
        form = BackgroundImageForm() # Create an empty form for displaying

    context = {
        'form': form,
    }
    return render(request, 'mapping/add_background_image.html', context)

@login_required # This page requires the user to be logged in
def routes_on_image_view(request, image_slug):
    """
    Displays a specific background image and the logged-in user's routes on it.
    """
    # Retrieve the background image based on the slug, or return 404 if not found
    background_image = get_object_or_404(BackgroundImage, slug=image_slug)

    # Retrieve all Route objects associated with this specific image
    # AND the currently logged-in user.
    user_routes_on_image = Route.objects.filter(
        background_image=background_image,
        user=request.user
    )

    context = {
        'background_image': background_image,
        'user_routes_on_image': user_routes_on_image,
        # We'll add route points data here later, potentially via the API or direct query
        # 'route_points_data': ...
    }
    return render(request, 'mapping/route_management.html', context)


@login_required # Requires login to see user's routes list
def user_routes_list_view(request):
    """
    Displays a list of all routes belonging to the authenticated user,
    across all background images.
    """
    # Get all routes for the current logged-in user
    # The related_name='routes' on the user field in the Route model is used here
    user_routes = request.user.routes.all().order_by('-created_at') # Order by creation date, newest first

    context = {
        'user_routes': user_routes,
    }
    return render(request, 'mapping/user_routes_list.html', context)


# --- API ViewSets ---

# Route ViewSet (Keep existing RouteViewSet)
class RouteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows routes to be viewed or edited.
    Limited to routes owned by the authenticated user.
    """
    serializer_class = RouteSerializer
    # permission_classes = [IsAuthenticated] # Explicitly mention if needed

    def get_queryset(self):
        """
        Return a list of all the routes for the currently authenticated user.
        """
        if self.request.user.is_authenticated:
            return self.request.user.routes.all().order_by('-created_at')
        return Route.objects.none()

    def perform_create(self, serializer):
        """
        Sets the user field to the current authenticated user when creating a route.
        """
        serializer.save(user=self.request.user)


# Route Point ViewSet (Nested under Route)
class RoutePointViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows route points to be viewed, added, updated, or deleted.
    Nested under a specific route (/api/routes/{route_pk}/points/).
    Limited to points on routes owned by the authenticated user.
    """
    serializer_class = RoutePointSerializer
    # permission_classes = [IsAuthenticated] # Default IsAuthenticated applies

    def get_queryset(self):
        """
        This view should return a list of all the points
        for the route specified in the URL, ensuring the route belongs
        to the authenticated user.
        """
        # Get the route_pk from the URL keyword arguments
        route_pk = self.kwargs.get('route_pk')

        # Filter routes by the authenticated user AND the route_pk
        # Using get_object_or_404 simplifies handling non-existent routes or routes
        # not owned by the user (will return 404).
        # Using filter().first() + check could return 403 if needed.
        # Let's use get_object_or_404 for simplicity as a non-existent *user-owned*
        # route resource should appear as Not Found.
        route = get_object_or_404(Route.objects.filter(user=self.request.user), pk=route_pk)

        # Return the points for this specific route, ordered by 'order' (Meta class default)
        return route.points.all()


    def perform_create(self, serializer):
        """
        Sets the route and the order field for a new route point.
        """
        # Get the route_pk from the URL keyword arguments
        route_pk = self.kwargs.get('route_pk')

        # Fetch the Route object again, ensuring it belongs to the user
        route = get_object_or_404(Route.objects.filter(user=self.request.user), pk=route_pk)

        # Determine the next sequential order number for this route's points
        # Get the highest existing order number for this route
        # Use 0 if no points exist yet.
        highest_order = route.points.aggregate(models.Max('order'))['order__max']
        next_order = (highest_order or -1) + 1  # Start with 0 if max is None (first point)

        # Check if the next_order value already exists in the route's points
        while route.points.filter(order=next_order).exists():
            next_order += 1  # Increment order until it's unique

        # Save the serializer, associating the point with the fetched route
        # and setting the determined order.
        # The serializer's validated_data already contains x and y.
        serializer.save(route=route, order=next_order)

    # Optional: Override perform_destroy to re-order points after deletion if needed
    # This adds complexity. A simpler approach is to leave gaps or re-order client-side
    # on retrieve and only renumber in a specific reorder API call.
    # Given "Simple Sequential" order logic decision, reordering on delete *is* required
    # for strict sequential ordering without gaps.

    def perform_destroy(self, instance):
        """
        Deletes the point and re-orders subsequent points for the same route.
        """
        # Get the route before deletion
        route = instance.route
        deleted_order = instance.order

        # Delete the instance
        instance.delete()

        # Renumber points after the deleted point
        # Retrieve points for the route that had an order greater than the deleted one
        points_to_renumber = route.points.filter(order__gt=deleted_order).order_by('order')

        # Update the order of subsequent points
        for i, point in enumerate(points_to_renumber):
            point.order = deleted_order + i # Assign new sequential order
            point.save()