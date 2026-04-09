from django.urls import path
from . import views

app_name = 'parking'

urlpatterns = [
    path('', views.home, name='home'),
    path('entry/', views.entry, name='entry'),
    path('select-slot/', views.select_slot, name='select_slot'),
    path('navigate/<uuid:session_id>/', views.navigate, name='navigate'),
    path('exit/', views.exit_scan, name='exit_scan'),
    path('qr/entry/', views.qr_entry, name='qr_entry'),
    path('qr/exit/', views.qr_exit, name='qr_exit'),
    path('api/slots/', views.api_slots, name='api_slots'),
]
