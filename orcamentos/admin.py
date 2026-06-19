from django.contrib import admin

from .models import Orcamento, OrcamentoItem, Servico


class OrcamentoItemInline(admin.TabularInline):
    model = OrcamentoItem
    extra = 1


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "fotografo", "valor_padrao")


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "valor_total", "created_at")
    list_filter = ("status",)
    inlines = [OrcamentoItemInline]
