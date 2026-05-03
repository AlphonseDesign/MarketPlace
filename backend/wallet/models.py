from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet({self.user.username})"


class WalletTransaction(models.Model):
    TYPE_DEPOSIT = "DEPOSIT"
    TYPE_WITHDRAWAL = "WITHDRAWAL"
    TYPE_INVEST = "INVEST"
    TYPE_PAYOUT = "PAYOUT"
    TYPE_ADJUSTMENT = "ADJUSTMENT"

    TYPE_CHOICES = [
        (TYPE_DEPOSIT, "Dépôt"),
        (TYPE_WITHDRAWAL, "Retrait"),
        (TYPE_INVEST, "Investissement"),
        (TYPE_PAYOUT, "Crédit investissement"),
        (TYPE_ADJUSTMENT, "Ajustement"),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    tx_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # crédit = positif, débit = négatif
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)

    reference = models.CharField(max_length=80, blank=True)
    note = models.CharField(max_length=220, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.wallet.user.username} {self.tx_type} {self.amount}"


class DepositRequest(models.Model):
    METHOD_AIRTEL = "AIRTEL_MONEY"
    METHOD_ORANGE = "ORANGE_MONEY"

    METHOD_CHOICES = [
        (METHOD_AIRTEL, "Airtel Money"),
        (METHOD_ORANGE, "Orange Money"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_APPROVED, "Approuvé"),
        (STATUS_REJECTED, "Rejeté"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deposit_requests")
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    payer_phone = models.CharField(max_length=30, help_text="Numéro du client (Mobile Money)")

    reference = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_deposits",
    )
    admin_note = models.CharField(max_length=220, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"DepositRequest({self.user.username}, {self.amount}, {self.status})"

    @transaction.atomic
    def approve(self, admin_user):
        if self.status != self.STATUS_PENDING:
            return

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=self.user)

        wallet.balance = (wallet.balance or Decimal("0")) + self.amount
        wallet.save(update_fields=["balance", "updated_at"])

        WalletTransaction.objects.create(
            wallet=wallet,
            tx_type=WalletTransaction.TYPE_DEPOSIT,
            amount=self.amount,
            balance_after=wallet.balance,
            reference=self.reference or f"DEP-{self.pk}",
            note="Dépôt approuvé (validation backoffice)",
        )

        self.status = self.STATUS_APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.save(update_fields=["status", "reviewed_at", "reviewed_by"])

    @transaction.atomic
    def reject(self, admin_user, note: str = ""):
        if self.status != self.STATUS_PENDING:
            return
        self.status = self.STATUS_REJECTED
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.admin_note = note[:220]
        self.save(update_fields=["status", "reviewed_at", "reviewed_by", "admin_note"])


class WithdrawalRequest(models.Model):
    METHOD_AIRTEL = "AIRTEL_MONEY"
    METHOD_ORANGE = "ORANGE_MONEY"
    METHOD_SIMULATION = "SIMULATION"  # compatibilité

    METHOD_CHOICES = [
        (METHOD_AIRTEL, "Airtel Money"),
        (METHOD_ORANGE, "Orange Money"),
        (METHOD_SIMULATION, "Simulation"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_APPROVED, "Approuvé"),
        (STATUS_REJECTED, "Rejeté"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="withdrawal_requests")
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    payout_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_SIMULATION)
    payout_account = models.CharField(max_length=80, blank=True)
    reference = models.CharField(max_length=80, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_withdrawals",
    )
    admin_note = models.CharField(max_length=220, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"WithdrawalRequest({self.user.username}, {self.amount}, {self.status})"

    @transaction.atomic
    def approve(self, admin_user):
        if self.status != self.STATUS_PENDING:
            return

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=self.user)

        if (wallet.balance or Decimal("0")) < self.amount:
            self.status = self.STATUS_REJECTED
            self.reviewed_at = timezone.now()
            self.reviewed_by = admin_user
            self.admin_note = "Solde insuffisant au moment de l'approbation."
            self.save(update_fields=["status", "reviewed_at", "reviewed_by", "admin_note"])
            return

        wallet.balance = wallet.balance - self.amount
        wallet.save(update_fields=["balance", "updated_at"])

        WalletTransaction.objects.create(
            wallet=wallet,
            tx_type=WalletTransaction.TYPE_WITHDRAWAL,
            amount=-self.amount,
            balance_after=wallet.balance,
            reference=self.reference or f"WDR-{self.pk}",
            note="Retrait approuvé (validation backoffice)",
        )

        self.status = self.STATUS_APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.save(update_fields=["status", "reviewed_at", "reviewed_by"])

    @transaction.atomic
    def reject(self, admin_user, note: str = ""):
        if self.status != self.STATUS_PENDING:
            return
        self.status = self.STATUS_REJECTED
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.admin_note = note[:220]
        self.save(update_fields=["status", "reviewed_at", "reviewed_by", "admin_note"])