from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from products.models import InvestmentProduct
from wallet.models import Wallet, DepositRequest, WithdrawalRequest
from investments.models import Investment


def home(request):
    products = InvestmentProduct.objects.filter(is_active=True)[:12]
    return render(request, "dashboard/home.html", {"products": products})


@login_required
def user_dashboard(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    deposits = DepositRequest.objects.filter(user=request.user)[:10]
    withdrawals = WithdrawalRequest.objects.filter(user=request.user)[:10]

    pending_deposits = DepositRequest.objects.filter(
        user=request.user, status=DepositRequest.STATUS_PENDING
    ).count()
    pending_withdrawals = WithdrawalRequest.objects.filter(
        user=request.user, status=WithdrawalRequest.STATUS_PENDING
    ).count()

    transactions = wallet.transactions.all()[:10]
    investments = Investment.objects.filter(user=request.user)[:10]

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "wallet": wallet,
            "deposits": deposits,
            "withdrawals": withdrawals,
            "pending_deposits": pending_deposits,
            "pending_withdrawals": pending_withdrawals,
            "transactions": transactions,
            "investments": investments,
        },
    )