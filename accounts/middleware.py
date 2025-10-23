from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.contrib import messages

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                allowed_paths = [
                    reverse("profile_update"),
                    reverse("logout"),
                ]
            except NoReverseMatch:
                allowed_paths = []

            if (
                hasattr(request.user, "is_student")
                and request.user.is_student()
                and not request.user.profile_completed
                and request.path not in allowed_paths
            ):
                messages.warning(request, "⚠️ Please complete your profile to access other pages.")
                return redirect("profile_update")

        return self.get_response(request)
