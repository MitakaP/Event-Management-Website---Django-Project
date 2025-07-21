from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Event, EventCategory, Ticket, EventComment, Notification
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture', 'bio')}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'start_date', 'end_date', 'location', 'event_type', 'is_active')
    list_filter = ('event_type', 'is_active', 'category', 'start_date')
    search_fields = ('title', 'description', 'location', 'organizer__username')
    date_hierarchy = 'start_date'
    raw_id_fields = ('organizer',)
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organizer=request.user)

class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'event', 'attendee', 'purchase_date', 'is_active')
    list_filter = ('is_active', 'event', 'purchase_date')
    search_fields = ('ticket_number', 'event__title', 'attendee__username')
    raw_id_fields = ('event', 'attendee')
    readonly_fields = ('purchase_date', 'ticket_number')

class EventCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'event__title', 'content')
    raw_id_fields = ('user', 'event')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    raw_id_fields = ('user', 'related_event')
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected notifications as read"

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventCategory)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(EventComment, EventCommentAdmin)
admin.site.register(Notification, NotificationAdmin)