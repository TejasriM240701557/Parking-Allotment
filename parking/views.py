import io
import math
import base64
import json

import qrcode
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.conf import settings

from .models import ParkingSlot, ParkingSession, VEHICLE_SIZE_MAP
from .forms import EntryForm, ExitForm
from datetime import timedelta

def _cleanup_stale_sessions():
    now = timezone.now()
    stale_threshold = now - timedelta(hours=24)
    stale_sessions = ParkingSession.objects.filter(is_active=True, entry_time__lte=stale_threshold)
    if not stale_sessions.exists():
        return
    rate = getattr(settings, 'PARKING_RATE_PER_HOUR', 40)
    for session in stale_sessions:
        session.exit_time = session.entry_time + timedelta(hours=24)
        session.amount = 24 * rate
        session.is_active = False
        session.save()
        if session.slot:
            session.slot.is_available = True
            session.slot.save()


def bookings(request):
    """List all user tickets (active and finished)."""
    _cleanup_stale_sessions()
    # For a real app, this would filter by request.user
    active_sessions = ParkingSession.objects.filter(is_active=True).order_by('-entry_time')
    finished_sessions = ParkingSession.objects.filter(is_active=False).order_by('-exit_time')
    return render(request, 'parking/bookings.html', {
        'active_sessions': active_sessions,
        'finished_sessions': finished_sessions,
    })


