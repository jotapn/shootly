from django.contrib import admin

from .models import Pagamento


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "valor", "confirmado_por", "metodo")
    list_filter = ("status", "confirmado_por", "metodo")
