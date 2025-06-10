# mapping_tool/urls.py
from django.urls import path
from . import views

app_name = 'mapping_tool'

urlpatterns = [
    path('maps/add/', views.add_map_view, name='add_map'),
    path('boards/create/', views.create_board_view, name='create_board'),
    path('boards/<int:board_id>/play/', views.play_board_view, name='play_board'),
]