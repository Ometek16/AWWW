# mapping_tool/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid

# Predefiniowane kolory dla Kamieni Drogi (Waystones)
# Zgodnie z założeniami z "Master Prompt" (10 kolorów)
WAYSTONE_COLORS = [
    ('red', 'Czerwony'),        # Red
    ('blue', 'Niebieski'),      # Blue
    ('green', 'Zielony'),       # Green
    ('yellow', 'Żółty'),        # Yellow
    ('purple', 'Fioletowy'),    # Purple
    ('orange', 'Pomarańczowy'), # Orange
    ('pink', 'Różowy'),         # Pink
    ('cyan', 'Cyjan'),          # Cyan
    ('brown', 'Brązowy'),       # Brown
    ('black', 'Czarny'),        # Black
]

class Map(models.Model):
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_maps'
    )
    title = models.CharField(max_length=200, unique=True)
    image = models.ImageField(upload_to='maps/')
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug_candidate = base_slug
            # Prosta obsługa unikalności slugu, można rozbudować
            num = 1
            while Map.objects.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base_slug}-{num}"
                num += 1
            self.slug = slug_candidate
        super().save(*args, **kwargs)


class Board(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_boards'
    )
    map_reference = models.ForeignKey(
        Map,
        on_delete=models.CASCADE,
        related_name='boards_on_this_map'
    )
    name = models.CharField(max_length=200)
    grid_rows = models.PositiveIntegerField()
    grid_cols = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Waystone(models.Model):
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='waystones' # Umożliwia dostęp board_instance.waystones.all()
    )
    row = models.PositiveIntegerField() # indeks od 0
    col = models.PositiveIntegerField() # indeks od 0
    color = models.CharField(
        max_length=20,
        choices=WAYSTONE_COLORS
    )

    class Meta:
        unique_together = ('board', 'row', 'col')

    def __str__(self):
        return f"Waystone ({self.row},{self.col}) on {self.board.name} - {self.get_color_display()}"
    
    
class UserPathSegment(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='user_path_segments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='drawn_path_segments')
    
    # Współrzędne komórek siatki
    start_row = models.PositiveIntegerField()
    start_col = models.PositiveIntegerField()
    end_row = models.PositiveIntegerField()
    end_col = models.PositiveIntegerField()
    
    # Możemy dodać kolor, jeśli chcemy, aby użytkownik mógł wybierać
    # color = models.CharField(max_length=20, default='rgba(0,123,255,0.9)') 
    # Na razie użyjemy domyślnego koloru zdefiniowanego w JS, więc to pole jest opcjonalne.

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Można dodać indeksy dla szybszego wyszukiwania
        indexes = [
            models.Index(fields=['board', 'user']),
        ]
        # Można rozważyć unique_together, jeśli jeden segment nie powinien być dodany wielokrotnie,
        # ale przy rysowaniu swobodnym to może być trudne do zarządzania.
        # unique_together = ('board', 'user', 'start_row', 'start_col', 'end_row', 'end_col')

    def __str__(self):
        return f"Path on '{self.board.name}' by '{self.user.username}': ({self.start_row},{self.start_col})->({self.end_row},{self.end_col})"