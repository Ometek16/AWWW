from django.shortcuts import render, redirect
from .models import UserImage
from .forms import ImageUploadForm
from ui import get_random_context

# Main page with 9 random images and an upload link
def home(request):
    context = get_random_context()
    # Get 9 random images from the database
    images = UserImage.objects.all()
    random_images = images.order_by('?')[:9]  # 9 random images
    
    context['images'] = random_images
    return render(request, "home.html", context)

# Image upload page where users can submit images
def upload_image(request):
    context = get_random_context()
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Save the image to the database
            return redirect('home')  # Redirect back to the main page
    else:
        form = ImageUploadForm()

    context['form'] = form
    return render(request, "upload.html", context)