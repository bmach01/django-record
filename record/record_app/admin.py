from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Channel, Message, ChannelMembership


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
