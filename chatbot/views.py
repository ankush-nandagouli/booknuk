from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .serializers import ConversationSerializer
from .ai_utils import handle_user_message

User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def start_conversation(request):
    """
    Start a new conversation.
    Body: { "user_id": <optional>, "title": <optional> }
    """
    user = None
    user_id = request.data.get("user_id")

    if request.user.is_authenticated:
        user = request.user
    elif user_id:
        user = User.objects.filter(pk=user_id).first()

    conv = Conversation.objects.create(
        user=user,
        title=request.data.get("title", "Chat Session")
    )

    return Response(
        {"conversation_id": conv.id, "message": "✅ Conversation started"},
        status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def chat_message(request):
    """
    Send a message and get chatbot reply.
    Body: { "conversation_id": <id>, "text": "..." }
    """
    text = request.data.get("text", "").strip()
    if not text:
        return Response({"error": "Empty message"}, status=status.HTTP_400_BAD_REQUEST)

    conv_id = request.data.get("conversation_id")
    if conv_id:
        conv = get_object_or_404(Conversation, pk=conv_id)
    else:
        conv = Conversation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            title="Quick Chat"
        )

    # Save user message
    Message.objects.create(conversation=conv, role="user", text=text)

    # Generate reply using rule-based logic
    reply = handle_user_message(text, user=conv.user)

    # Save bot message
    bot_msg = Message.objects.create(conversation=conv, role="bot", text=reply)

    return Response({
        "reply": reply,
        "conversation_id": conv.id,
        "message_id": bot_msg.id
    }, status=status.HTTP_200_OK)


