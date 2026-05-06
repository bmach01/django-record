from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),
    path('channel/create/', views.create_channel_view, name='create_channel'),
    path('channel/<int:channel_id>/edit/', views.edit_channel_view, name='edit_channel'),
    path('channel/<int:channel_id>/delete/', views.delete_channel_view, name='delete_channel'),
    path('channel/<int:channel_id>/message/', views.send_message_view, name='send_message'),
    path('channel/<int:channel_id>/invite/', views.invite_to_channel_view, name='invite_channel'),
]
