from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Channel, Message, ChannelMembership, PrivateConversation, PrivateMessage, Report


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Dodatkowe informacje', {'fields': ('role', 'description')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_type', 'is_public', 'created_by', 'created_at')
    list_filter = ('channel_type', 'is_public', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informacje podstawowe', {
            'fields': ('name', 'description', 'channel_type', 'is_public')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'channel', 'created_at', 'content_preview')
    list_filter = ('channel', 'created_at', 'author')
    search_fields = ('content', 'author__username', 'channel__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Wiadomość'


@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'added_by', 'added_at')
    list_filter = ('channel', 'added_at')
    search_fields = ('user__username', 'channel__name')
    readonly_fields = ('added_at',)


@admin.register(PrivateConversation)
class PrivateConversationAdmin(admin.ModelAdmin):
    list_display = ('participant1', 'participant2', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participant1__username', 'participant2__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('participant1', 'participant2')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_author', 'reported_by', 'status', 'action_taken', 'created_at', 'resolved_by')
    list_filter = ('status', 'action_taken', 'created_at')
    search_fields = ('message_author__username', 'reported_by__username', 'reason', 'message_preview')
    readonly_fields = ('created_at', 'resolved_at')


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conversation', 'created_at', 'content_preview')
    list_filter = ('conversation', 'created_at', 'sender')
    search_fields = ('content', 'sender__username', 'conversation__participant1__username', 'conversation__participant2__username')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Wiadomość'
