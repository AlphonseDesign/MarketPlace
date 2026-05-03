from django.contrib import admin
from .models import Wallet, WalletTransaction, DepositRequest, WithdrawalRequest


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__username", "user__email")


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "tx_type", "amount", "balance_after", "reference", "created_at")
    list_filter = ("tx_type", "created_at")
    search_fields = ("wallet__user__username", "reference", "note")


# ---- Deposit actions
@admin.action(description="Approuver (crédite le wallet)")
def approve_selected_deposits(modeladmin, request, queryset):
    for dep in queryset:
        dep.approve(request.user)


@admin.action(description="Rejeter")
def reject_selected_deposits(modeladmin, request, queryset):
    for dep in queryset:
        dep.reject(request.user, note="Rejet admin")


@admin.action(description="Remettre en attente (PENDING)")
def reset_deposits_to_pending(modeladmin, request, queryset):
    for dep in queryset:
        dep.status = DepositRequest.STATUS_PENDING
        dep.reviewed_at = None
        dep.reviewed_by = None
        dep.admin_note = ""
        dep.save()


@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "method", "status", "created_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "method", "created_at")
    search_fields = ("user__username", "reference")
    readonly_fields = ("status", "created_at", "reviewed_at", "reviewed_by")
    actions = [approve_selected_deposits, reject_selected_deposits, reset_deposits_to_pending]


# ---- Withdrawal actions
@admin.action(description="Approuver (débite le wallet)")
def approve_selected_withdrawals(modeladmin, request, queryset):
    for w in queryset:
        w.approve(request.user)


@admin.action(description="Rejeter")
def reject_selected_withdrawals(modeladmin, request, queryset):
    for w in queryset:
        w.reject(request.user, note="Rejet admin")


@admin.action(description="Remettre en attente (PENDING)")
def reset_withdrawals_to_pending(modeladmin, request, queryset):
    for w in queryset:
        w.status = WithdrawalRequest.STATUS_PENDING
        w.reviewed_at = None
        w.reviewed_by = None
        w.admin_note = ""
        w.save()


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "payout_method", "status", "created_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "payout_method", "created_at")
    search_fields = ("user__username", "reference", "payout_account")
    readonly_fields = ("status", "created_at", "reviewed_at", "reviewed_by")
    actions = [approve_selected_withdrawals, reject_selected_withdrawals, reset_withdrawals_to_pending]