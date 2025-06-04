from django.db import models
from django.contrib.auth.models import User # Django's built-in User model

class RollResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roll_results')
    number = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], # Choices for numbers 1 to 5
        help_text="The number rolled (1-5)"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp'] # Order by most recent first

    def __str__(self):
        return f"{self.user.username} rolled {self.number} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"