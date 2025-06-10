# mapping_tool/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Map, Board, Waystone, WAYSTONE_COLORS, UserPathSegment
from collections import Counter # Do zliczania kolorów

User = get_user_model()

class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class MapSerializer(serializers.ModelSerializer):
    uploader = UserNestedSerializer(read_only=True) # Zakładam, że UserNestedSerializer jest zdefiniowany

    class Meta:
        model = Map
        # UPEWNIJ SIĘ, ŻE 'image' JEST NA LIŚCIE PÓL
        fields = ['id', 'title', 'image', 'slug', 'uploader', 'uploaded_at']
        read_only_fields = ['slug', 'uploader', 'uploaded_at']

    # Ta metoda jest kluczowa dla uzyskania pełnego URL obrazka
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request') # Pobierz request z kontekstu

        # Jeśli 'image' jest w polach i instancja ma obrazek
        if 'image' in representation and instance.image and instance.image.url:
            if request is not None:
                representation['image'] = request.build_absolute_uri(instance.image.url)
            else:
                representation['image'] = instance.image.url # Fallback, jeśli nie ma requestu w kontekście
        elif 'image' in representation: # Jeśli pole 'image' istnieje, ale nie ma pliku
            representation['image'] = None # Ustaw na null, aby było to jawne w JSON
        
        return representation

# --- Nowe serializery ---

class WaystoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waystone
        fields = ['id', 'row', 'col', 'color']
        # 'board' będzie ustawiane automatycznie przez zagnieżdżony serializer BoardSerializer


class BoardSerializer(serializers.ModelSerializer):
    # Ustawia pole creator jako ReadOnlyField i domyślnie pobiera je z request.user.
    # To się dzieje automatycznie, jeśli pole jest ForeignKey i read_only=True,
    # a w ViewSet ustawiamy creator przy tworzeniu.
    # Alternatywnie, CurrentUserDefault.
    creator = UserNestedSerializer(read_only=True) # Wyświetlamy zagnieżdżone dane użytkownika

    # Akceptuje map_reference jako ID mapy (PrimaryKeyRelatedField).
    # Domyślnie ForeignKey jest traktowane jak PrimaryKeyRelatedField, więc nie trzeba jawnie deklarować,
    # chyba że chcemy dostosować queryset lub inne opcje.
    # map_reference = serializers.PrimaryKeyRelatedField(queryset=Map.objects.all()) # To jest domyślne zachowanie

    # Zawiera zagnieżdżony WaystoneSerializer dla pola waystones.
    # Aby móc tworzyć/aktualizować waystones razem z Board, potrzebujemy nadpisać metody create/update.
    # `read_only=True` sprawiłoby, że nie moglibyśmy wysyłać waystones do zapisu.
    # Usuwamy `read_only=True` i dodajemy `write_only=True` dla danych wejściowych,
    # oraz osobne pole dla danych wyjściowych, lub obsługujemy to w create/update.
    
    # Dla odczytu (GET)
    waystones = WaystoneSerializer(many=True, read_only=True)
    # Dla zapisu (POST/PUT) - to pole nie jest bezpośrednio mapowane na model,
    # ale używane w logice create/update. Nazwijmy je inaczej, aby uniknąć konfliktu.
    waystones_input = WaystoneSerializer(many=True, write_only=True, required=False)

    map_details = MapSerializer(source='map_reference', read_only=True) # Do wyświetlania szczegółów mapy


    class Meta:
        model = Board
        fields = [
            'id', 'name', 'creator', 'map_reference', 'map_details', 'grid_rows', 'grid_cols',
            'created_at', 'updated_at', 'waystones', 'waystones_input'
        ]
        read_only_fields = ('created_at', 'updated_at', 'creator') # creator jest ustawiany w perform_create ViewSetu

    def validate_waystones_input(self, waystones_data):
        """
        Walidacja dla pola waystones_input:
        Sprawdza, czy dla każdego z 10 kolorów jest 0 lub 2 Kamienie Drogi.
        """
        if not waystones_data: # Jeśli pusta lista, jest OK
            return waystones_data

        color_counts = Counter()
        for ws_data in waystones_data:
            # Sprawdzenie czy waystone ma poprawne pola (row, col, color) - DRF zrobi to dla WaystoneSerializer
            # Sprawdzenie czy kolor jest poprawny - DRF zrobi to (choices w modelu)
            color_counts[ws_data['color']] += 1

        all_possible_colors = [color_choice[0] for color_choice in WAYSTONE_COLORS]

        for color_code in all_possible_colors:
            count = color_counts.get(color_code, 0)
            if count != 0 and count != 2:
                raise serializers.ValidationError(
                    f"Nieprawidłowa konfiguracja planszy: Kolor '{color_code}' "
                    f"ma {count} kamieni. Każdy kolor musi mieć dokładnie 0 lub 2 kamienie."
                )
        return waystones_data

    # Nadpisanie create i update, aby obsłużyć zagnieżdżone tworzenie/aktualizację Waystones
    def create(self, validated_data):
        waystones_data = validated_data.pop('waystones_input', [])
        # creator jest ustawiany w perform_create ViewSetu, więc nie ma go w validated_data na tym etapie
        # jeśli by nie był, to: validated_data['creator'] = self.context['request'].user
        board = Board.objects.create(**validated_data)
        for waystone_data in waystones_data:
            Waystone.objects.create(board=board, **waystone_data)
        return board

    def update(self, instance, validated_data):
        waystones_data = validated_data.pop('waystones_input', None) # None aby odróżnić od pustej listy

        # Aktualizuj pola Board
        instance.name = validated_data.get('name', instance.name)
        instance.map_reference = validated_data.get('map_reference', instance.map_reference)
        instance.grid_rows = validated_data.get('grid_rows', instance.grid_rows)
        instance.grid_cols = validated_data.get('grid_cols', instance.grid_cols)
        instance.save()

        # Aktualizuj Waystones (jeśli zostały dostarczone)
        if waystones_data is not None: # Jeśli przekazano waystones_input (nawet jako pustą listę)
            instance.waystones.all().delete() # Usuń stare waystones
            for waystone_data in waystones_data:
                Waystone.objects.create(board=instance, **waystone_data)
        
        return instance
    
class UserPathSegmentSerializer(serializers.ModelSerializer):
    # user pole nie jest potrzebne przy tworzeniu (ustawiane z request.user),
    # ani przy odczycie (filtrujemy po użytkowniku)
    # Jeśli chcesz je zwracać, dodaj: user = UserNestedSerializer(read_only=True)
    
    class Meta:
        model = UserPathSegment
        fields = ['id', 'board', 'start_row', 'start_col', 'end_row', 'end_col', 'created_at']
        # 'board' i 'user' będą ustawiane w logice zapisu, nie wysyłane wprost przez klienta
        # w tym kontekście, lub board będzie częścią URL.
        read_only_fields = ('id', 'created_at', 'user', 'board') # board może być z URL

    def validate(self, data):
        # Można dodać walidację, np. czy współrzędne są w granicach siatki planszy
        # (choć to powinno być zapewnione przez UI)
        # board = self.context['board'] # Jeśli przekazujemy board w kontekście
        # if data['start_row'] >= board.grid_rows or ... :
        #     raise serializers.ValidationError("Współrzędne poza planszą.")
        return data