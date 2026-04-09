from django import forms
from .models import ParkingSession, VEHICLE_TYPE_CHOICES


class EntryForm(forms.ModelForm):
    """Form shown at the entry gate."""

    class Meta:
        model = ParkingSession
        fields = ['driver_name', 'phone', 'vehicle_plate', 'vehicle_type']
        widgets = {
            'driver_name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g. John Doe',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g. 9876543210',
                'type': 'tel',
            }),
            'vehicle_plate': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g. KA-01-AB-1234',
            }),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'driver_name': 'Full Name',
            'phone': 'Phone Number',
            'vehicle_plate': 'License Plate',
            'vehicle_type': 'Vehicle Type',
        }


class ExitForm(forms.Form):
    """Form shown at the exit gate."""
    driver_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. John Doe',
        }),
        label='Full Name',
    )
    vehicle_plate = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. KA-01-AB-1234',
        }),
        label='License Plate',
    )
    vehicle_type = forms.ChoiceField(
        choices=VEHICLE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Vehicle Type',
    )
