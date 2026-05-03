from django.urls import path
from .views import (
    deposit_request_create,
    deposit_request_confirm,
    withdraw_request_create,
    withdraw_request_confirm,
)

urlpatterns = [
    path("deposit/", deposit_request_create, name="deposit_request_create"),
    path("deposit/confirm/<int:pk>/", deposit_request_confirm, name="deposit_request_confirm"),

    path("withdraw/", withdraw_request_create, name="withdraw_request_create"),
    path("withdraw/confirm/<int:pk>/", withdraw_request_confirm, name="withdraw_request_confirm"),
]