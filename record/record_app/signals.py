from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Channel, ChannelMembership


channel_layer = get_channel_layer()


@receiver(post_save, sender=Channel)
def channel_created_signal(sender, instance, created, **kwargs):
    """
    Signal sent when a new channel is created.
    Notifies all users about the new channel.
    """
    if created:
        # Pobierz wszystkich użytkowników do powiadomienia
        # - administratorów
        # - członków kanału
        # - dla kanałów publicznych wszyscy
        from django.contrib.auth import get_user_model

        User = get_user_model()
        users_to_notify = set()

        if instance.is_public:
            # Powiadom wszystkich
            users_to_notify = set(User.objects.values_list("id", flat=True))
        else:
            # Powiadom członków i administratorów
            members = instance.members.values_list("user_id", flat=True)
            admins = User.objects.filter(role__in=["admin", "moderator"]).values_list(
                "id", flat=True
            )
            users_to_notify = set(members) | set(admins)

        # Wyślij notyfikacje
        for user_id in users_to_notify:
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}_channels",
                {
                    "type": "channel_created",
                    "channel_id": instance.id,
                    "channel_name": instance.name,
                    "is_public": instance.is_public,
                },
            )


@receiver(post_delete, sender=Channel)
def channel_deleted_signal(sender, instance, **kwargs):
    """
    Signal sent when a channel is deleted.
    Notifies all users about the deleted channel.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    users_to_notify = set()

    # Powiadom wszystkich zainteresowanych
    members = instance.members.values_list("user_id", flat=True)
    admins = User.objects.filter(role__in=["admin", "moderator"]).values_list(
        "id", flat=True
    )
    users_to_notify = set(members) | set(admins)

    # Wyślij notyfikacje
    for user_id in users_to_notify:
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}_channels",
            {
                "type": "channel_deleted",
                "channel_id": instance.id,
            },
        )


@receiver(post_save, sender=ChannelMembership)
def user_added_to_channel_signal(sender, instance, created, **kwargs):
    """
    Signal sent when a user is added to a channel.
    Notifies the user about the new channel they were added to.
    """
    if created:
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.user.id}_channels",
            {
                "type": "user_added_to_channel",
                "channel_id": instance.channel.id,
                "channel_name": instance.channel.name,
            },
        )
