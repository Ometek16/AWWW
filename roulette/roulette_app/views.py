import random
import time
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, StreamingHttpResponse # Added StreamingHttpResponse
from django.views.decorators.http import require_POST
from .models import RollResult
import json
import traceback
import datetime
from django.utils.timezone import now
from .forms import CustomUserCreationForm

def index(request):
    return render(request, 'roulette_app/index.html')

@require_POST # Ensure this view only accepts POST requests
@login_required # Ensure only logged-in users can spin
def spin_wheel(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You must be logged in to spin the wheel.")

    # Generate a random number between 1 and 5
    rolled_number = random.randint(1, 5)

    # Save the roll result to the database
    roll_result = RollResult.objects.create(
        user=request.user,
        number=rolled_number
    )

    return JsonResponse({
        'success': True,
        'rolled_number': rolled_number,
        'message': f"You rolled a {rolled_number}!"
    })
    
def sse_events(request):
    def event_stream():
        last_check_time = now()

        while True:
            new_rolls = RollResult.objects.filter(timestamp__gt=last_check_time).order_by('timestamp')

            for roll in new_rolls:
                data = {
                    'user_id': roll.user.id,
                    'username': roll.user.username,
                    'rolled_number': roll.number,
                    'timestamp': roll.timestamp.isoformat(),
                }
                yield f"event: roll_result\ndata: {json.dumps(data)}\n\n"
                last_check_time = roll.timestamp

            yield 'event: heartbeat\ndata: {}\n\n'
            time.sleep(1)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

def get_recent_ones(request):
    recent_ones = RollResult.objects.filter(number=1).order_by('-timestamp')[:10]

    data = [
        {
            'username': roll.user.username,
            'timestamp': roll.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        for roll in recent_ones
    ]
    return JsonResponse({'recent_ones': data})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # After successful registration, redirect to login page
            return redirect('login') # 'login' is the name of Django's built-in login URL
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})