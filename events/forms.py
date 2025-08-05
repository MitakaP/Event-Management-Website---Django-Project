from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import CustomUser, Event, EventComment, Ticket



class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'profile_picture', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and CustomUser.objects.filter(phone_number=phone_number).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This phone number is already in use.")
        return phone_number

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })
        self.fields['profile_picture'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })

        
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'user_type', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].choices = [
            (value, label) 
            for value, label in CustomUser.USER_TYPE_CHOICES 
            if value != 3 
        ]
        self.fields['user_type'].initial = 1

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and CustomUser.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("This phone number is already in use.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        # Add any additional cross-field validation here if needed
        return cleaned_data
    


class CustomAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)


class EventForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control datetime-picker',
            'placeholder': 'Select start date and time'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control datetime-picker',
            'placeholder': 'Select end date and time'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_date', 'end_date', 
                 'category', 'event_type', 'capacity', 'price', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter event title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your event in detail',
                'rows': 4
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter physical location or online meeting link'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'event_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum attendees',
                'min': 1
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'min': 0,
                'step': '0.01'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'title': 'Event Title',
            'description': 'Description',
            'location': 'Location',
            'start_date': 'Start Date & Time',
            'end_date': 'End Date & Time',
            'category': 'Category',
            'event_type': 'Event Type',
            'capacity': 'Maximum Capacity',
            'price': 'Ticket Price (USD)',
            'image': 'Event Image'
        }
        help_texts = {
            'description': 'Provide a detailed description of your event (minimum 50 characters)',
            'capacity': 'Maximum number of attendees allowed',
            'price': 'Set to 0 for free events',
            'image': 'Recommended size: 1200×600 pixels (JPEG or PNG)'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError("End date must be after start date.")
            if start_date < timezone.now():
                raise ValidationError("Start date cannot be in the past.")
        
        description = cleaned_data.get('description')
        if description and len(description) < 50:
            raise ValidationError("Description must be at least 50 characters long.")
        
        return cleaned_data
    

class EventCommentForm(forms.ModelForm):
    class Meta:
        model = EventComment
        fields = ['content', 'rating']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 2}),
        }

class TicketPurchaseForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1, initial=1)
    
    class Meta:
        model = Ticket
        fields = []
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.event and quantity > self.event.available_tickets:
            raise ValidationError(f"Only {self.event.available_tickets} tickets available.")
        return quantity

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )

    