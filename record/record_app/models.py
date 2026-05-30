from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.templatetags.static import static

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
    is_banned = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return static('images/default_pfp.jpg')

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
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    audio = models.FileField(upload_to='messages_audio/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Wiadomość'
        verbose_name_plural = 'Wiadomości'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username} w {self.channel.name}: {self.content[:50]}"


class PrivateConversation(models.Model):
    """
    Konwersacja prywatna pomiędzy dwoma użytkownikami.
    Do takiej rozmowy nie można dodawać kolejnych użytkowników.
    """
    participant1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_conversations_as_participant1')
    participant2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_conversations_as_participant2')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('participant1', 'participant2')
        verbose_name = 'Konwersacja prywatna'
        verbose_name_plural = 'Konwersacje prywatne'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Rozmowa: {self.participant1.username} <-> {self.participant2.username}"
    
    def get_other_user(self, user):
        """Zwraca drugiego uczestnika rozmowy."""
        if user == self.participant1:
            return self.participant2
        return self.participant1


class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Oczekujące'),
        ('resolved', 'Rozwiązane'),
    ]
    ACTION_CHOICES = [
        ('delete_message', 'Usunięto wiadomość'),
        ('ban_user', 'Zablokowano użytkownika'),
        ('dismissed', 'Odrzucono'),
    ]

    message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    message_author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_reports')
    message_preview = models.TextField(blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_reports')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES, blank=True)

    class Meta:
        verbose_name = 'Zgłoszenie'
        verbose_name_plural = 'Zgłoszenia'
        ordering = ['-created_at']
        unique_together = ('message', 'reported_by')

    def __str__(self):
        reporter = self.reported_by.username if self.reported_by else '?'
        return f"Zgłoszenie przez {reporter} @ {self.created_at:%Y-%m-%d %H:%M}"


class PrivateMessage(models.Model):
    """
    Pojedyncza wiadomość prywatna w konwersacji.
    """
    conversation = models.ForeignKey(PrivateConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_private_messages')
    image = models.ImageField(upload_to='private_messages/', blank=True, null=True)
    audio = models.FileField(upload_to='private_messages_audio/', blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Wiadomość prywatna'
        verbose_name_plural = 'Wiadomości prywatne'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
