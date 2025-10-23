from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """
    A conversation between a user and the chatbot.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Conversation #{self.pk} - {self.user or 'anon'}"


class Message(models.Model):
    """
    A message in a conversation.
    role: 'user' or 'bot' or 'system'
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=(("user","user"),("bot","bot"),("system","system")))
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # optional link to LMS entities
    book = models.ForeignKey("books.Book", on_delete=models.SET_NULL, null=True, blank=True)
    issued_book = models.ForeignKey("books.IssuedBook", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.role}: {self.text[:80]}"
