from rest_framework import serializers
from .models import BackgroundImage, Route, RoutePoint

class BackgroundImageSerializer(serializers.ModelSerializer):
    """
    Serializer for the BackgroundImage model (read-only for embedding).
    """
    # Use SerializerMethodField to get the full image URL
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BackgroundImage
        # Fields to include in the API representation
        fields = ['id', 'name', 'slug', 'image', 'image_url', 'description', 'uploaded_at']
        # Make image field read-only to prevent direct file uploads via this serializer (upload handled separately)
        # Or, if you need to update other fields without changing the image, you can make image read_only=True
        # However, for simplicity in this context (used for *reading* nested data), let's keep it standard.
        # The .url accessor makes it read-only anyway for the 'image' field itself.
        read_only_fields = ['slug', 'uploaded_at'] # Slug and upload time are set automatically

    def get_image_url(self, obj):
        """
        Get the absolute URL for the image.
        """
        if obj.image:
            # Use request context to build absolute URL if needed, otherwise relative .url is fine
            # request = self.context.get('request')
            # if request is not None:
            #     return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None # Or an empty string

class RoutePointSerializer(serializers.ModelSerializer):
    """
    Serializer for the RoutePoint model.
    Used for listing points within a route and potentially creating/updating individual points.
    """
    class Meta:
        model = RoutePoint
        fields = ['id', 'x', 'y', 'order', 'created_at']
        # Mark 'order' as read-only so it's not required in POST/PUT/PATCH data
        # The backend will set it in perform_create.
        read_only_fields = ['order', 'created_at'] # <-- Add 'order' here


    # Optional: Add custom validation for x, y range (0.0 to 1.0)
    def validate(self, data):
        x = data.get('x')
        y = data.get('y')
        if x is not None and not (0.0 <= x <= 1.0):
             raise serializers.ValidationError({"x": "X coordinate must be between 0.0 and 1.0"})
        if y is not None and not (0.0 <= y <= 1.0):
             raise serializers.ValidationError({"y": "Y coordinate must be between 0.0 and 1.0"})
        return data


class RouteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Route model.
    Includes nested points and relates to BackgroundImage.
    Handles read/write differently for background_image and points.
    """
    # For creating/updating a Route, accept the background_image slug or ID
    # Using SlugRelatedField is often more user-friendly than PK for clients
    # background_image = serializers.SlugRelatedField(
    #     slug_field='slug', # Use the 'slug' field for lookup
    #     queryset=BackgroundImage.objects.all(), # Allow selecting any existing image
    #     write_only=True # Only include this field when writing (create/update)
    # )

    # Alternative for create/update: Use PrimaryKeyRelatedField
    background_image_id = serializers.PrimaryKeyRelatedField(
         queryset=BackgroundImage.objects.all(), # Allow selecting any existing image
         source='background_image', # Map this field to the 'background_image' model field
         write_only=True # Only include this field when writing
    )


    # For reading/retrieving a Route, embed the BackgroundImage details
    # Using BackgroundImageSerializer as nested serializer
    background_image_details = BackgroundImageSerializer(
        source='background_image', # Use the 'background_image' model field
        read_only=True # Only include this field when reading
    )

    # For reading/retrieving a Route, embed its points
    # Use the RoutePointSerializer as nested serializer, many=True for a list of points
    # Make it read_only because points are managed via the /points/ endpoint, not directly here
    points = RoutePointSerializer(many=True, read_only=True)

    # User field is read-only, will display the username by default with ModelSerializer
    # user = serializers.ReadOnlyField(source='user.username') # Example if you want custom representation

    class Meta:
        model = Route
        # Fields included in the API representation for READ (GET) requests
        fields = ['id', 'user', 'background_image_id', 'background_image_details', 'name', 'description', 'points', 'created_at']
        # Fields included in the API representation for WRITE (POST, PUT, PATCH) requests
        # ModelSerializer automatically uses write_only fields for writing.
        # Fields not in `fields` or explicitly `write_only=True` are excluded from writing.
        # 'user' and 'created_at' are automatically read_only or handled by perform_create.
        read_only_fields = ['user', 'points', 'created_at'] # 'user' and 'created_at' are set by server, 'points' are managed separately


    # You can add custom validation for the Route itself if needed
    # def validate_name(self, value):
    #     # Example: Ensure route name is unique for this user (if unique_together constraint wasn't enough)
    #     if self.instance is None and Route.objects.filter(user=self.context['request'].user, name=value).exists():
    #          raise serializers.ValidationError("You already have a route with this name.")
    #     return value