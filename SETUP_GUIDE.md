# Django Channels WebSocket - Setup & Implementation Guide

## ✅ Co zostało zrobione

Projekt został uaktualniony z obsługą WebSocketów za pośrednictwem Django Channels. Teraz chat działa w **real-time** bez potrzeby odświeżania strony.

### Zainstalowane pakiety:
- ✅ `channels` - obsługa WebSocketów
- ✅ `daphne` - ASGI serwer (zastępuje WSGI)
- ✅ `channels-redis` - dla produkcji (opcjonalnie)

### Nowe pliki:
1. **`record_app/consumers.py`** - WebSocket consumers
   - `ChatConsumer` - obsługa wiadomości w real-time
   - `ChannelUpdateConsumer` - aktualizacje listy kanałów

2. **`record_app/routing.py`** - routing WebSocketów
   - `/ws/chat/<channel_id>/` - chat w kanale
   - `/ws/channels/<user_id>/` - aktualizacje kanałów

3. **`record_app/signals.py`** - sygnały Django
   - Automatyczne powiadamianie o nowych kanałach
   - Automatyczne powiadamianie o usunięciu kanałów
   - Automatyczne powiadamianie o dodaniu użytkownika do kanału

### Zmienione pliki:
- ✅ `record/settings.py` - dodane Channels i konfiguracja channel layer
- ✅ `record/asgi.py` - ProtocolTypeRouter dla WebSocketów
- ✅ `record_app/apps.py` - załadowanie sygnałów
- ✅ `record_app/templates/record_app/home.html` - JavaScript WebSocket
- ✅ `run_daphne.py` - naprawione import sys

---

## 🚀 Jak uruchomić

### Opcja 1: Uruchomienie z Daphne (REKOMENDOWANE)

```bash
cd record
daphne -b 127.0.0.1 -p 8000 record.asgi:application
```

### Opcja 2: Użycie skryptu

```bash
python run_daphne.py
```

### Opcja 3: Za pomocą manage.py (wymaga zainstalowania django-extensions)

```bash
cd record
python manage.py runserver_plus
```

### Ważne ❗
**NIE UŻYWAJ `python manage.py runserver`** - WebSockety nie będą działać!

---

## 🔧 Konfiguracja dla produkcji

### Dla produkcji z Redis:

Zainstaluj Redis:
```bash
# Windows (jeśli masz WSL lub Docker)
wsl
sudo apt-get install redis-server
redis-server

# Lub użyj Dockera
docker run -d -p 6379:6379 redis
```

Zmień konfigurację w `record/settings.py`:
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

---

## ✨ Funkcjonalności

### 1. Wiadomości w Real-Time
- Wiadomość pojawia się na ekranach wszystkich użytkowników w kanale **natychmiast**
- Brak potrzeby odświeżania strony
- Automatyczne scroll do ostatniej wiadomości

### 2. Powiadomienia o użytkownikach
- Powiadomienie gdy użytkownik dołączy do kanału
- Powiadomienie gdy użytkownik opuści kanał
- Automatyczne zamknięcie kanału jeśli został usunięty

### 3. Aktualizacja listy kanałów
- Nowy kanał pojawia się automatycznie
- Kanały publiczne dla wszystkich
- Prywatne kanały tylko dla zaproszonych

### 4. Fallback do tradycyjnego wysyłania
- Jeśli WebSocket się nie połączy, system automatycznie przejdzie na tradycyjne wysyłanie POST
- Brak utraty funkcjonalności

---

## 📝 Testowanie

### Test 1: Real-time wiadomości
1. Otwórz dwie karty/okna przeglądarki
2. Zaloguj się na dwóch różnych kontach
3. Dodaj obu użytkowników do kanału
4. Wyślij wiadomość - pojawi się natychmiast w drugiej karcie

### Test 2: Powiadomienia
1. W jednym oknie usuń kanał
2. Inne okno powinno automatycznie je opuścić/odświeżyć

### Test 3: Nowy kanał
1. Administrator tworzy nowy kanał
2. Zaproszeni użytkownicy zobaczą go bez odświeżania strony

---

## 🐛 Troubleshooting

### WebSocket connection refused
- Upewnij się, że używasz **Daphne**, a nie `runserver`
- Sprawdź czy port 8000 jest wolny
- Sprawdź w konsoli przeglądarki (F12 → Console) czy jest błąd połączenia

### Wiadomości nie przychodzą
1. Sprawdź czy WebSocket jest połączony (konsola przeglądarki)
2. Upewnij się że są w tym samym kanale
3. Odśwież stronę i spróbuj ponownie

### Błędy migracji
```bash
cd record
python manage.py migrate
```

---

## 📊 Architektura

```
┌─────────────────────────────────────────┐
│          Przeglądarka (HTTP)            │
├─────────────────────────────────────────┤
│  ↓ WebSocket upgrade (ws://)             │
│         Daphne ASGI Server              │
│  ↓ Routing (record/asgi.py)              │
│         Consumer (ChatConsumer)         │
│  ↓ Broadcast                             │
│    Channel Layer (In-Memory/Redis)      │
│         ↓ ↓ ↓ (do wszystkich subskryb)   │
│    Wszystkie podłączone przeglądarki    │
└─────────────────────────────────────────┘
```

---

## 🔐 Bezpieczeństwo

- ✅ AuthMiddlewareStack - weryfikacja użytkownika
- ✅ Sprawdzenie dostępu do kanału w consumer
- ✅ Escape HTML w JavaScript (prevencja XSS)
- ✅ CSRF token w formularzu (fallback)

---

## 📈 Performance Tips

1. **For Development**: Użyj In-Memory Channel Layer (default)
2. **For Production**: Użyj Redis Channel Layer
3. **Monitor**: Śledź liczbę otwartych WebSocket połączeń
4. **Scale**: Jeśli potrzebujesz skalować, dodaj load balancer (nginx)

---

## 🎓 Dodatkowe zasoby

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Daphne Documentation](https://github.com/django/daphne)
- [WebSocket MDN Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

## ❓ FAQ

**P: Czy potrzebny mi Redis?**
A: Nie dla developmentu. For produkcji - **TAK**, dla lepszej skalowalności.

**P: Czy mogę używać nginx?**
A: Tak, ale wymagana jest specjalna konfiguracja dla WebSocketów (proxy_pass, upgrade headers).

**P: Czy to działa na Heroku?**
A: Tak, ale za pomocą Heroku Redis add-on.

**P: Czy to bezpieczne?**
A: Tak, jeśli używasz HTTPS (wss://) w produkcji.

---

Generated: Django Channels Implementation
