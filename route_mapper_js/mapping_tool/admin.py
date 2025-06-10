# mapping_tool/admin.py
from django.contrib import admin
from .models import Map, Board, Waystone # Dodajemy Board i Waystone

@admin.register(Map)
class MapAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploader', 'uploaded_at')
    search_fields = ('title', 'uploader__username')

    

# Inline admin dla Waystones wewnątrz BoardAdmin
class WaystoneInline(admin.TabularInline):
    model = Waystone
    extra = 1 # Ile pustych formularzy Waystone pokazać
    # Można dodać readonly_fields jeśli jakieś pola Waystone nie powinny być edytowane z tego poziomu
    # fields = ('row', 'col', 'color') # jawne określenie kolejności pól

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'map_reference', 'grid_rows', 'grid_cols', 'created_at', 'updated_at')
    search_fields = ('name', 'creator__username', 'map_reference__title')
    list_filter = ('map_reference', 'creator', 'created_at') # Dodatkowe filtry
    inlines = [WaystoneInline] # Dodajemy Waystones jako inline
    readonly_fields = ('created_at', 'updated_at')

# Opcjonalnie, jeśli chcemy mieć też osobny panel dla Waystone (choć zarządzanie przez Board jest zwykle lepsze)
# @admin.register(Waystone)
# class WaystoneAdmin(admin.ModelAdmin):
#     list_display = ('board', 'row', 'col', 'color', 'get_board_creator')
#     search_fields = ('board__name', 'board__creator__username')
#     list_filter = ('color', 'board__map_reference')

#     def get_board_creator(self, obj):
#         return obj.board.creator
#     get_board_creator.short_description = 'Board Creator'
#     get_board_creator.admin_order_field = 'board__creator'