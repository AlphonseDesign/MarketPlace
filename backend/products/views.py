from django.shortcuts import render, get_object_or_404
from .models import InvestmentProduct
from wallet.models import Wallet


def product_list(request):
    products = InvestmentProduct.objects.filter(is_active=True)
    return render(request, "products/list.html", {"products": products})


def product_detail(request, pk: int):
    product = get_object_or_404(InvestmentProduct, pk=pk, is_active=True)

    wallet = None
    if request.user.is_authenticated:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

    return render(request, "products/detail.html", {"product": product, "wallet": wallet})