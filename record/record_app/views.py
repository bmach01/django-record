from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from .forms import LoginForm, RegisterForm, ChannelForm, MessageForm, PrivateMessageForm, StartPrivateConversationForm
from .models import Channel, ChannelMembership, Message, PrivateConversation, PrivateMessage

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Zalogowany jako {username}")
                return redirect('home')
            else:
                messages.error(request, "Zła nazwa użytkownika lub hasło.")
    else:
        form = LoginForm()
    
    return render(request, 'record_app/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Rejestracja udana! Teraz się zaloguj.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
    
    return render(request, 'record_app/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "Wylogowany pomyślnie.")
    return redirect('login')


@login_required(login_url='login')
def home_view(request):
    # Pobierz wszystkie kanały dostępne dla użytkownika
    # (publiczne, które utworzył, lub do których należy)
    all_channels = Channel.objects.filter(
        Q(is_public=True) |
        Q(members__user=request.user) | 
        Q(created_by=request.user)
    ).distinct()
    
    # Grupuj kanały po typie
    text_channels = all_channels.filter(channel_type='text').order_by('name')
    voice_channels = all_channels.filter(channel_type='voice').order_by('name')
    
    # Pobierz wybrany kanał (jeśli istnieje)
    selected_channel_id = request.GET.get('channel_id')
    selected_channel = None
    messages_list = []
    
    if selected_channel_id:
        try:
            selected_channel = Channel.objects.get(id=selected_channel_id)
            
            # Sprawdź dostęp do kanału
            is_member = selected_channel.members.filter(user=request.user).exists() or \
                       selected_channel.is_public or \
                       selected_channel.created_by == request.user
            
            if not is_member and not request.user.role == 'admin':
                messages.error(request, "Nie masz dostępu do tego kanału.")
                selected_channel = None
            else:
                messages_list = selected_channel.messages.all()[:50]  # Ostatnie 50 wiadomości
        except Channel.DoesNotExist:
            pass
    
    # Formularz do wysyłania wiadomości
    message_form = MessageForm() if selected_channel else None
    
    context = {
        'text_channels': text_channels,
        'voice_channels': voice_channels,
        'selected_channel': selected_channel,
        'messages': messages_list,
        'message_form': message_form,
        'is_admin': request.user.role in ['admin', 'moderator'],
    }
    
    return render(request, 'record_app/home.html', context)


@login_required(login_url='login')
def create_channel_view(request):
    # Tylko administratorzy mogą tworzyć kanały
    if request.user.role not in ['admin', 'moderator']:
        messages.error(request, "Nie masz uprawnień do tworzenia kanałów.")
        return redirect('home')
    
    if request.method == 'POST':
        form = ChannelForm(request.POST)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.created_by = request.user
            channel.save()
            
            # Dodaj twórcę kanału do listy członków
            ChannelMembership.objects.create(
                channel=channel,
                user=request.user,
                added_by=request.user
            )
            
            messages.success(request, f"Kanał '{channel.name}' został utworzony.")
            return redirect('home')
    else:
        form = ChannelForm()
    
    context = {'form': form, 'action': 'Utwórz kanał'}
    return render(request, 'record_app/channel_form.html', context)


@login_required(login_url='login')
def edit_channel_view(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    
    # Tylko administratorzy i twórca mogą edytować
    if request.user not in [channel.created_by] and request.user.role not in ['admin', 'moderator']:
        messages.error(request, "Nie masz uprawnień do edytowania tego kanału.")
        return redirect('home')
    
    if request.method == 'POST':
        form = ChannelForm(request.POST, instance=channel)
        if form.is_valid():
            form.save()
            messages.success(request, f"Kanał '{channel.name}' został zaktualizowany.")
            return redirect('home')
    else:
        form = ChannelForm(instance=channel)
    
    context = {'form': form, 'action': 'Edytuj kanał', 'channel': channel}
    return render(request, 'record_app/channel_form.html', context)


@login_required(login_url='login')
def delete_channel_view(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    
    # Tylko administratorzy mogą usuwać
    if request.user not in [channel.created_by] and request.user.role not in ['admin', 'moderator']:
        messages.error(request, "Nie masz uprawnień do usuwania kanałów.")
        return redirect('home')
    
    if request.method == 'POST':
        channel_name = channel.name
        channel.delete()
        messages.success(request, f"Kanał '{channel_name}' został usunięty.")
        return redirect('home')
    
    context = {'channel': channel}
    return render(request, 'record_app/delete_channel.html', context)


@login_required(login_url='login')
def send_message_view(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    
    # Sprawdź dostęp
    is_member = channel.members.filter(user=request.user).exists() or \
               channel.is_public or \
               channel.created_by == request.user
    
    if not is_member and not request.user.role == 'admin':
        messages.error(request, "Nie masz dostępu do tego kanału.")
        return redirect('home')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.channel = channel
            message.author = request.user
            message.save()
            messages.success(request, "Wiadomość wysłana.")
    
    return redirect(reverse('home') + f'?channel_id={channel_id}')


@login_required(login_url='login')
def invite_to_channel_view(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    
    # Tylko administratorzy mogą zapraszać
    if request.user not in [channel.created_by] and request.user.role not in ['admin', 'moderator']:
        messages.error(request, "Nie masz uprawnień do zapraszania użytkowników.")
        return redirect('home')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            membership, created = ChannelMembership.objects.get_or_create(
                channel=channel,
                user=user,
                defaults={'added_by': request.user}
            )
            if created:
                messages.success(request, f"Użytkownik '{user.username}' został dodany do kanału.")
            else:
                messages.info(request, f"Użytkownik '{user.username}' już należy do kanału.")
        except User.DoesNotExist:
            messages.error(request, "Użytkownik nie istnieje.")
    
    users = User.objects.exclude(
        channel_memberships__channel=channel
    ).exclude(id=channel.created_by.id).distinct()
    
    context = {'channel': channel, 'users': users}
    return render(request, 'record_app/invite_channel.html', context)


@login_required(login_url='login')
def private_conversations_view(request):
    """Wyświetla listę prywatnych konwersacji użytkownika."""
    conversations = PrivateConversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).order_by('-updated_at')
    
    # Dodaj drugiego uczestnika do każdej konwersacji
    for conversation in conversations:
        conversation.other_user = conversation.get_other_user(request.user)
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'record_app/private_conversations.html', context)


@login_required(login_url='login')
def private_chat_view(request, conversation_id):
    """Wyświetla prywatną konwersację i umożliwia wysyłanie wiadomości przez WebSocket."""
    conversation = get_object_or_404(PrivateConversation, id=conversation_id)
    
    # Sprawdzenie, czy użytkownik jest uczestnikiem rozmowy
    if request.user not in [conversation.participant1, conversation.participant2]:
        messages.error(request, "Nie masz dostępu do tej rozmowy.")
        return redirect('private_conversations')
    
    # Pobierz drugiego uczestnika
    other_user = conversation.get_other_user(request.user)
    
    # Pobierz wiadomości (ostatnie 50)
    private_messages = conversation.messages.all()[:50]
    
    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': private_messages,
    }
    return render(request, 'record_app/private_chat.html', context)


@login_required(login_url='login')
def start_private_conversation_view(request):
    """Pozwala użytkownikowi wybrać, z kim chce rozmawiać prywatnie."""
    if request.method == 'POST':
        form = StartPrivateConversationForm(request.POST, current_user=request.user)
        if form.is_valid():
            other_user = form.cleaned_data['user']
            
            # Sprawdzenie lub utworzenie konwersacji
            # Upewnij się, że participant1 ma mniejszy id niż participant2 dla spójności
            if request.user.id < other_user.id:
                conversation, created = PrivateConversation.objects.get_or_create(
                    participant1=request.user,
                    participant2=other_user,
                )
            else:
                conversation, created = PrivateConversation.objects.get_or_create(
                    participant1=other_user,
                    participant2=request.user,
                )
            
            return redirect('private_chat', conversation_id=conversation.id)
    else:
        form = StartPrivateConversationForm(current_user=request.user)
    
    context = {
        'form': form,
        'users': form.user_queryset,
    }
    return render(request, 'record_app/start_private_conversation.html', context)
