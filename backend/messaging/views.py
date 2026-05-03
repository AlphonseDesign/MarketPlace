from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages as dj_messages
from django.db.models import Count, Q, F
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Conversation, Message

User = get_user_model()


def staff_required_bo(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url="bo_login")(view_func)


# -------------------------
# CLIENT
# -------------------------

@login_required
def threads(request):
    convs = (
        Conversation.objects.filter(user=request.user)
        .select_related("admin")
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__sender_id=F("admin_id"), messages__read_at__isnull=True),
            )
        )
        .order_by("-last_message_at", "-created_at")
    )
    admins = User.objects.filter(is_staff=True, is_active=True).order_by("username")[:50]
    return render(request, "messaging/threads.html", {"conversations": convs, "admins": admins})


@login_required
def start_chat(request, admin_id: int):
    admin = get_object_or_404(User, pk=admin_id, is_staff=True, is_active=True)
    conv, _ = Conversation.objects.get_or_create(user=request.user, admin=admin)
    return redirect("msg_chat", conv_id=conv.id)


@login_required
def chat(request, conv_id: int):
    conv = get_object_or_404(Conversation.objects.select_related("admin", "user"), pk=conv_id)
    if conv.user_id != request.user.id:
        return HttpResponseForbidden("Accès interdit")

    # Marquer comme lu côté client (messages admin)
    conv.messages.filter(sender_id=conv.admin_id, read_at__isnull=True).update(read_at=timezone.now())

    chat_messages = list(conv.messages.select_related("sender").order_by("-created_at")[:80])
    chat_messages.reverse()

    return render(request, "messaging/chat.html", {"conv": conv, "chat_messages": chat_messages})


@login_required
def api_send(request, conv_id: int):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Méthode invalide"}, status=405)

    conv = get_object_or_404(Conversation, pk=conv_id)
    if conv.user_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Accès interdit"}, status=403)

    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "Message vide"}, status=400)
    if len(body) > 2000:
        return JsonResponse({"ok": False, "error": "Message trop long"}, status=400)

    msg = Message.objects.create(conversation=conv, sender=request.user, body=body)

    conv.last_message_at = msg.created_at
    conv.last_message_preview = body[:160]
    conv.save(update_fields=["last_message_at", "last_message_preview"])

    return JsonResponse({
        "ok": True,
        "message": {
            "id": msg.id,
            "body": msg.body,
            "created_at": msg.created_at.isoformat(),
            "sender": "me",
        }
    })


@login_required
def api_poll(request, conv_id: int):
    conv = get_object_or_404(Conversation, pk=conv_id)
    if conv.user_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Accès interdit"}, status=403)

    after_id = int(request.GET.get("after_id") or 0)
    new_msgs = conv.messages.select_related("sender").filter(id__gt=after_id).order_by("created_at")[:80]

    payload = []
    admin_ids_to_mark = []

    for m in new_msgs:
        sender = "me" if m.sender_id == request.user.id else "admin"
        payload.append({
            "id": m.id,
            "body": m.body,
            "created_at": m.created_at.isoformat(),
            "sender": sender,
        })
        if sender == "admin" and m.read_at is None:
            admin_ids_to_mark.append(m.id)

    if admin_ids_to_mark:
        conv.messages.filter(id__in=admin_ids_to_mark).update(read_at=timezone.now())

    return JsonResponse({"ok": True, "messages": payload})


# -------------------------
# BACKOFFICE
# -------------------------

@staff_required_bo
def bo_inbox(request):
    convs = (
        Conversation.objects.select_related("user", "admin")
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__sender_id=F("user_id"), messages__read_at__isnull=True),
            )
        )
        .order_by("-last_message_at", "-created_at")
    )
    return render(request, "backoffice/messages_list.html", {"conversations": convs})


@staff_required_bo
def bo_chat(request, conv_id: int):
    conv = get_object_or_404(Conversation.objects.select_related("admin", "user"), pk=conv_id)

    # Marquer comme lu côté admin (messages client)
    conv.messages.filter(sender_id=conv.user_id, read_at__isnull=True).update(read_at=timezone.now())

    chat_messages = list(conv.messages.select_related("sender").order_by("-created_at")[:120])
    chat_messages.reverse()

    return render(request, "backoffice/messages_chat.html", {"conv": conv, "chat_messages": chat_messages})


@staff_required_bo
def bo_send(request, conv_id: int):
    if request.method != "POST":
        return redirect("bo_messages_chat", conv_id=conv_id)

    conv = get_object_or_404(Conversation, pk=conv_id)

    body = (request.POST.get("body") or "").strip()
    if not body:
        dj_messages.error(request, "Message vide.")
        return redirect("bo_messages_chat", conv_id=conv_id)

    if len(body) > 2000:
        dj_messages.error(request, "Message trop long.")
        return redirect("bo_messages_chat", conv_id=conv_id)

    msg = Message.objects.create(conversation=conv, sender=request.user, body=body)

    conv.last_message_at = msg.created_at
    conv.last_message_preview = body[:160]
    conv.save(update_fields=["last_message_at", "last_message_preview"])

    dj_messages.success(request, "Réponse envoyée.")
    return redirect("bo_messages_chat", conv_id=conv_id)