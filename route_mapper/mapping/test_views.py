# mapping/tests.py

from django.test import TestCase, Client # Import Client
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.utils.text import slugify
from django.urls import reverse # Import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import BackgroundImage, Route, RoutePoint

# Get the User model
User = get_user_model()

# Keep your ModelTests class here (from previous step)
class ModelTests(TestCase):
    # ... (your existing ModelTests code) ...
    pass # Placeholder


class WebViewTests(TestCase):
    """
    Integration tests for the Django web views in the mapping app.
    Uses Django's built-in test Client.
    """

    def setUp(self):
        """
        Set up test data and client before each test method.
        """
        # Use the default Django test client
        self.client = Client()

        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # Create dummy images for BackgroundImage tests
        # We'll need multiple images to test the random selection on the homepage
        from django.conf import settings
        import os
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        self.dummy_image_file = SimpleUploadedFile(
            name='dummy_image.jpg',
            content=b'dummy_image_content',
            content_type='image/jpeg'
        )
         # Create up to 10 images to test the 'up to 9 random' logic
        for i in range(10):
             img_name = f'Homepage Image {i+1}'
             img_slug = slugify(img_name) # Manually create slugs for simplicity
             # Create images directly without auto-slug logic for setup
             # Note: If BackgroundImage save() auto-slugs, make sure it handles existing slugs
             # The model's save method should handle this.
             # Let's create them via objects.create() which calls save()
             BackgroundImage.objects.create(
                 name=img_name,
                 # Use a new SimpleUploadedFile instance each time if testing image field saving thoroughly
                 # Or reuse a dummy one if just testing model creation/retrieval
                 image=SimpleUploadedFile(f'homepage_img_{i+1}.jpg', b'img content'),
                 uploader=self.user
             )

        # Create a route for the user (useful for testing route list page later)
        self.bg_image_for_route = BackgroundImage.objects.order_by('?').first() # Get one of the images
        if self.bg_image_for_route:
             self.user_route = Route.objects.create(user=self.user, background_image=self.bg_image_for_route, name='My First Web Route')
        else:
             # Handle case where no background images were created (shouldn't happen with the loop above)
             self.bg_image_for_route = BackgroundImage.objects.create(name='Single Image', image=SimpleUploadedFile('single.jpg', b'content'))
             self.user_route = Route.objects.create(user=self.user, background_image=self.bg_image_for_route, name='My First Web Route')


        # Get URLs using named patterns
        self.homepage_url = reverse('mapping:homepage')
        self.add_image_url = reverse('mapping:add_background_image')
        self.login_url = reverse('login') # From django.contrib.auth.urls


    # --- Homepage Tests (/ - mapping:homepage) ---

    def test_homepage_loads_successfully_anonymous(self):
        """Homepage loads successfully for anonymous users."""
        response = self.client.get(self.homepage_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mapping/homepage.html')
        self.assertContains(response, "Welcome to Route Mapper!") # Check for some key text

    def test_homepage_loads_successfully_authenticated(self):
        """Homepage loads successfully for authenticated users."""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.homepage_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mapping/homepage.html')
        self.assertContains(response, f"Logout ({self.user.username})") # Check for logged-in user info


    def test_homepage_displays_random_images(self):
        """Homepage displays the correct number of random background images."""
        # We created 10 images in setUp
        response = self.client.get(self.homepage_url)
        self.assertEqual(response.status_code, 200)

        # The homepage displays up to 9 random images.
        # Count how many image containers are present in the response HTML.
        # This requires inspecting the HTML structure output by your template.
        # Assuming image items are within divs with class 'image-item'
        image_item_count = response.content.decode('utf-8').count('<div class="image-item">')

        # Since we created 10 images, it should display up to 9.
        # The exact number might be less if the random sample logic
        # handles cases where there are fewer than 9 total images.
        # Our view uses random.sample(image_list, min(len(image_list), 9)).
        # So if total is 10, min(10, 9) is 9. If total was 5, min(5, 9) is 5.
        total_images_in_db = BackgroundImage.objects.count()
        expected_display_count = min(total_images_in_db, 9)

        self.assertEqual(image_item_count, expected_display_count)

        # We cannot reliably test *which* images are displayed due to randomness,
        # but we can test the number.

    # --- Background Image Upload Page Tests (/add-background-image/ - mapping:add_background_image) ---

    def test_add_image_page_requires_login(self):
        """Accessing add image page as anonymous user redirects to login."""
        response = self.client.get(self.add_image_url)
        self.assertEqual(response.status_code, 302) # Should redirect

        # Check the redirect URL is the login page
        # The 'next' parameter should point back to the page the user tried to access
        expected_redirect_url = f"{self.login_url}?next={self.add_image_url}"
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=200)

    def test_add_image_page_accessible_authenticated(self):
        """Add image page is accessible for authenticated users."""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.add_image_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mapping/add_background_image.html')
        self.assertContains(response, "Upload a New Background Image") # Check for key text

    # Note: You would also add tests here for POSTing the form,
    # checking validation errors, successful save, redirection, etc.
    # Example (basic):
    # def test_add_image_form_submit_authenticated_success(self):
    #      self.client.login(username='testuser', password='testpassword')
    #      # Need to create a new SimpleUploadedFile for the POST request
    #      new_dummy_image = SimpleUploadedFile(name='uploaded.png', content=b'png content', content_type='image/png')
    #      data = {'name': 'Uploaded Map', 'description': 'A map I uploaded', 'image': new_dummy_image}
    #      response = self.client.post(self.add_image_url, data, follow=True) # follow=True follows the redirect

    #      self.assertEqual(response.status_code, 200) # Should redirect to homepage (200 after redirect)
    #      self.assertRedirects(response, self.homepage_url)
    #      self.assertTrue(BackgroundImage.objects.filter(name='Uploaded Map', uploader=self.user).exists())


    # --- Route List Page Tests (/routes/ - mapping:user_routes_list) ---

    # Add tests for the user_routes_list_view here:
    # - Requires login (similar to add_image_page_requires_login)
    # - Loads successfully for authenticated user
    # - Displays only the authenticated user's routes in the list
    # - Displays the correct number of routes

    def test_user_routes_list_requires_login(self):
        """Accessing user routes list page as anonymous user redirects to login."""
        list_url = reverse('mapping:user_routes_list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 302)
        expected_redirect_url = f"{self.login_url}?next={list_url}"
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=200)


    def test_user_routes_list_accessible_authenticated(self):
        """User routes list page is accessible for authenticated users."""
        self.client.login(username='testuser', password='testpassword')
        list_url = reverse('mapping:user_routes_list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mapping/user_routes_list.html')
        self.assertContains(response, "My Routes") # Check for key text


    def test_user_routes_list_only_shows_own_routes(self):
        """Authenticated user only sees their own routes on the list page."""
        self.client.login(username='testuser', password='testpassword')
        list_url = reverse('mapping:user_routes_list')

        # Create a route for another user
        another_user = User.objects.create_user(username='anotheruser2', password='password2')
        another_users_bg = BackgroundImage.objects.create(name='Another Bg', image=SimpleUploadedFile('another.jpg', b'content'))
        another_users_route = Route.objects.create(user=another_user, background_image=another_users_bg, name='Another Users Route')

        # We created one route for self.user in setUp (self.user_route)
        # Total routes in DB should be 2
        self.assertEqual(Route.objects.count(), 2)

        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)

        # Check that only the current user's route name is present in the response content
        self.assertContains(response, self.user_route.name)
        self.assertNotContains(response, another_users_route.name)

        # Check the number of list items expected (assuming one <li> per route)
        list_item_count = response.content.decode('utf-8').count('<li>')
        self.assertEqual(list_item_count, 1) # Should only show the one route for self.user


    # --- Route Management Page Tests (/on/<slug>/ - mapping:routes_on_image) ---

    # Add tests for the routes_on_image_view here:
    # - Requires login
    # - Returns 404 if slug doesn't exist
    # - Loads successfully for authenticated user with valid slug
    # - Shows the correct background image
    # - Lists only the authenticated user's routes ON THAT SPECIFIC IMAGE
    # - Returns 404 if the background image exists but user tries to access it
    #   while not logged in (already covered by @login_required redirect)
    # - Returns 404 if the background image exists but belongs to another user
    #   and you have permissions restricting viewing other users' images (less likely based on current setup)

    def test_route_management_page_requires_login(self):
        """Accessing route management page as anonymous user redirects to login."""
        # Need a valid slug for the URL
        valid_slug = BackgroundImage.objects.first().slug
        manage_url = reverse('mapping:routes_on_image', kwargs={'image_slug': valid_slug})
        response = self.client.get(manage_url)
        self.assertEqual(response.status_code, 302)
        expected_redirect_url = f"{self.login_url}?next={manage_url}"
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=200)

    def test_route_management_page_returns_404_for_invalid_slug(self):
        """Route management page returns 404 for invalid slug."""
        self.client.login(username='testuser', password='testpassword')
        invalid_slug = 'non-existent-image-slug'
        manage_url = reverse('mapping:routes_on_image', kwargs={'image_slug': invalid_slug})
        response = self.client.get(manage_url)
        self.assertEqual(response.status_code, 404)


    def test_route_management_page_accessible_authenticated_valid_slug(self):
        """Route management page is accessible for authenticated user with valid slug."""
        self.client.login(username='testuser', password='testpassword')
        valid_slug = BackgroundImage.objects.first().slug
        manage_url = reverse('mapping:routes_on_image', kwargs={'image_slug': valid_slug})
        response = self.client.get(manage_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mapping/route_management.html')
        self.assertContains(response, f"Manage Routes on \"{BackgroundImage.objects.first().name}\"") # Check for image name

    def test_route_management_page_only_shows_own_routes_on_that_image(self):
        """Route management page lists only user's routes for that specific image."""
        self.client.login(username='testuser', password='testpassword')

        # Create routes for different users and on different images
        another_user = User.objects.create_user(username='anotheruser3', password='password3')
        bg_image_A = BackgroundImage.objects.create(name='Image A', image=SimpleUploadedFile('a.jpg', b'content'))
        bg_image_B = BackgroundImage.objects.create(name='Image B', image=SimpleUploadedFile('b.jpg', b'content'))

        # Routes for self.user
        my_route_A1 = Route.objects.create(user=self.user, background_image=bg_image_A, name='My Route A1')
        my_route_A2 = Route.objects.create(user=self.user, background_image=bg_image_A, name='My Route A2')
        my_route_B1 = Route.objects.create(user=self.user, background_image=bg_image_B, name='My Route B1')

        # Routes for another_user
        their_route_A1 = Route.objects.create(user=another_user, background_image=bg_image_A, name='Their Route A1')
        their_route_B1 = Route.objects.create(user=another_user, background_image=bg_image_B, name='Their Route B1')

        # Total routes for self.user: 3 (A1, A2, B1)
        # Total routes on Image A: 3 (my_A1, my_A2, their_A1)
        # Total routes on Image B: 2 (my_B1, their_B1)

        # Test viewing routes on Image A
        manage_url_A = reverse('mapping:routes_on_image', kwargs={'image_slug': bg_image_A.slug})
        response_A = self.client.get(manage_url_A)
        self.assertEqual(response_A.status_code, 200)

        # Should contain names of self.user's routes on Image A
        self.assertContains(response_A, my_route_A1.name)
        self.assertContains(response_A, my_route_A2.name)
        # Should NOT contain names of other routes
        self.assertNotContains(response_A, my_route_B1.name) # My route on different image
        self.assertNotContains(response_A, their_route_A1.name) # Other user's route on this image
        self.assertNotContains(response_A, their_route_B1.name) # Other user's route on different image

        # Count list items for user's routes on this image (assuming <li> per route in 'Your Routes')
        # You might need a more specific selector if there are other lists in the template
        route_list_item_count_A = response_A.content.decode('utf-8').count('id="routeList"') # Find the ul
        # Assuming each route within that ul is an <li>
        if route_list_item_count_A: # Check if the ul exists (only if user_routes_on_image is not empty)
             route_list_item_count_A = response_A.content.decode('utf-8').split('id="routeList"')[1].split('</ul>')[0].count('<li>')
             self.assertEqual(route_list_item_count_A, 2) # Should be 2 routes (my_A1, my_A2)
        else:
             # If user has no routes on this image, the list might not be rendered,
             # and the "You have no routes defined..." message would be present.
             # In this test case, the user *does* have routes, so this else should not be hit.
             pass # Add assertion for "no routes" message if testing that case

        # Test viewing routes on Image B
        manage_url_B = reverse('mapping:routes_on_image', kwargs={'image_slug': bg_image_B.slug})
        response_B = self.client.get(manage_url_B)
        self.assertEqual(response_B.status_code, 200)

        self.assertContains(response_B, my_route_B1.name)
        self.assertNotContains(response_B, my_route_A1.name)
        self.assertNotContains(response_B, their_route_A1.name)

        route_list_item_count_B = response_B.content.decode('utf-8').count('id="routeList"')
        if route_list_item_count_B:
             route_list_item_count_B = response_B.content.decode('utf-8').split('id="routeList"')[1].split('</ul>')[0].count('<li>')
             self.assertEqual(route_list_item_count_B, 1) # Should be 1 route (my_B1)


    # Add tests for DELETE route via web form if implemented (currently API only)
    # Add tests for other web pages as you create them (e.g., route detail page if separate)