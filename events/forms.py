from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import CustomUser, Event, EventComment, Ticket

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, initial=1)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'user_type', 'phone_number')

class CustomAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)

class EventForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_date', 'end_date', 
                 'category', 'event_type', 'capacity', 'price', 'image']
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError("End date must be after start date.")
            if start_date < timezone.now():
                raise ValidationError("Start date cannot be in the past.")
        
        return cleaned_data

class EventCommentForm(forms.ModelForm):
    class Meta:
        model = EventComment
        fields = ['content', 'rating']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
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

    