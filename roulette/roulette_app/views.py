import random
import json # Nadal potrzebne dla JSONResponse i channel_layer.group_send
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# Usunięto 'StreamingHttpResponse' - nie jest już potrzebne dla SSE.
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from .models import RollResult
# Usunięto 'time', 'traceback', 'datetime', 'asyncio', 'django.utils.timezone.now'
from .forms import CustomUserCreationForm

# Importy dla Django Channels - WAŻNE!
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def index(request):
    return render(request, 'roulette_app/index.html')

@require_POST
@login_required
def spin_wheel(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You must be logged in to spin the wheel.")

    rolled_number = random.randint(1, 5)

    roll_result = RollResult.objects.create(
        user=request.user,
        number=rolled_number
    )

    # Wysyłanie wiadomości o spinie do Channel Layer (Dla WebSocketa)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'roulette_group', # Nazwa grupy z Consumer'a (consumers.py)
        {
            'type': 'roulette_message', # Nazwa metody w Consumer'ze (async def roulette_message(self, event):)
            'message': { # Dane, które zostaną przesłane do klienta przez WebSocket
                'id': roll_result.id,
                'user_id': request.user.id,
                'username': request.user.username,
                'rolled_number': rolled_number,
                'timestamp': roll_result.timestamp.isoformat(),
            }
        }
    )

    return JsonResponse({
        'success': True,
        'rolled_number': rolled_number,
        'username': request.user.username,
        'message': f"You rolled a {rolled_number}!"
    })

# --- WAŻNE: W TYM MIEJSCU NIE POWINNO BYĆ ABSOLUTNIE ŻADNEGO KODU FUNKCJI `sse_events` ---
# UPEWNIJ SIĘ, ŻE TO JEST PUSTE PO FUNKCJI `spin_wheel` do `get_recent_ones`.

def get_recent_ones(request):
    # To jest zwykły synchroniczny widok HTTP, więc operacje bazodanowe są tutaj OK.
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
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})