from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import DepositRequest, WithdrawalRequest, Wallet

MIN_DEPOSIT = Decimal("2300")
MAX_DEPOSIT = Decimal("2300000")

MIN_WITHDRAW = Decimal("12000")
MAX_WITHDRAW = Decimal("200000")


def normalize_phone(raw: str) -> str:
    return (raw or "").strip().replace(" ", "")


@login_required
def deposit_request_create(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        amount_str = (request.POST.get("amount") or "").strip()
        method = (request.POST.get("method") or "").strip()
        payer_phone = normalize_phone(request.POST.get("payer_phone") or "")

        allowed_methods = {DepositRequest.METHOD_AIRTEL, DepositRequest.METHOD_ORANGE}
        if method not in allowed_methods:
            messages.error(request, "Mode de paiement invalide.")
            return redirect("deposit_request_create")

        if len(payer_phone) < 8:
            messages.error(request, "Veuillez entrer un numéro valide.")
            return redirect("deposit_request_create")

        try:
            amount = Decimal(amount_str)
        except Exception:
            messages.error(request, "Montant invalide.")
            return redirect("deposit_request_create")

        if amount < MIN_DEPOSIT:
            messages.error(request, f"Le montant minimum est {MIN_DEPOSIT} FC.")
            return redirect("deposit_request_create")

        if amount > MAX_DEPOSIT:
            messages.error(request, f"Le montant maximum est {MAX_DEPOSIT} FC.")
            return redirect("deposit_request_create")

        pending_count = DepositRequest.objects.filter(
            user=request.user, status=DepositRequest.STATUS_PENDING
        ).count()
        if pending_count >= 5:
            messages.error(request, "Vous avez déjà plusieurs demandes en attente. Merci de patienter.")
            return redirect("deposit_request_create")

        dep = DepositRequest.objects.create(
            user=request.user,
            amount=amount,
            method=method,
            payer_phone=payer_phone,
            reference="",
        )
        dep.reference = f"DEP-{dep.pk}"
        dep.save(update_fields=["reference"])

        return redirect("deposit_request_confirm", pk=dep.pk)

    return render(
        request,
        "wallet/deposit_request.html",
        {"wallet": wallet, "min_deposit": MIN_DEPOSIT, "max_deposit": MAX_DEPOSIT},
    )


@login_required
def deposit_request_confirm(request, pk: int):
    dep = get_object_or_404(DepositRequest, pk=pk, user=request.user)
    full_name = (request.user.get_full_name() or request.user.username).strip()

    pay_number = "0998676693"
    pay_name = "TABARD NTAMUKUNZI ESAIE"

    return render(
        request,
        "wallet/deposit_confirm.html",
        {"deposit": dep, "full_name": full_name, "pay_number": pay_number, "pay_name": pay_name},
    )


@login_required
def withdraw_request_create(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        amount_str = (request.POST.get("amount") or "").strip()
        method = (request.POST.get("method") or "").strip()
        phone = normalize_phone(request.POST.get("phone") or "")

        allowed_methods = {WithdrawalRequest.METHOD_AIRTEL, WithdrawalRequest.METHOD_ORANGE}
        if method not in allowed_methods:
            messages.error(request, "Mode de retrait invalide.")
            return redirect("withdraw_request_create")

        # Préfixes obligatoires
        if method == WithdrawalRequest.METHOD_AIRTEL and not phone.startswith("+2439"):
            messages.error(request, "Pour Airtel Money, le numéro doit commencer par +2439.")
            return redirect("withdraw_request_create")

        if method == WithdrawalRequest.METHOD_ORANGE and not phone.startswith("+2438"):
            messages.error(request, "Pour Orange Money, le numéro doit commencer par +2438.")
            return redirect("withdraw_request_create")

        if len(phone) < 10:
            messages.error(request, "Veuillez entrer un numéro valide.")
            return redirect("withdraw_request_create")

        try:
            amount = Decimal(amount_str)
        except Exception:
            messages.error(request, "Montant invalide.")
            return redirect("withdraw_request_create")

        if amount < MIN_WITHDRAW:
            messages.error(request, f"Le montant minimum de retrait est {MIN_WITHDRAW} FC.")
            return redirect("withdraw_request_create")

        if amount > MAX_WITHDRAW:
            messages.error(request, f"Le montant maximum de retrait est {MAX_WITHDRAW} FC.")
            return redirect("withdraw_request_create")

        if amount > wallet.balance:
            messages.error(request, "Solde insuffisant.")
            return redirect("withdraw_request_create")

        pending_count = WithdrawalRequest.objects.filter(
            user=request.user, status=WithdrawalRequest.STATUS_PENDING
        ).count()
        if pending_count >= 3:
            messages.error(request, "Vous avez déjà des retraits en attente.")
            return redirect("withdraw_request_create")

        w = WithdrawalRequest.objects.create(
            user=request.user,
            amount=amount,
            payout_method=method,
            payout_account=phone,
            reference="",
            status=WithdrawalRequest.STATUS_PENDING,
        )
        w.reference = f"WDR-{w.pk}"
        w.save(update_fields=["reference"])

        return redirect("withdraw_request_confirm", pk=w.pk)

    return render(
        request,
        "wallet/withdraw_request.html",
        {
            "wallet": wallet,
            "min_withdraw": MIN_WITHDRAW,
            "max_withdraw": MAX_WITHDRAW,
        },
    )


@login_required
def withdraw_request_confirm(request, pk: int):
    w = get_object_or_404(WithdrawalRequest, pk=pk, user=request.user)
    full_name = (request.user.get_full_name() or request.user.username).strip()

    return render(
        request,
        "wallet/withdraw_confirm.html",
        {"w": w, "full_name": full_name},
    )