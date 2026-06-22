from django.contrib import admin

from .models import PortalEntrega, Selecao, SelecaoItem


class SelecaoItemInline(admin.TabularInline):
    model = SelecaoItem
    extra = 0


@admin.register(Selecao)
class SelecaoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "concluida_em")
    inlines = [SelecaoItemInline]


@admin.register(PortalEntrega)
class PortalEntregaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "created_at")
