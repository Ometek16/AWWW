from django.db import models

class UserImage(models.Model):
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption or f"Image {self.id}"