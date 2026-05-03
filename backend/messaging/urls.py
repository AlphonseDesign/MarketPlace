from django.urls import path
from . import views

urlpatterns = [
    path("", views.threads, name="msg_threads"),
    path("start/<int:admin_id>/", views.start_chat, name="msg_start"),
    path("chat/<int:conv_id>/", views.chat, name="msg_chat"),

    # API polling + send (client)
    path("api/<int:conv_id>/send/", views.api_send, name="msg_api_send"),
    path("api/<int:conv_id>/poll/", views.api_poll, name="msg_api_poll"),
]