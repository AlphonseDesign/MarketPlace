from django.contrib import admin
from .models import Investment


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "principal_cdf", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "product__name")