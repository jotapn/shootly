from django.contrib import admin

from .models import Contrato


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "assinatura_data")
    readonly_fields = ("hash_documento", "assinatura_ip", "assinatura_data")
