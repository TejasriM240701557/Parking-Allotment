from django.contrib import admin
from .models import ParkingSlot, ParkingSession


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_number', 'size', 'floor', 'is_available')
    list_filter = ('size', 'floor', 'is_available')
    search_fields = ('slot_number',)


@admin.register(ParkingSession)
class ParkingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver_name', 'vehicle_plate', 'slot', 'entry_time', 'is_active')
    list_filter = ('is_active', 'vehicle_type')
    search_fields = ('driver_name', 'vehicle_plate')
