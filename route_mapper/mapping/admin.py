from django.contrib import admin
from .models import BackgroundImage, Route, RoutePoint

# Optional: Customize how BackgroundImage is displayed in the admin
class BackgroundImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'uploader', 'uploaded_at')
    # Make the slug field read-only as it's auto-generated
    readonly_fields = ('slug', 'uploaded_at')
    # Add search capability by name or slug
    search_fields = ('name', 'slug')
    # Add filter by uploader
    list_filter = ('uploader', 'uploaded_at')

    # Optionally, pre-populate slug from name on add/change form
    # prepopulated_fields = {'slug': ('name',)} # Note: This might conflict slightly with custom save() slug logic
    # The custom save() method is more robust for ensuring uniqueness,
    # so relying on readonly_fields and the save() method is better.

# Optional: Customize how Route is displayed in the admin
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'background_image', 'created_at')
    # Add filter by user and background image
    list_filter = ('user', 'background_image', 'created_at')
    # Add search capability by name or description
    search_fields = ('name', 'description')
    # Make user and created_at read-only (assuming they are set automatically)
    readonly_fields = ('user', 'created_at') # User will likely be set by the view/serializer, not admin form

    # You could potentially add RoutePoint as an inline here
    # class RoutePointInline(admin.TabularInline):
    #     model = RoutePoint
    #     extra = 1 # Number of empty forms to display
    #     fields = ('x', 'y', 'order') # Customize fields shown
    #     readonly_fields = ('created_at',)
    #     # order is automatically managed in the model Meta, but in the admin
    #     # inline, you might need to manually order them or use a third-party lib
    #     # if you want drag-and-drop reordering in the admin.
    #     # For basic entry, the default order field is fine.
    # inlines = [RoutePointInline] # Add this line to RouteAdmin


# Optional: Customize how RoutePoint is displayed in the admin
class RoutePointAdmin(admin.ModelAdmin):
    list_display = ('route', 'order', 'x', 'y', 'created_at')
    list_filter = ('route', 'created_at')
    search_fields = ('route__name',) # Search points by the route's name
    # Make created_at read-only
    readonly_fields = ('created_at',)

# Register your models here with their optional custom Admin classes
admin.site.register(BackgroundImage, BackgroundImageAdmin)
admin.site.register(Route, RouteAdmin)
admin.site.register(RoutePoint, RoutePointAdmin)