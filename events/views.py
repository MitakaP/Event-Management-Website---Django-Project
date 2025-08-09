from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Event, EventComment, Ticket, CustomUser, Notification, EventCategory
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, EventForm,
    EventCommentForm, TicketPurchaseForm, CustomPasswordResetForm, ProfileUpdateForm
)
from django.contrib.auth.views import (
    LoginView, PasswordResetView, PasswordResetConfirmView, LogoutView
)

from asgiref.sync import sync_to_async


class HomeView(TemplateView):
    template_name = 'events/index.html'
    
    async def get(self, request, *args, **kwargs):
        context = await self.get_context_data(**kwargs)
        return self.render_to_response(context)
    
    async def get_context_data(self, **kwargs):
        context = await sync_to_async(super().get_context_data)(**kwargs)
        context['upcoming_events'] = await self.get_upcoming_events()
        return context
    
    @sync_to_async
    def get_upcoming_events(self):
        return list(Event.objects.filter(
            start_date__gt=timezone.now(),
            is_active=True
        ).order_by('start_date')[:6])


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Event.objects.filter(is_active=True, start_date__gt=timezone.now())
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(event_type='public')
        
        return queryset.order_by('start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = EventCategory.objects.all()
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        
        if event.event_type == 'private' and not self.request.user.is_authenticated:
            context['access_denied'] = True
            return context
        
        context['access_denied'] = False
        context['comments'] = event.comments.all().order_by('-created_at')
        context['comment_form'] = EventCommentForm()
        context['event'] = event
        
        if self.request.user.is_authenticated:
            context['has_ticket'] = event.tickets.filter(
                attendee=self.request.user,
                is_active=True
            ).exists()
            context['ticket_form'] = TicketPurchaseForm(event=event, user=self.request.user)
        
        return context
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        event = self.get_object()
        form = EventCommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.event = event
            comment.user = request.user
            comment.save()
            messages.success(request, 'Your comment has been posted.')
        else:
            messages.error(request, 'There was an error posting your comment.')
        
        return redirect('event_detail', pk=event.pk)


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_create.html'
    success_url = reverse_lazy('event_list')
    
    def test_func(self):
        return self.request.user.user_type in [2, 3] 
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)


class MyEventsListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/my_events.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user).order_by('-start_date')
    

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_update.html'
    
    def test_func(self):
        event = self.get_object()
        return self.request.user == event.organizer or self.request.user.user_type == 3
    
    def get_success_url(self):
        return reverse_lazy('event_detail', kwargs={'pk': self.object.pk})


class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('event_list')
    
    def test_func(self):
        event = self.get_object()
        print(event)
        return self.request.user == event.organizer or self.request.user.user_type == 3
    
    def delete(self, request, *args, **kwargs):
        event = self.get_object()
        event.is_active = False
        event.save()
        
        for ticket in event.tickets.filter(is_active=True):
            Notification.objects.create(
                user=ticket.attendee,
                notification_type='event_cancellation',
                message=f"The event '{event.title}' has been cancelled.",
                related_event=event
            )
        
        messages.success(request, 'Event has been cancelled.')
        return redirect(self.get_success_url())


@login_required
def purchase_ticket(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST, event=event, user=request.user)
        
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            for _ in range(quantity):
                ticket = Ticket.objects.create(
                    event=event,
                    attendee=request.user,
                    is_active=True
                )
            
            Notification.objects.create(
                user=request.user,
                notification_type='ticket_confirmation',
                message=f"Your ticket(s) for '{event.title}' have been confirmed.",
                related_event=event
            )
            
            messages.success(request, f'Successfully purchased {quantity} ticket(s) for {event.title}.')
            return redirect('user_dashboard')
    else:
        form = TicketPurchaseForm(event=event, user=request.user)
    
    return render(request, 'events/ticket_purchase.html', {
        'form': form,
        'event': event
    })


class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'events/user_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.user_type == 1:  # Attendee
            context['upcoming_events'] = Event.objects.filter(
                tickets__attendee=user,
                tickets__is_active=True,
                start_date__gt=timezone.now()
            ).distinct()
            context['past_events'] = Event.objects.filter(
                tickets__attendee=user,
                tickets__is_active=True,
                start_date__lte=timezone.now()
            ).distinct()
        elif user.user_type == 2:  # Organizer
            context['organized_events'] = user.organized_events.filter(is_active=True)
            context['past_events'] = user.organized_events.filter(
                is_active=True,
                start_date__lte=timezone.now()
            )
        
        context['unread_notifications'] = user.notifications.filter(is_read=False)
        return context


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'events/registration/login.html'
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        
        if self.request.user.user_type == 3:
            return reverse_lazy('admin_dashboard')
        return reverse_lazy('user_dashboard')
    
    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)
        return super().form_valid(form)


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'events/registration/password_reset.html'
    email_template_name = 'events/registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'events/registration/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful. Please log in.')
        return response
        
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'events/registration/update_profile.html'
    success_url = reverse_lazy('profile_update')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.title()}: {error}")
        return super().form_invalid(form)
    

class UserTicketsView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'events/user_tickets.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        return Ticket.objects.filter(attendee=self.request.user, is_active=True)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = EventComment
    fields = ['content', 'rating']
    template_name = 'events/comment_edit.html'
    
    def get_success_url(self):
        return reverse_lazy('event_detail', kwargs={'pk': self.object.event.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Comment updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.title()}: {error}")
        return super().form_invalid(form)

    def get_queryset(self):
        return EventComment.objects.filter(user=self.request.user)


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = EventComment
    template_name = 'events/comment_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('event_detail', kwargs={'pk': self.object.event.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Comment deleted successfully!')
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return EventComment.objects.filter(user=self.request.user)
    

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home') 
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response


@login_required
def mark_notification_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('user_dashboard')


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'events/admin/custom_admin.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_events'] = Event.objects.count()
        context['total_users'] = CustomUser.objects.count()
        context['recent_events'] = Event.objects.order_by('-created_at')[:5]
        context['recent_users'] = CustomUser.objects.order_by('-date_joined')[:5]
        return context
    

class MarkAllNotificationsAsReadView(View):
    def get(self, request, *args, **kwargs):
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        unread_notifications.update(is_read=True)
        return redirect('user_dashboard')