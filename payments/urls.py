from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("jobs/<int:job_pk>/pagamento/", views.pagamento_detail_view, name="detail"),
    path("jobs/<int:job_pk>/pagamento/criar/", views.pagamento_create_view, name="create"),
    path("jobs/<int:job_pk>/pagamento/confirmar/", views.pagamento_confirm_manual_view, name="confirm_manual"),
    path("webhooks/asaas/", views.webhook_asaas_view, name="webhook_asaas"),
]