def _make_qr_data_uri(data: str) -> str:
    """Generate a QR code and return it as a base64 data URI."""
    img = qrcode.make(data, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f'data:image/png;base64,{b64}'


# ─── Landing ───────────────────────────────────────────────────────
def home(request):
    """Landing page with Entry / Exit buttons."""
    _cleanup_stale_sessions()
    active_sessions = ParkingSession.objects.filter(is_active=True).count()
    total_slots = ParkingSlot.objects.count()
    free_slots = ParkingSlot.objects.filter(is_available=True).count()
    return render(request, 'parking/home.html', {
        'active_sessions': active_sessions,
        'total_slots': total_slots,
        'free_slots': free_slots,
    })


# ─── Entry flow ────────────────────────────────────────────────────
def entry(request):
    """Step 1 – driver fills in details."""
    _cleanup_stale_sessions()
    if request.method == 'POST':
        form = EntryForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            request.session['pending_session'] = {
                'driver_name': session.driver_name,
                'phone': session.phone,
                'vehicle_plate': session.vehicle_plate,
                'vehicle_type': session.vehicle_type,
            }
            return redirect('parking:select_slot')
    else:
        form = EntryForm()
    return render(request, 'parking/entry.html', {'form': form})


def select_slot(request):
    """Step 2 – show available slots that fit the vehicle and let the driver pick one."""
    pending = request.session.get('pending_session')
    if not pending:
        return redirect('parking:entry')

    vehicle_type = pending['vehicle_type']
    # Determine required minimum slot size
    size_order = {'small': 0, 'medium': 1, 'large': 2}
    min_size_val = VEHICLE_SIZE_MAP.get(vehicle_type, 1)
    suitable_sizes = [s for s, v in size_order.items() if v >= min_size_val]

    # All slots on this page (for showing occupied ones too)
    all_slots = ParkingSlot.objects.filter(size__in=suitable_sizes)

    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        slot = get_object_or_404(ParkingSlot, pk=slot_id, is_available=True)

        session = ParkingSession.objects.create(
            driver_name=pending['driver_name'],
            phone=pending['phone'],
            vehicle_plate=pending['vehicle_plate'],
            vehicle_type=pending['vehicle_type'],
            slot=slot,
        )
        slot.is_available = False
        slot.save()

        del request.session['pending_session']
        return redirect('parking:navigate', session_id=session.id)

    # Group slots by floor
    floors = {}
    for slot in all_slots:
        floors.setdefault(slot.floor, []).append(slot)

    # Vehicle type display name
    type_display = dict(ParkingSession._meta.get_field('vehicle_type').choices).get(vehicle_type, vehicle_type)

    return render(request, 'parking/select_slot.html', {
        'floors': dict(sorted(floors.items())),
        'vehicle_type': vehicle_type,
        'type_display': type_display,
        'pending': pending,
    })


# ─── Live slot availability API ────────────────────────────────────
def api_slots(request):
    """JSON endpoint returning current slot availability and overall stats for live updates."""
    _cleanup_stale_sessions()
    slots = ParkingSlot.objects.all().values('id', 'slot_number', 'size', 'floor', 'is_available')
    active_sessions = ParkingSession.objects.filter(is_active=True).count()
    total_slots = ParkingSlot.objects.count()
    free_slots = ParkingSlot.objects.filter(is_available=True).count()

    return JsonResponse({
        'slots': list(slots),
        'stats': {
            'active_sessions': active_sessions,
            'total_slots': total_slots,
            'free_slots': free_slots
        }
    })


# ─── Navigation ────────────────────────────────────────────────────
def navigate(request, session_id):
    """Step 3 – show a visual guide / map to the reserved slot."""
    session = get_object_or_404(ParkingSession, pk=session_id)
    # Generate QR Code representing the ticket/session id
    qr_data_uri = _make_qr_data_uri(str(session.id))
    return render(request, 'parking/navigate.html', {
        'session': session,
        'qr_data_uri': qr_data_uri,
    })


# ─── Exit flow ─────────────────────────────────────────────────────
def exit_scan(request):
    """Exit gate – driver enters car details to check out and free slot instantly."""
    _cleanup_stale_sessions()
    error_message = None

    if request.method == 'POST':
        form = ExitForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['driver_name'].strip()
            plate = form.cleaned_data['vehicle_plate'].strip().upper()
            vtype = form.cleaned_data['vehicle_type']

            session = ParkingSession.objects.filter(
                driver_name__iexact=name,
                vehicle_plate__iexact=plate,
                vehicle_type=vtype,
                is_active=True,
            ).first()

            if session:
                now = timezone.now()
                duration = now - session.entry_time
                total_seconds = int(duration.total_seconds())
                total_minutes = total_seconds // 60
                hours = total_minutes // 60
                minutes = total_minutes % 60

                if hours >= 1:
                    duration_display = f"{hours} hr {minutes} min"
                else:
                    duration_display = f"{minutes} min"

                rate = getattr(settings, 'PARKING_RATE_PER_HOUR', 40)
                raw_amount = (total_seconds / 3600) * rate
                amount = max(10, round(raw_amount, 2))

                # Finalise & free slot immediately
                session.exit_time = now
                session.amount = amount
                session.is_active = False
                session.save()

                if session.slot:
                    session.slot.is_available = True
                    session.slot.save()

                return render(request, 'parking/receipt.html', {
                    'session': session,
                    'duration_display': duration_display,
                    'amount': amount,
                })
            else:
                error_message = 'No active parking session matches those details. Please check and try again.'
    else:
        form = ExitForm()
    return render(request, 'parking/exit.html', {
        'form': form,
        'error_message': error_message,
    })

# ─── QR Code Generation ───────────────────────────────────────────
def qr_entry(request):
    """Display printable QR code for the ENTRY gate."""
    url = request.build_absolute_uri('/entry/')
    qr_data_uri = _make_qr_data_uri(url)
    return render(request, 'parking/qr_display.html', {
        'qr_data_uri': qr_data_uri,
        'label': 'Entry Gate',
        'target_url': url,
    })


def qr_exit(request):
    """Display printable QR code for the EXIT gate."""
    url = request.build_absolute_uri('/exit/')
    qr_data_uri = _make_qr_data_uri(url)
    return render(request, 'parking/qr_display.html', {
        'qr_data_uri': qr_data_uri,
        'label': 'Exit Gate',
        'target_url': url,
    })
