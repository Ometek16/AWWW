from django.db import models
from django.conf import settings # Recommended way to get the user model
from django.utils.text import slugify
import uuid # To help ensure unique slugs if needed, though simple counter is often enough

# Get the currently active User model
# This is preferred over importing django.contrib.auth.models.User directly
User = settings.AUTH_USER_MODEL

class BackgroundImage(models.Model):
    """
    Represents a background image (map, floor plan, etc.) that routes can be drawn on.
    Includes user upload and automatic slug generation.
    """
    name = models.CharField(
        max_length=255,
        help_text="A descriptive name for the background image."
        # As per decision, name is not necessarily unique globally, slug will be.
    )
    slug = models.SlugField(
        max_length=255,
        unique=True, # Ensure slugs are unique
        blank=True, # Allow blank on creation, it will be auto-generated
        help_text="URL-friendly identifier (auto-generated from name)."
    )
    image = models.ImageField(
        upload_to='background_images/', # Files will be stored in MEDIA_ROOT/background_images/
        help_text="The image file (e.g., JPG, PNG)."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of the image."
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, # Automatically set the field to now when the object is first created.
        help_text="Timestamp when the image was uploaded."
    )
    uploader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, # Don't delete the image if the uploader is deleted
        null=True,
        blank=True,
        related_name='uploaded_images', # Access images uploaded by a user via user.uploaded_images.all()
        help_text="The user who uploaded this image (optional)."
    )

    class Meta:
        verbose_name = "Background Image"
        verbose_name_plural = "Background Images"
        # Consider ordering if you want a default list order, e.g. by name or upload date
        # ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Auto-generates a unique slug from the name before saving.
        """
        if not self.slug: # Generate slug only if it's not already set
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Check for uniqueness
            while BackgroundImage.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Optional: If the name changes after the slug is set, you might want to regenerate
        # or update the slug. This adds complexity (e.g., breaking old URLs).
        # For now, let's assume the slug is generated only on initial creation.
        # If you need slug updates based on name changes, the logic would be more complex
        # and involve checking if self.pk is not None and comparing original name vs current name.

        super().save(*args, **kwargs)


class Route(models.Model):
    """
    Represents a sequence of points (RoutePoints) associated with a background image.
    Owned by a user.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # Delete routes if the user is deleted
        related_name='routes', # Access routes for a user via user.routes.all()
        help_text="The user who created this route."
    )
    background_image = models.ForeignKey(
        BackgroundImage,
        on_delete=models.PROTECT, # Prevent deleting an image if a route uses it
        related_name='routes', # Access routes using this image via image.routes.all()
        help_text="The background image for this route."
    )
    name = models.CharField(
        max_length=255,
        help_text="A name for this route."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of the route."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the route was created."
    )
    # Optional: Add last_modified field auto_now=True

    class Meta:
        verbose_name = "Route"
        verbose_name_plural = "Routes"
        # Optional: Add unique_together = ('user', 'name') if route names must be unique per user
        # ordering = ['-created_at'] # Default order by creation date

    def __str__(self):
        return f"{self.name} (by {self.user.username})"


class RoutePoint(models.Model):
    """
    Represents a single coordinate point within a route, maintaining order.
    Coordinates are stored as floats (0.0 to 1.0) relative to image dimensions.
    """
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE, # Delete points if the route is deleted
        related_name='points', # Access points for a route via route.points.all()
        help_text="The route this point belongs to."
    )
    x = models.FloatField(
        help_text="X coordinate as a fraction (0.0 to 1.0) of the image width."
    )
    y = models.FloatField(
        help_text="Y coordinate as a fraction (0.0 to 1.0) of the image height."
    )
    order = models.PositiveIntegerField(
        help_text="The sequential order of this point within the route (starts from 0 or 1)."
        # Note: The order needs to be managed manually (or via a library)
        # during creation, deletion, and reordering in views/serializers.
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the point was created."
    )

    class Meta:
        verbose_name = "Route Point"
        verbose_name_plural = "Route Points"
        # Ensure points are always retrieved in their defined order
        ordering = ['order']
        # Prevent duplicate order numbers within the same route
        unique_together = ('route', 'order')


    def __str__(self):
        return f"Point {self.order} on Route '{self.route.name}' ({self.x:.2f}, {self.y:.2f})"