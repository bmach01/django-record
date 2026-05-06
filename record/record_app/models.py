from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Zwykły Użytkownik'),
        ('moderator', 'Moderator'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Channel(models.Model):
    CHANNEL_TYPE_CHOICES = [
        ('text', 'Kanał tekstowy'),
        ('voice', 'Kanał głosowy'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    channel_type = models.CharField(
        max_length=10,
        choices=CHANNEL_TYPE_CHOICES,
        default='text'
    )
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_channels')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Kanał'
        verbose_name_plural = 'Kanały'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"


class ChannelMembership(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channel_memberships')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_members')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('channel', 'user')
        verbose_name = 'Członkostwo w kanale'
        verbose_name_plural = 'Członkostwa w kanałach'
    
    def __str__(self):
        return f"{self.user.username} w {self.channel.name}"


class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Wiadomość'
        verbose_name_plural = 'Wiadomości'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username} w {self.channel.name}: {self.content[:50]}"
