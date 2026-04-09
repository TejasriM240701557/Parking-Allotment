from django.core.management.base import BaseCommand
from parking.models import ParkingSlot


class Command(BaseCommand):
    help = 'Seed the database with sample parking slots'

    def handle(self, *args, **options):
        if ParkingSlot.objects.exists():
            self.stdout.write(self.style.WARNING('Slots already exist – skipping seed.'))
            return

        slots = []
        # Floor 1 – Ground: A-01..A-08 (small), A-09..A-16 (medium), A-17..A-20 (large)
        for i in range(1, 9):
            slots.append(ParkingSlot(slot_number=f'A-{i:02d}', size='small', floor=1))
        for i in range(9, 17):
            slots.append(ParkingSlot(slot_number=f'A-{i:02d}', size='medium', floor=1))
        for i in range(17, 21):
            slots.append(ParkingSlot(slot_number=f'A-{i:02d}', size='large', floor=1))

        # Floor 2 – Upper: B-01..B-06 (small), B-07..B-12 (medium), B-13..B-18 (large)
        for i in range(1, 7):
            slots.append(ParkingSlot(slot_number=f'B-{i:02d}', size='small', floor=2))
        for i in range(7, 13):
            slots.append(ParkingSlot(slot_number=f'B-{i:02d}', size='medium', floor=2))
        for i in range(13, 19):
            slots.append(ParkingSlot(slot_number=f'B-{i:02d}', size='large', floor=2))

        ParkingSlot.objects.bulk_create(slots)
        self.stdout.write(self.style.SUCCESS(f'Created {len(slots)} parking slots.'))
