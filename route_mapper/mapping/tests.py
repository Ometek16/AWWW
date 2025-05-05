from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError # For testing database constraints
from django.utils.text import slugify # Helper for slug generation verification

from .models import BackgroundImage, Route, RoutePoint

# Get the User model
User = get_user_model()

class ModelTests(TestCase):
    """
    Unit tests for the Django models in the mapping app.
    """

    def setUp(self):
        """
        Set up test data before each test method.
        """
        # Create a test user (needed for Route and BackgroundImage uploader)
        self.user = User.objects.create_user(username='testuser', password='password123')

        # Create a test BackgroundImage (needed for Route)
        # We'll create more specific images for BackgroundImage tests below
        # but this one is useful for creating Routes.
        self.bg_image_base = BackgroundImage.objects.create(
            name='Test Background',
            # ImageField requires a file-like object or path.
            # For basic tests, you can use a dummy file or mock it.
            # Using SimpleUploadedFile is a common way to simulate uploads.
            # Requires Pillow for image processing: pip install Pillow
            image='path/to/dummy/image.jpg', # Using a placeholder, test runner might need actual file or mock
            description='A generic test background image.',
            uploader=self.user
        )
        # Note: For robust ImageField testing without actual files, consider mocking
        # or using django-imagekit's test utilities if you were using it.
        # For basic model saving/slug logic, a simple path placeholder is often sufficient
        # provided you don't try to open/process the image file itself in the test.
        # Let's use a simple file create approach here.

        # Ensure a dummy image file exists for tests that require it
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.conf import settings
        import os
        # Create media directory if it doesn't exist (for test runner)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        # Create a dummy JPEG file
        self.dummy_image_file = SimpleUploadedFile(
            name='dummy_image.jpg',
            content=b'dummy_image_content', # Replace with actual valid image content if needed
            content_type='image/jpeg'
        )
        # Create another dummy image for testing slug uniqueness with different files
        self.dummy_image_file_2 = SimpleUploadedFile(
             name='dummy_image_2.jpg',
             content=b'dummy_image_content_2',
             content_type='image/jpeg'
        )


    # --- BackgroundImage Tests ---

    def test_background_image_creation(self):
        """Test creating a BackgroundImage instance."""
        image = BackgroundImage.objects.create(
            name='Another Image',
            image=self.dummy_image_file,
            uploader=self.user
        )
        self.assertIsNotNone(image.pk) # Check if object was saved and got a primary key
        self.assertEqual(image.name, 'Another Image')
        self.assertEqual(image.uploader, self.user)
        self.assertIsNotNone(image.uploaded_at)
        # Check if the slug was generated automatically
        self.assertIsNotNone(image.slug)
        self.assertEqual(image.slug, slugify('Another Image')) # Check initial slug value


    def test_background_image_auto_slug_generation(self):
        """Test automatic slug generation on save."""
        image_name = 'My Unique Image Name'
        image = BackgroundImage.objects.create(
            name=image_name,
            image=self.dummy_image_file,
            uploader=self.user
        )
        expected_slug = slugify(image_name)
        self.assertEqual(image.slug, expected_slug)

    def test_background_image_auto_slug_uniqueness(self):
        """Test automatic slug generation handles duplicates."""
        image_name = 'Duplicate Name'
        image1 = BackgroundImage.objects.create(
            name=image_name,
            image=self.dummy_image_file,
            uploader=self.user
        )
        expected_slug1 = slugify(image_name)
        self.assertEqual(image1.slug, expected_slug1)

        # Create another image with the exact same name
        image2 = BackgroundImage.objects.create(
            name=image_name,
             image=self.dummy_image_file_2, # Use a different dummy file
            uploader=self.user
        )
        expected_slug2 = f"{slugify(image_name)}-1"
        self.assertEqual(image2.slug, expected_slug2)
        self.assertNotEqual(image1.slug, image2.slug)

        # Create a third image with the same name
        image3 = BackgroundImage.objects.create(
             name=image_name,
             image=self.dummy_image_file, # Can reuse dummy file if needed
             uploader=self.user
         )
        expected_slug3 = f"{slugify(image_name)}-2"
        self.assertEqual(image3.slug, expected_slug3)
        self.assertNotEqual(image1.slug, image3.slug)
        self.assertNotEqual(image2.slug, image3.slug)


    def test_background_image_unique_slug_constraint(self):
        """Test database enforces unique slug."""
        slug_value = 'manual-unique-slug'
        BackgroundImage.objects.create(
            name='First Image',
            slug=slug_value, # Manually set the slug
            image=self.dummy_image_file,
            uploader=self.user
        )

        # Attempt to create another image with the exact same manual slug
        with self.assertRaises(IntegrityError):
            BackgroundImage.objects.create(
                name='Second Image',
                slug=slug_value, # Attempt to use the same slug
                image=self.dummy_image_file_2,
                uploader=self.user
            )

    # Note: Testing unique=True on a field is often done by attempting to save
    # two objects with the same value and expecting an IntegrityError.
    # The initial prompt mentioned BackgroundImage.title (or name), but our model
    # has unique=True on the slug, not the name. This test covers the unique slug.


    # --- RoutePoint Tests ---

    def test_route_point_creation(self):
        """Test creating a RoutePoint instance."""
        route = Route.objects.create(
            user=self.user,
            background_image=self.bg_image_base,
            name='Test Route'
        )
        point = RoutePoint.objects.create(
            route=route,
            x=0.1,
            y=0.2,
            order=0
        )
        self.assertIsNotNone(point.pk)
        self.assertEqual(point.route, route)
        self.assertEqual(point.x, 0.1)
        self.assertEqual(point.y, 0.2)
        self.assertEqual(point.order, 0)
        self.assertIsNotNone(point.created_at)

    def test_route_point_unique_order_constraint(self):
        """Test database enforces unique order per route."""
        route = Route.objects.create(
            user=self.user,
            background_image=self.bg_image_base,
            name='Test Route for Points'
        )
        RoutePoint.objects.create(
            route=route,
            x=0.1, y=0.1, order=0
        )

        # Attempt to create another point with the same order on the same route
        with self.assertRaises(IntegrityError):
            RoutePoint.objects.create(
                route=route,
                x=0.2, y=0.2, order=0 # Same route, same order
            )

    def test_route_point_same_order_different_routes_allowed(self):
        """Test same order is allowed on different routes."""
        route1 = Route.objects.create(
            user=self.user,
            background_image=self.bg_image_base,
            name='Route 1'
        )
        route2 = Route.objects.create(
            user=self.user,
            background_image=self.bg_image_base,
            name='Route 2'
        )

        point1 = RoutePoint.objects.create(
            route=route1,
            x=0.1, y=0.1, order=0
        )
        point2 = RoutePoint.objects.create(
            route=route2,
            x=0.2, y=0.2, order=0 # Same order as point1, but on different route
        )
        # If no IntegrityError is raised, the test passes

        self.assertEqual(point1.order, point2.order)
        self.assertNotEqual(point1.route, point2.route)

    def test_route_point_ordering_meta(self):
        """Test points are ordered by 'order' by default."""
        route = Route.objects.create(
            user=self.user,
            background_image=self.bg_image_base,
            name='Route with Points'
        )
        # Create points out of sequence
        point2 = RoutePoint.objects.create(route=route, x=0.3, y=0.3, order=2)
        point0 = RoutePoint.objects.create(route=route, x=0.1, y=0.1, order=0)
        point1 = RoutePoint.objects.create(route=route, x=0.2, y=0.2, order=1)

        # Fetch points for the route - they should come back in order due to Meta class
        fetched_points = route.points.all()

        self.assertEqual(len(fetched_points), 3)
        self.assertEqual(fetched_points[0].order, 0)
        self.assertEqual(fetched_points[1].order, 1)
        self.assertEqual(fetched_points[2].order, 2)
        self.assertEqual(fetched_points[0], point0)
        self.assertEqual(fetched_points[1], point1)
        self.assertEqual(fetched_points[2], point2)


    # --- Basic Relationship Tests ---

    def test_user_routes_relationship(self):
        """Test user.routes related_name."""
        route1 = Route.objects.create(user=self.user, background_image=self.bg_image_base, name='Route A')
        route2 = Route.objects.create(user=self.user, background_image=self.bg_image_base, name='Route B')

        user_routes = self.user.routes.all()
        self.assertIn(route1, user_routes)
        self.assertIn(route2, user_routes)
        self.assertEqual(user_routes.count(), 2)

    def test_route_points_relationship(self):
        """Test route.points related_name."""
        route = Route.objects.create(user=self.user, background_image=self.bg_image_base, name='Route XYZ')
        point1 = RoutePoint.objects.create(route=route, x=0.1, y=0.1, order=0)
        point2 = RoutePoint.objects.create(route=route, x=0.2, y=0.2, order=1)

        route_points = route.points.all() # This will be ordered by 'order' due to Meta
        self.assertEqual(route_points.count(), 2)
        self.assertEqual(route_points[0], point1)
        self.assertEqual(route_points[1], point2)

    def test_background_image_routes_relationship(self):
        """Test background_image.routes related_name."""
        user2 = User.objects.create_user(username='testuser2', password='password123')
        route1 = Route.objects.create(user=self.user, background_image=self.bg_image_base, name='Route A')
        route2 = Route.objects.create(user=user2, background_image=self.bg_image_base, name='Route B')

        image_routes = self.bg_image_base.routes.all()
        self.assertIn(route1, image_routes)
        self.assertIn(route2, image_routes)
        self.assertEqual(image_routes.count(), 2) # Counts routes from different users on this image

    def test_background_image_uploader_relationship(self):
        """Test background_image.uploader relationship."""
        self.assertEqual(self.bg_image_base.uploader, self.user)

        # Test without uploader (null=True, blank=True)
        image_no_uploader = BackgroundImage.objects.create(
             name='Image No Uploader',
             image=self.dummy_image_file,
             uploader=None # Or just omit uploader
        )
        self.assertIsNone(image_no_uploader.uploader)


# Note: For full test coverage, you'd also test:
# - Model field verbose_name, help_text (less critical)
# - __str__ methods
# - Validation logic (if implemented in model.clean)
# - Cascade/Protect behavior on deletion (e.g., deleting user, deleting image, deleting route)
# - Edge cases for slug generation (empty name, very long name, special characters)
# - FloatField precision / range validation (if added to model.clean)