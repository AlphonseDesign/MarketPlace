from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import logout as auth_logout
from django.db.models import Sum

from django.shortcuts import get_object_or_404, redirect, render

from investments.models import Investment
from products.models import InvestmentProduct
from wallet.models import Wallet, WalletTransaction, DepositRequest, WithdrawalRequest

from .forms import (
    BOLoginForm,
    InvestmentProductForm,
    AdminUserCreateForm,
    AdminUserUpdateForm,
    AdminUserSetPasswordForm,
)

User = get_user_model()


def staff_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url="bo_login",
    )(view_func)


def superuser_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url="bo_login",
    )(view_func)


def bo_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("bo_dashboard")

    form = BOLoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if not user.is_staff:
            messages.error(request, "Accès refusé : ce compte n’est pas administrateur.")
            return redirect("bo_login")
        login(request, user)
        return redirect("bo_dashboard")

    return render(request, "backoffice/login.html", {"form": form})


@staff_required
def bo_logout(request):
    auth_logout(request)
    return redirect("bo_login")


@staff_required
def dashboard(request):
    total_users = User.objects.count()
    total_wallet_balance = Wallet.objects.aggregate(s=Sum("balance"))["s"] or 0

    pending_deposits = DepositRequest.objects.filter(status=DepositRequest.STATUS_PENDING).count()
    pending_withdrawals = WithdrawalRequest.objects.filter(status=WithdrawalRequest.STATUS_PENDING).count()

    total_products = InvestmentProduct.objects.count()
    active_products = InvestmentProduct.objects.filter(is_active=True).count()

    inv_total = Investment.objects.aggregate(s=Sum("principal_cdf"))["s"] or 0
    inv_active = Investment.objects.filter(status=Investment.STATUS_ACTIVE).count()
    inv_closed = Investment.objects.filter(status=Investment.STATUS_CLOSED).count()

    return render(request, "backoffice/dashboard.html", {
        "total_users": total_users,
        "total_wallet_balance": total_wallet_balance,
        "pending_deposits": pending_deposits,
        "pending_withdrawals": pending_withdrawals,
        "total_products": total_products,
        "active_products": active_products,
        "inv_total": inv_total,
        "inv_active": inv_active,
        "inv_closed": inv_closed,
    })


# ---------- Produits ----------
@staff_required
def products_list(request):
    products = InvestmentProduct.objects.all()
    return render(request, "backoffice/products_list.html", {"products": products})


@staff_required
def product_create(request):
    if request.method == "POST":
        form = InvestmentProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit créé avec succès.")
            return redirect("bo_products_list")
    else:
        form = InvestmentProductForm()
    return render(request, "backoffice/product_form.html", {"form": form, "title": "Nouveau produit"})


@staff_required
def product_edit(request, pk: int):
    product = get_object_or_404(InvestmentProduct, pk=pk)
    if request.method == "POST":
        form = InvestmentProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit mis à jour.")
            return redirect("bo_products_list")
    else:
        form = InvestmentProductForm(instance=product)
    return render(request, "backoffice/product_form.html", {"form": form, "title": "Modifier produit"})


# ---------- Dépôts ----------
@staff_required
def deposits_list(request):
    deposits = DepositRequest.objects.all()
    return render(request, "backoffice/deposits_list.html", {"deposits": deposits})


@staff_required
def deposit_approve(request, pk: int):
    if request.method != "POST":
        return redirect("bo_deposits_list")
    dep = get_object_or_404(DepositRequest, pk=pk)
    dep.approve(request.user)
    messages.success(request, "Dépôt approuvé et crédité sur le wallet.")
    return redirect("bo_deposits_list")


@staff_required
def deposit_reject(request, pk: int):
    if request.method != "POST":
        return redirect("bo_deposits_list")
    dep = get_object_or_404(DepositRequest, pk=pk)
    dep.reject(request.user, note="Rejet backoffice")
    messages.warning(request, "Dépôt rejeté.")
    return redirect("bo_deposits_list")


# ---------- Retraits ----------
@staff_required
def withdrawals_list(request):
    withdrawals = WithdrawalRequest.objects.all()
    return render(request, "backoffice/withdrawals_list.html", {"withdrawals": withdrawals})


@staff_required
def withdraw_approve(request, pk: int):
    if request.method != "POST":
        return redirect("bo_withdrawals_list")
    w = get_object_or_404(WithdrawalRequest, pk=pk)
    w.approve(request.user)
    messages.success(request, "Retrait approuvé et débité du wallet.")
    return redirect("bo_withdrawals_list")


@staff_required
def withdraw_reject(request, pk: int):
    if request.method != "POST":
        return redirect("bo_withdrawals_list")
    w = get_object_or_404(WithdrawalRequest, pk=pk)
    w.reject(request.user, note="Rejet backoffice")
    messages.warning(request, "Retrait rejeté.")
    return redirect("bo_withdrawals_list")


# ---------- Utilisateurs ----------
@staff_required
def users_list(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "backoffice/users_list.html", {"users": users})


@superuser_required
def user_create(request):
    if request.method == "POST":
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur créé.")
            return redirect("bo_users_list")
    else:
        form = AdminUserCreateForm()
    return render(request, "backoffice/user_form.html", {"form": form, "title": "Créer un utilisateur"})


@superuser_required
def user_edit(request, user_id: int):
    u = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = AdminUserUpdateForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur mis à jour.")
            return redirect("bo_users_list")
    else:
        form = AdminUserUpdateForm(instance=u)
    return render(request, "backoffice/user_form.html", {"form": form, "title": "Modifier utilisateur"})


@superuser_required
def user_set_password(request, user_id: int):
    u = get_object_or_404(User, pk=user_id)
    form = AdminUserSetPasswordForm(u, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Mot de passe changé.")
        return redirect("bo_users_list")
    return render(request, "backoffice/user_password.html", {"form": form, "u": u})


# ---------- Wallets / Transactions ----------
@staff_required
def wallets_list(request):
    wallets = Wallet.objects.select_related("user").order_by("-updated_at")
    return render(request, "backoffice/wallets_list.html", {"wallets": wallets})


@staff_required
def wallet_detail(request, user_id: int):
    wallet = get_object_or_404(Wallet.objects.select_related("user"), user_id=user_id)
    tx = wallet.transactions.all()[:50]
    return render(request, "backoffice/wallet_detail.html", {"wallet": wallet, "transactions": tx})


# ---------- Investissements ----------
@staff_required
def investments_list(request):
    investments = Investment.objects.select_related("user", "product").all()
    return render(request, "backoffice/investments_list.html", {"investments": investments})