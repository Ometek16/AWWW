# mapping/test_api.py (or add to mapping/tests.py)

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.urls import reverse # Used to get URLs by name
from django.core.files.uploadedfile import SimpleUploadedFile # Needed for dummy image file

from .models import BackgroundImage, Route

# Get the User model
User = get_user_model()

class RouteApiTests(APITestCase):
    """
    Integration tests for the Route API endpoints (/api/routes/).
    Focuses on authentication and object-level permissions.
    """

    def setUp(self):
        """
        Set up test data and API clients.
        """
        # Standard API client instance
        self.client = APIClient()

        # Create users and get their tokens
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.another_user = User.objects.create_user(username='anotheruser', password='anotherpassword')
        self.another_token = Token.objects.create(user=self.another_user)

        # Client authenticated for self.user
        self.authenticated_client = APIClient()
        self.authenticated_client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Client authenticated for another_user
        self.another_authenticated_client = APIClient()
        self.another_authenticated_client.credentials(HTTP_AUTHORIZATION='Token ' + self.another_token.key)

        # Need a background image as a ForeignKey for Route
        # Create a dummy image file for the ImageField
        dummy_image = SimpleUploadedFile(
            name='test_map.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        self.bg_image = BackgroundImage.objects.create(name='Test Map', image=dummy_image)
        # For simplicity, let's assume one background image is enough for route creation tests.
        # In a real app, you might test selecting different images.

        # Create routes for each user using the same background image
        self.my_route = Route.objects.create(user=self.user, background_image=self.bg_image, name='My Awesome Route')
        self.another_users_route = Route.objects.create(user=self.another_user, background_image=self.bg_image, name='Their Boring Route')

        # Get API URLs using reverse names from the router in mapping/urls.py
        # The basename='route' in the router provides names like 'route-list', 'route-detail'
        self.routes_list_url = reverse('route-list') # /api/routes/
        self.my_route_detail_url = reverse('route-detail', kwargs={'pk': self.my_route.pk}) # /api/routes/my_route_id/
        self.another_routes_detail_url = reverse('route-detail', kwargs={'pk': self.another_users_route.pk}) # /api/routes/another_route_id/


    # --- Authentication Tests ---

    def test_list_routes_requires_authentication(self):
        """Ensure GET /api/routes/ requires authentication."""
        response = self.client.get(self.routes_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_route_requires_authentication(self):
        """Ensure POST /api/routes/ requires authentication."""
        data = {'name': 'Unauthorized Route', 'background_image_id': self.bg_image.pk}
        response = self.client.post(self.routes_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Also verify the route was NOT created
        self.assertEqual(Route.objects.count(), 2) # Still only the two created in setUp

    def test_retrieve_route_requires_authentication(self):
        """Ensure GET /api/routes/{id}/ requires authentication."""
        response = self.client.get(self.my_route_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_route_requires_authentication(self):
        """Ensure DELETE /api/routes/{id}/ requires authentication."""
        response = self.client.delete(self.my_route_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    # --- Creation Test (Authenticated) ---

    def test_create_route_authenticated(self):
        """Authenticated user can create a route."""
        data = {'name': 'New Route From API', 'background_image_id': self.bg_image.pk}
        response = self.authenticated_client.post(self.routes_list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # We started with 2 routes in setUp, should be 3 now
        self.assertEqual(Route.objects.count(), 3)
        self.assertEqual(response.data['name'], 'New Route From API')
        # The 'user' field IS included in the response data (it's not write_only)
        self.assertEqual(response.data['user'], self.user.pk)

        # --- REMOVE the assertion that caused the error: ---
        # self.assertEqual(response.data['background_image_id'], self.bg_image.pk) # This field is write_only

        # --- ADD this check: Fetch the object from the DB and verify the relation ---
        new_route_id = response.data['id'] # Get the ID from the response
        new_route = Route.objects.get(pk=new_route_id) # Fetch the newly created route
        self.assertEqual(new_route.background_image, self.bg_image) # Assert the relation is correct in the database

        # Optional: You could still check that the read-only nested details are there
        self.assertIsNotNone(response.data.get('background_image_details'))
        self.assertEqual(response.data['background_image_details']['id'], self.bg_image.pk)


    # --- Permission/Ownership Tests ---

    def test_list_routes_only_returns_own_routes(self):
        """Authenticated user only sees their own routes in the list."""
        response = self.authenticated_client.get(self.routes_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data), 1) # Should only see their own route
        self.assertEqual(response_data[0]['id'], self.my_route.pk)
        self.assertEqual(response_data[0]['name'], 'My Awesome Route')

        # Check the other user's perspective
        response_another = self.another_authenticated_client.get(self.routes_list_url)
        self.assertEqual(response_another.status_code, status.HTTP_200_OK)
        response_data_another = response_another.json()
        self.assertEqual(len(response_data_another), 1) # Should only see their own route
        self.assertEqual(response_data_another[0]['id'], self.another_users_route.pk)


    def test_retrieve_own_route_authenticated(self):
        """Authenticated user can retrieve their own route detail."""
        response = self.authenticated_client.get(self.my_route_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.my_route.pk)
        self.assertEqual(response.data['name'], 'My Awesome Route')
        # Check nested background image details are included (read_only=True)
        self.assertIsNotNone(response.data['background_image_details'])
        self.assertEqual(response.data['background_image_details']['id'], self.bg_image.pk)
        # Check nested points are included (read_only=True), should be empty list initially
        self.assertEqual(response.data['points'], [])


    def test_retrieve_another_users_route_returns_404(self):
        """Authenticated user cannot retrieve another user's route."""
        response = self.authenticated_client.get(self.another_routes_detail_url)
        # Due to get_queryset filtering combined with get_object_or_404,
        # attempting to retrieve an object outside the user's queryset results in 404.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_update_own_route_authenticated(self):
        """Authenticated user can update their own route."""
        # Note: We used PUT/PATCH in the serializer/viewset implicitly via ModelViewSet,
        # but we haven't explicitly tested it until now.
        updated_data = {'name': 'My Updated Route Name', 'description': 'New description'}
        response = self.authenticated_client.patch(self.my_route_detail_url, updated_data, format='json') # Use PATCH for partial update

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'My Updated Route Name')
        self.assertEqual(response.data['description'], 'New description')

        # Verify database updated
        self.my_route.refresh_from_db()
        self.assertEqual(self.my_route.name, 'My Updated Route Name')
        self.assertEqual(self.my_route.description, 'New description')


    def test_update_another_users_route_returns_404(self):
        """Authenticated user cannot update another user's route."""
        updated_data = {'name': 'Attempted Hack'}
        response = self.authenticated_client.patch(self.another_routes_detail_url, updated_data, format='json')
        # Again, 404 because the object is not in the user's queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify the other user's route was NOT updated
        self.another_users_route.refresh_from_db()
        self.assertEqual(self.another_users_route.name, 'Their Boring Route') # Original name


    def test_delete_own_route_authenticated(self):
        """Authenticated user can delete their own route."""
        # Check route exists before deletion
        self.assertTrue(Route.objects.filter(pk=self.my_route.pk).exists())

        response = self.authenticated_client.delete(self.my_route_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT) # Success, no content returned

        # Verify route is deleted from the database
        self.assertFalse(Route.objects.filter(pk=self.my_route.pk).exists())
        # Total routes should be 1 now (only the another_users_route remains)
        self.assertEqual(Route.objects.count(), 1)


    def test_delete_another_users_route_returns_404(self):
        """Authenticated user cannot delete another user's route."""
        # Check route exists before attempt
        self.assertTrue(Route.objects.filter(pk=self.another_users_route.pk).exists())

        response = self.authenticated_client.delete(self.another_routes_detail_url)

        # Again, 404 because the object is not in the user's queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify the other user's route was NOT deleted
        self.assertTrue(Route.objects.filter(pk=self.another_users_route.pk).exists())
        self.assertEqual(Route.objects.count(), 2) # Count remains the same


    # Note: You would add similar tests for RoutePoint endpoints (/api/routes/{route_pk}/points/ and /api/routes/{route_pk}/points/{pk}/)
    # ensuring:
    # - Authentication is required
    # - User can create/list/retrieve/update/delete points ONLY on routes they own
    # - Attempting to interact with points on another user's route (even if providing a valid point ID)
    #   returns 404 because the parent route is filtered by ownership in get_queryset.