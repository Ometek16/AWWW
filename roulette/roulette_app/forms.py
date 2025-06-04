from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

# This form will be used for user self-registration
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields # Uses default fields: username, password, password_confirmation
        # If you wanted to add email:
        # fields = ('username', 'email') + UserCreationForm.Meta.fields[2:]

    # You can add custom validation or fields here if needed
    # For now, UserCreationForm is sufficient for basic username/password registration.