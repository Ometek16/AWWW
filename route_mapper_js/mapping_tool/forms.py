# mapping_tool/forms.py
from django import forms
from .models import Map

class MapForm(forms.ModelForm):
    class Meta:
        model = Map
        fields = ['title', 'image'] # Wykluczamy uploader i slug
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }