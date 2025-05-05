from django import forms
from .models import BackgroundImage

class BackgroundImageForm(forms.ModelForm):
    """
    Form for users to upload a new BackgroundImage.
    """
    class Meta:
        model = BackgroundImage
        # Fields the user should fill out
        fields = ['name', 'image', 'description']
        # The slug, uploaded_at, and uploader fields are set automatically
        # or in the view, so they are excluded from the form.
        # exclude = ['slug', 'uploaded_at', 'uploader'] # Alternative way

    # Optional: Add custom validation if needed, e.g., file type or size limits
    # def clean_image(self):
    #     image = self.cleaned_data.get('image')
    #     if image:
    #         # Basic example: Check file extension (requires more robust handling for production)
    #         allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    #         if not any(image.name.lower().endswith(ext) for ext in allowed_extensions):
    #             raise forms.ValidationError("Only JPG, PNG, and GIF images are allowed.")
    #         # Example: Limit file size (e.g., 5MB)
    #         # if image.size > 5 * 1024 * 1024: # 5MB
    #         #    raise forms.ValidationError("Image file size cannot exceed 5MB.")
    #     return image