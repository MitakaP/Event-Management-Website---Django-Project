from django.urls import path
from .views import (
    HomeView, EventListView, EventDetailView, EventCreateView,
    EventUpdateView, EventDeleteView, purchase_ticket, UserDashboardView,
    CustomLoginView, RegisterView, CustomPasswordResetView, mark_notification_as_read,
    AdminDashboardView, CustomLogoutView
)
from django.contrib.auth.views import (
    PasswordResetDoneView, PasswordResetCompleteView, 
    LogoutView, PasswordResetConfirmView,
)

urlpatterns = [
    # Public views
    path('', HomeView.as_view(), name='home'),
    path('events/', EventListView.as_view(), name='event_list'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('events/create/', EventCreateView.as_view(), name='event_create'),
    path('events/<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),
    path('events/<int:pk>/delete/', EventDeleteView.as_view(), name='event_delete'),
    path('events/<int:pk>/purchase/', purchase_ticket, name='purchase_ticket'),
    path('dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    path('notifications/<int:pk>/mark-read/', mark_notification_as_read, name='mark_notification_read'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]