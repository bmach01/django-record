from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages


class BannedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and getattr(request.user, 'is_banned', False):
            logout(request)
            messages.error(request, "Twoje konto zostało zablokowane.")
            return redirect('login')
        return self.get_response(request)
