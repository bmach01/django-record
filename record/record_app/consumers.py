import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Channel, Message, ChannelMembership, PrivateConversation, PrivateMessage


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messages.
    Handles incoming messages and broadcasts them to all users in the channel.
    """

    async def connect(self):
        """
        Called when a WebSocket connection is established.
        """
        self.channel_id = self.scope["url_route"]["kwargs"]["channel_id"]
        self.channel_group_name = f"chat_{self.channel_id}"
        self.user = self.scope["user"]

        # Sprawdzenie dostępu do kanału
        has_access = await self.check_channel_access()
        if not has_access:
            await self.close()
            return

        # Dodaj do grupy kanału
        await self.channel_layer.group_add(self.channel_group_name, self.channel_name)
        await self.accept()

        # Powiadom o dołączeniu
        await self.channel_layer.group_send(
            self.channel_group_name,
            {
                "type": "user_joined",
                "username": self.user.username,
                "user_id": self.user.id,
            },
        )

    async def disconnect(self, close_code):
        """
        Called when a WebSocket connection is closed.
        """
        if hasattr(self, "channel_group_name"):
            # Powiadom o opuszczeniu
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    "type": "user_left",
                    "username": self.user.username,
                    "user_id": self.user.id,
                },
            )

            # Usuń z grupy kanału
            await self.channel_layer.group_discard(
                self.channel_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """
        Called when a message is received from the WebSocket.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "chat_message":
                content = data.get("message", "").strip()
                if content:
                    # Zapisz wiadomość do bazy danych
                    message = await self.save_message(content)
                    if message:
                        # Wyślij do grupy
                        await self.channel_layer.group_send(
                            self.channel_group_name,
                            {
                                "type": "chat_message",
                                "message": content,
                                "username": self.user.username,
                                "user_id": self.user.id,
                                "timestamp": message.created_at.isoformat(),
                                "message_id": message.id,
                            },
                        )
        except json.JSONDecodeError:
            pass

    async def chat_message(self, event):
        """
        Receive a chat message from the group and send it to the WebSocket.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "username": event["username"],
                    "user_id": event["user_id"],
                    "timestamp": event["timestamp"],
                    "message_id": event["message_id"],
                }
            )
        )

    async def user_joined(self, event):
        """
        Receive user joined notification from the group.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "username": event["username"],
                    "user_id": event["user_id"],
                }
            )
        )

    async def user_left(self, event):
        """
        Receive user left notification from the group.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "username": event["username"],
                    "user_id": event["user_id"],
                }
            )
        )

    async def channel_updated(self, event):
        """
        Receive channel update notification.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "channel_updated",
                    "action": event.get("action"),
                    "channel_name": event.get("channel_name"),
                    "channel_id": event.get("channel_id"),
                }
            )
        )

    @database_sync_to_async
    def check_channel_access(self):
        """
        Check if the user has access to the channel.
        """
        try:
            channel = Channel.objects.get(id=self.channel_id)
            # Sprawdzenie: publiczny kanał, członek, twórca, lub admin
            is_public = channel.is_public
            is_member = channel.members.filter(user=self.user).exists()
            is_creator = channel.created_by == self.user
            is_admin = self.user.role in ["admin", "moderator"]

            return is_public or is_member or is_creator or is_admin
        except Channel.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        """
        Save a message to the database.
        """
        try:
            channel = Channel.objects.get(id=self.channel_id)
            message = Message.objects.create(
                channel=channel, author=self.user, content=content
            )
            return message
        except Channel.DoesNotExist:
            return None


class ChannelUpdateConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for channel list updates.
    Handles updates to the channel list (new channels, deleted channels, etc.)
    """

    async def connect(self):
        """
        Called when a WebSocket connection is established.
        """
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}_channels"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        """
        Called when a WebSocket connection is closed.
        """
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def channel_created(self, event):
        """
        Receive channel created notification.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "channel_created",
                    "channel_id": event["channel_id"],
                    "channel_name": event["channel_name"],
                    "is_public": event["is_public"],
                }
            )
        )

    async def channel_deleted(self, event):
        """
        Receive channel deleted notification.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "channel_deleted",
                    "channel_id": event["channel_id"],
                }
            )
        )

    async def user_added_to_channel(self, event):
        """
        Receive user added to channel notification.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_added_to_channel",
                    "channel_id": event["channel_id"],
                    "channel_name": event["channel_name"],
                }
            )
        )


class PrivateChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for private chat messages.
    Handles real-time private messaging between two users.
    """

    async def connect(self):
        """
        Called when a WebSocket connection is established.
        """
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"private_chat_{self.conversation_id}"
        self.user = self.scope["user"]

        # Sprawdzenie dostępu do konwersacji
        has_access = await self.check_conversation_access()
        if not has_access:
            await self.close()
            return

        # Dodaj do grupy konwersacji
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when a WebSocket connection is closed.
        """
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Called when a message is received from the WebSocket.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "chat_message":
                content = data.get("message", "").strip()
                if content:
                    # Zapisz wiadomość do bazy danych
                    message = await self.save_message(content)
                    if message:
                        # Wyślij do grupy
                        await self.channel_layer.group_send(
                            self.group_name,
                            {
                                "type": "chat_message",
                                "message": content,
                                "username": self.user.username,
                                "user_id": self.user.id,
                                "timestamp": message.created_at.isoformat(),
                                "message_id": message.id,
                            },
                        )
        except json.JSONDecodeError:
            pass

    async def chat_message(self, event):
        """
        Receive a chat message from the group and send it to the WebSocket.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "username": event["username"],
                    "user_id": event["user_id"],
                    "timestamp": event["timestamp"],
                    "message_id": event["message_id"],
                }
            )
        )

    @database_sync_to_async
    def check_conversation_access(self):
        """
        Check if the user has access to the private conversation.
        """
        try:
            conversation = PrivateConversation.objects.get(id=self.conversation_id)
            return (self.user == conversation.participant1 or 
                    self.user == conversation.participant2)
        except PrivateConversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        """
        Save a private message to the database.
        """
        try:
            conversation = PrivateConversation.objects.get(id=self.conversation_id)
            message = PrivateMessage.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            return message
        except PrivateConversation.DoesNotExist:
            return None
