from django.urls import path
from .views import invest_in_product

urlpatterns = [
    path("create/<int:product_id>/", invest_in_product, name="invest_in_product"),
]