from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from products.models import InvestmentProduct
from wallet.models import Wallet, WalletTransaction


class Investment(models.Model):
    STATUS_ACTIVE = "ACTIVE"
    STATUS_CLOSED = "CLOSED"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Actif"),
        (STATUS_CLOSED, "Clôturé"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="investments")
    product = models.ForeignKey(InvestmentProduct, on_delete=models.PROTECT, related_name="investments")

    principal_cdf = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    duration_days_snapshot = models.PositiveIntegerField(default=30)
    expected_end_at = models.DateTimeField(null=True, blank=True)

    # Auto-credit (traçabilité)
    credited_at = models.DateTimeField(null=True, blank=True)
    payout_amount_cdf = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    payout_factor_snapshot = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Investment({self.user.username} -> {self.product.name})"

    def get_expected_end_at(self):
        if self.expected_end_at:
            return self.expected_end_at
        if self.created_at:
            return self.created_at + timedelta(days=int(self.duration_days_snapshot or 0))
        return None

    @property
    def current_value_cdf(self):
        factor = self.product.performance_factor or Decimal("1.00")
        return (self.principal_cdf or Decimal("0")) * factor

    @property
    def pnl_cdf(self):
        return self.current_value_cdf - (self.principal_cdf or Decimal("0"))

    @property
    def is_credited(self):
        return self.credited_at is not None

    @classmethod
    @transaction.atomic
    def create_investment(cls, user, product: InvestmentProduct, amount: Decimal):
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)

        if amount <= 0:
            raise ValueError("Montant invalide")
        if not product.is_active:
            raise ValueError("Produit indisponible")
        if amount < product.min_investment_cdf:
            raise ValueError("Montant inférieur au minimum requis")
        if wallet.balance < amount:
            raise ValueError("Solde insuffisant")

        wallet.balance = wallet.balance - amount
        wallet.save(update_fields=["balance", "updated_at"])

        WalletTransaction.objects.create(
            wallet=wallet,
            tx_type=WalletTransaction.TYPE_INVEST,
            amount=-amount,
            balance_after=wallet.balance,
            reference=f"INV-{user.id}-{product.id}-{int(timezone.now().timestamp())}",
            note=f"Investissement dans {product.name}",
        )

        now = timezone.now()
        duration_days = int(product.duration_days or 0)
        expected_end = now + timedelta(days=duration_days)

        inv = cls.objects.create(
            user=user,
            product=product,
            principal_cdf=amount,
            status=cls.STATUS_ACTIVE,
            duration_days_snapshot=duration_days,
            expected_end_at=expected_end,
        )
        return inv

    @transaction.atomic
    def try_auto_credit(self):
        """
        Si l'investissement est arrivé à terme, crédite automatiquement le wallet
        (1 seule fois) et clôture l'investissement.
        """
        inv = (
            Investment.objects.select_for_update()
            .select_related("product")
            .get(pk=self.pk)
        )

        if inv.credited_at is not None:
            return False  # déjà crédité

        end_at = inv.get_expected_end_at()
        if not end_at:
            return False

        now = timezone.now()
        if now < end_at:
            return False  # pas encore terminé

        # Montant crédité = valeur au moment de la clôture (non garanti, peut être < principal)
        factor = inv.product.performance_factor or Decimal("1.00")
        payout = (inv.principal_cdf or Decimal("0")) * factor
        if payout < 0:
            payout = Decimal("0")

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=inv.user)

        wallet.balance = (wallet.balance or Decimal("0")) + payout
        wallet.save(update_fields=["balance", "updated_at"])

        WalletTransaction.objects.create(
            wallet=wallet,
            tx_type=WalletTransaction.TYPE_PAYOUT,
            amount=payout,
            balance_after=wallet.balance,
            reference=f"INV-PAYOUT-{inv.id}",
            note=f"Crédit auto: investissement terminé ({inv.product.name})",
        )

        inv.status = Investment.STATUS_CLOSED
        inv.closed_at = now
        inv.credited_at = now
        inv.payout_amount_cdf = payout
        inv.payout_factor_snapshot = factor
        inv.expected_end_at = end_at  # s’assure qu'il reste enregistré
        inv.save(update_fields=[
            "status", "closed_at", "credited_at",
            "payout_amount_cdf", "payout_factor_snapshot",
            "expected_end_at"
        ])

        return True