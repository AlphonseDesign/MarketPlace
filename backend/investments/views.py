from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from products.models import InvestmentProduct
from .models import Investment


@login_required
def invest_in_product(request, product_id: int):
    if request.method != "POST":
        return redirect("product_detail", pk=product_id)

    product = get_object_or_404(InvestmentProduct, pk=product_id, is_active=True)

    amount_str = (request.POST.get("amount") or "").strip()
    try:
        amount = Decimal(amount_str)
    except Exception:
        messages.error(request, "Montant invalide.")
        return redirect("product_detail", pk=product_id)

    try:
        Investment.create_investment(request.user, product, amount)
        messages.success(request, "Investissement effectué avec succès.")
        return redirect("user_dashboard")
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("product_detail", pk=product_id)