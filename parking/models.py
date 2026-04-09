import uuid
from django.db import models


VEHICLE_TYPE_CHOICES = [
    ('mini', 'Mini / Hatchback'),
    ('sedan', 'Sedan'),
    ('suv', 'SUV'),
    ('jeep', 'Jeep'),
    ('muv', 'MUV / Van'),
    ('truck', 'Truck / Pickup'),
]

# Maps each type to a minimum slot size needed (0 = small, 1 = medium, 2 = large)
VEHICLE_SIZE_MAP = {
    'mini': 0,
    'sedan': 1,
    'suv': 2,
    'jeep': 2,
    'muv': 2,
    'truck': 2,
}


class ParkingSlot(models.Model):
    """Represents one parking slot in the lot."""

    SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]

    slot_number = models.CharField(max_length=10, unique=True)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='medium')
    floor = models.IntegerField(default=1)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['floor', 'slot_number']

    def __str__(self):
        return f"{self.slot_number} ({self.get_size_display()}) – {'Free' if self.is_available else 'Occupied'}"


class ParkingSession(models.Model):
    """Tracks a single parking visit from entry to exit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    vehicle_plate = models.CharField(max_length=20)
    vehicle_type = models.CharField(
        max_length=10,
        choices=VEHICLE_TYPE_CHOICES,
        default='sedan',
    )
    slot = models.ForeignKey(ParkingSlot, on_delete=models.SET_NULL, null=True, blank=True)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.driver_name} – {self.vehicle_plate} ({'Active' if self.is_active else 'Closed'})"
