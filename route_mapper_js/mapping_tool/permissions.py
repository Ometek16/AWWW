# mapping_tool/permissions.py
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Niestandardowe uprawnienie, aby zezwolić właścicielom obiektu na jego edycję.
    Zakłada, że model instancji ma atrybut 'creator' lub 'uploader'.
    """
    def has_object_permission(self, request, view, obj):
        # Uprawnienia do odczytu są dozwolone dla każdego żądania,
        # więc zawsze zezwalamy na żądania GET, HEAD lub OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Uprawnienia do zapisu są dozwolone tylko właścicielowi.
        # Sprawdzamy, czy obiekt ma pole 'creator' (dla Board)
        if hasattr(obj, 'creator'):
            return obj.creator == request.user
        # Można dodać obsługę 'uploader' dla Map, jeśli to uprawnienie będzie używane też tam
        # if hasattr(obj, 'uploader'):
        # return obj.uploader == request.user
        return False