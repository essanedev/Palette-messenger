# apps/core/middleware.py
from django.shortcuts import redirect
from django.urls import reverse


class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_paths = [
            '/accounts/login/',
            '/accounts/register/',
            '/accounts/password_reset/',
            '/admin/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        path = request.path

        if any(path.startswith(public_path) for public_path in self.public_paths):
            return self.get_response(request)

        if path == '/':
            if request.user.is_authenticated:
                return redirect('users:discover')
            else:
                return redirect('users:login')

        if not request.user.is_authenticated and path not in [reverse('users:login'), reverse('users:register')]:
            return redirect(f"{reverse('users:login')}?next={path}")

        response = self.get_response(request)
        return response