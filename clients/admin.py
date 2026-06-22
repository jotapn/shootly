from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "fotografo", "email", "created_at")
    search_fields = ("nome", "email", "empresa")
