from django.urls import path
from . import views

app_name = 'roulette_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('spin/', views.spin_wheel, name='spin_wheel'),
    path('sse/events/', views.sse_events, name='sse_events'),
    path('api/recent-ones/', views.get_recent_ones, name='get_recent_ones'),
    path('register/', views.register, name='register'), # NEW: Registration URL
]