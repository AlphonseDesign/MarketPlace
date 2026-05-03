from django.contrib import admin
from django.utils.html import format_html
from .models import InvestmentProduct


@admin.register(InvestmentProduct)
class InvestmentProductAdmin(admin.ModelAdmin):
    list_display = (
        "thumb",
        "name",
        "min_investment_cdf",
        "estimated_gain_cdf",
        "duration_days",
        "note",
        "performance_factor",
        "is_active",
        "created_at",
    )
    list_filter = ("note", "is_active", "created_at")
    search_fields = ("name", "description")

    fields = (
        "name",
        "image",
        "description",
        "min_investment_cdf",
        "estimated_gain_cdf",
        "duration_days",
        "note",
        "performance_factor",
        "is_active",
    )

    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:72px;height:48px;object-fit:cover;border-radius:10px;border:1px solid #e5e7eb;" />',
                obj.image.url,
            )
        return "—"

    thumb.short_description = "Photo"