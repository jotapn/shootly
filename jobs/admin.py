from django.contrib import admin

from .models import ArquivoFoto, Job


class ArquivoFotoInline(admin.TabularInline):
    model = ArquivoFoto
    extra = 0


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("__str__", "fotografo", "cliente", "status", "valor_total")
    list_filter = ("status",)
    inlines = [ArquivoFotoInline]
