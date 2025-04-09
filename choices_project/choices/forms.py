from django import forms
from .models import UserImage

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = UserImage
        fields = ['image', 'caption']