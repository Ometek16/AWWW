# mapping_tool/views_api.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response # WAŻNE

from .models import Map, Board, Waystone, UserPathSegment # WAŻNE (UserPathSegment)
from .serializers import MapSerializer, BoardSerializer, WaystoneSerializer, UserPathSegmentSerializer # WAŻNE (UserPathSegmentSerializer)
from .permissions import IsOwnerOrReadOnly

class MapViewSet(viewsets.ModelViewSet):
    # ... (bez zmian)
    queryset = Map.objects.all().order_by('-uploaded_at')
    serializer_class = MapSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'head', 'options']


class BoardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows boards to be viewed, created, edited and deleted.
    """
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly] # Wymagane zalogowanie, edycja tylko przez właściciela

    def get_queryset(self):
        """
        Ten widok powinien zwracać listę wszystkich plansz
        stworzonych przez aktualnie uwierzytelnionego użytkownika.
        """
        user = self.request.user
        if user.is_authenticated:
            return Board.objects.filter(creator=user).order_by('-updated_at')
        return Board.objects.none() # Niezalogowani nie widzą żadnych plansz na liście

    def perform_create(self, serializer):
        """
        Automatycznie ustawia 'creator' na zalogowanego użytkownika podczas tworzenia planszy.
        """
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['get', 'post'], url_path='user-paths', permission_classes=[permissions.IsAuthenticated])
    def user_paths(self, request, pk=None):
        board = self.get_object() # Pobiera planszę o ID=pk
        
        # Sprawdzenie, czy użytkownik jest twórcą planszy (jeśli to warunek modyfikacji planszy)
        # Dla ścieżek użytkownika, użytkownik powinien być po prostu zalogowany.
        # Niekoniecznie musi być twórcą planszy, aby na niej rysować dla siebie.

        if request.method == 'GET':
            # Pobierz ścieżki tylko dla tego użytkownika i tej planszy
            paths = UserPathSegment.objects.filter(board=board, user=request.user).order_by('created_at')
            serializer = UserPathSegmentSerializer(paths, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            # Odbierz listę segmentów ścieżek od klienta
            # Klient powinien wysłać listę obiektów:
            # [{start_row: r, start_col: c, end_row: r2, end_col: c2}, ...]
            
            # Usuń istniejące ścieżki tego użytkownika dla tej planszy
            UserPathSegment.objects.filter(board=board, user=request.user).delete()

            # Zapisz nowe ścieżki
            # request.data powinna być listą ścieżek
            new_paths_data = request.data 
            if not isinstance(new_paths_data, list):
                return Response({"error": "Oczekiwano listy segmentów ścieżek."}, status=status.HTTP_400_BAD_REQUEST)

            created_paths_serializers = []
            for path_data in new_paths_data:
                # Dodaj board i user do danych każdego segmentu
                path_data['board'] = board.id # Serializer oczekuje ID
                path_data['user'] = request.user.id # Serializer oczekuje ID
                
                serializer = UserPathSegmentSerializer(data=path_data, context={'board': board}) # Przekazujemy board do kontekstu dla ewentualnej walidacji
                if serializer.is_valid():
                    # Nie zapisujemy bezpośrednio przez serializer.save(), bo user i board są read_only
                    # Tworzymy obiekty ręcznie lub dostosowujemy serializer.
                    # Prostsze ręczne tworzenie w tym przypadku:
                    try:
                        UserPathSegment.objects.create(
                            board=board,
                            user=request.user,
                            start_row=path_data['start_row'],
                            start_col=path_data['start_col'],
                            end_row=path_data['end_row'],
                            end_col=path_data['end_col']
                        )
                        # Jeśli UserPathSegmentSerializer miałby być użyty do zapisu,
                        # musiałby akceptować board_id i user_id lub być inaczej skonstruowany.
                        # np. serializer.save(board=board, user=request.user)
                    except KeyError:
                         return Response({"error": "Brakujące pola w danych ścieżki (start_row, start_col, end_row, end_col)."}, status=status.HTTP_400_BAD_REQUEST)

                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Pobierz nowo utworzone ścieżki, aby je zwrócić
            final_paths = UserPathSegment.objects.filter(board=board, user=request.user).order_by('created_at')
            final_serializer = UserPathSegmentSerializer(final_paths, many=True)
            return Response(final_serializer.data, status=status.HTTP_201_CREATED)