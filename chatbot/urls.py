from django.urls import path
from . import views

urlpatterns = [
    path("start/", views.start_conversation, name="chat_start"),
    path("message/", views.chat_message, name="chat_message"),

]
