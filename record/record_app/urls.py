from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),
    path('channel/create/', views.create_channel_view, name='create_channel'),
    path('channel/<int:channel_id>/edit/', views.edit_channel_view, name='edit_channel'),
    path('channel/<int:channel_id>/delete/', views.delete_channel_view, name='delete_channel'),
    path('channel/<int:channel_id>/message/', views.send_message_view, name='send_message'),
    path('channel/<int:channel_id>/invite/', views.invite_to_channel_view, name='invite_channel'),
    # Zarządzanie użytkownikami
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/ban/', views.ban_user_view, name='ban_user'),
    path('users/<int:user_id>/unban/', views.unban_user_view, name='unban_user'),
    # Zgłoszenia
    path('message/<int:message_id>/report/', views.report_message_view, name='report_message'),
    path('reports/', views.reports_list_view, name='reports_list'),
    path('reports/<int:report_id>/resolve/', views.resolve_report_view, name='resolve_report'),
    # Prywatne wiadomości
    path('private/', views.private_conversations_view, name='private_conversations'),
    path('private/<int:conversation_id>/', views.private_chat_view, name='private_chat'),
    path('private/start/', views.start_private_conversation_view, name='start_private_conversation'),
]
