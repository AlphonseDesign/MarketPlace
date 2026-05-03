from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_user",
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_admin",
    )

    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_preview = models.CharField(max_length=160, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "admin")
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        return f"Conv({self.user.username} <-> {self.admin.username})"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")

    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    # lu par le destinataire (conversation à 2)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Msg({self.sender.username})"

    def mark_read(self):
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])