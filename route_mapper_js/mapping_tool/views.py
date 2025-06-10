# mapping_tool/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm # Już jest
from django.contrib import messages # Już jest
from django.contrib.auth.decorators import login_required # Nowy import
from .forms import MapForm # Nowy import
from django.contrib.auth.decorators import login_required
from .models import Map, WAYSTONE_COLORS, Board 
from .serializers import BoardSerializer
import json


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Konto dla {username} zostało utworzone! Możesz się teraz zalogować.')
            return redirect('login') # Przekieruj do strony logowania po pomyślnej rejestracji
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def add_map_view(request):
    if request.method == 'POST':
        form = MapForm(request.POST, request.FILES)
        if form.is_valid():
            map_instance = form.save(commit=False)
            map_instance.uploader = request.user # Przypisanie zalogowanego użytkownika
            map_instance.save() # To wywoła metodę save() modelu, która generuje slug
            messages.success(request, f'Mapa "{map_instance.title}" została pomyślnie dodana!')
            return redirect('home') # Przekierowanie na stronę główną (lub listę map)
    else:
        form = MapForm()
    return render(request, 'mapping_tool/add_map.html', {'form': form})



def home_view(request):
    maps = Map.objects.all().order_by('-uploaded_at')[:6] # Pokaż kilka ostatnich map
    user_boards = Board.objects.filter(creator=request.user).order_by('-updated_at') if request.user.is_authenticated else []
    context = {
        'maps': maps,
        'user_boards': user_boards, # Dodajemy dla przyszłego listowania plansz użytkownika
    }
    return render(request, 'mapping_tool/home.html', context)


@login_required
def create_board_view(request):
    maps = Map.objects.all().order_by('title')
    initial_map_id = request.GET.get('map_id', None)

    # Oryginalna lista tupli Pythona dla pętli Django w szablonie
    python_waystone_colors_list = WAYSTONE_COLORS 

    # String JSON dla JavaScript
    waystone_colors_json_string = "[]" # Domyślna wartość
    if WAYSTONE_COLORS:
        try:
            waystone_colors_json_string = json.dumps(WAYSTONE_COLORS)
        except TypeError:
            # Obsługa błędu, jeśli WAYSTONE_COLORS nie jest serializowalne
            pass 
    
    # DEBUG:
    print(f"DEBUG (views.py): python_waystone_colors_list = {python_waystone_colors_list}")
    print(f"DEBUG (views.py): waystone_colors_json_string = {waystone_colors_json_string}")

    context = {
        'maps': maps,
        'waystone_colors_list_for_django_loop': python_waystone_colors_list, # Dla pętli Django
        'waystone_colors_for_js': waystone_colors_json_string,          # Dla JavaScriptu
        'initial_map_id': initial_map_id,
    }
    return render(request, 'mapping_tool/create_board.html', context)

@login_required # Na razie tylko zalogowani mogą "grać"
def play_board_view(request, board_id):
    # Pobierz planszę lub zwróć 404. Można dodać sprawdzanie, czy użytkownik jest twórcą,
    # jeśli "granie" ma być ograniczone tylko do twórcy lub ma jakieś specjalne uprawnienia.
    # Na razie zakładamy, że jeśli zna ID i jest zalogowany, może zobaczyć.
    board = get_object_or_404(Board, id=board_id)
    # board = get_object_or_404(Board, id=board_id, creator=request.user) # Jeśli tylko właściciel

    # Serializuj dane planszy, aby łatwo przekazać je do JS (w tym waystones)
    board_serializer = BoardSerializer(board, context={'request': request}) # Dodajemy context dla pełnych URLi obrazków
    board_data_json = json.dumps(board_serializer.data) # Konwertujemy do stringa JSON

    # WAYSTONE_COLORS mogą być potrzebne w JS do np. legendy, jeśli będziemy ją robić
    waystone_colors_list_for_django_loop = WAYSTONE_COLORS
    waystone_colors_json_string = json.dumps(WAYSTONE_COLORS)


    context = {
        'board': board,
        'board_data_for_js': board_data_json, # Serializowane dane planszy jako string JSON
        'waystone_colors_list_for_django_loop': waystone_colors_list_for_django_loop, # Dla legendy w Django, jeśli potrzebne
        'waystone_colors_for_js': waystone_colors_json_string, # Dla logiki JS
    }
    return render(request, 'mapping_tool/play_board.html', context)