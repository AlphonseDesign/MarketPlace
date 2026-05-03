from django.db import models


class InvestmentProduct(models.Model):
    NOTE_TRUSTED = "TRUSTED"
    NOTE_MAYBE = "MAYBE"
    NOTE_POPULAR = "POPULAR"

    NOTE_CHOICES = [
        (NOTE_TRUSTED, "Fiable"),
        (NOTE_MAYBE, "Pas vraiment"),
        (NOTE_POPULAR, "Populaire"),
    ]

    name = models.CharField(max_length=140)

    # Option 1 (recommandée pour hébergement): lien internet
    image_url = models.URLField(
        blank=True,
        help_text="Lien direct https://... (ex: .jpg, .png). Prioritaire si rempli."
    )

    # Option 2 (facultative): upload local
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    description = models.TextField()

    min_investment_cdf = models.DecimalField(max_digits=14, decimal_places=2, help_text="Montant minimum en FC")
    estimated_gain_cdf = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Gain estimé en FC (NON GARANTI). Ne pas présenter comme une promesse.",
    )

    duration_days = models.PositiveIntegerField(help_text="Durée estimée en jours")
    note = models.CharField(max_length=10, choices=NOTE_CHOICES, default=NOTE_POPULAR)

    performance_factor = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=1.00,
        help_text="Indice de performance (non garanti). Ex: 1.05, 0.97",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name