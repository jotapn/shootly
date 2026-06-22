from django.urls import path
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

app_name = "payments"


class WebhookPlaceholder(TemplateView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


urlpatterns = [
    path("jobs/<int:job_pk>/pagamento/", TemplateView.as_view(template_name="placeholder.html"), name="detail"),
    path("jobs/<int:job_pk>/pagamento/criar/", TemplateView.as_view(template_name="placeholder.html"), name="create"),
    path("jobs/<int:job_pk>/pagamento/confirmar/", TemplateView.as_view(template_name="placeholder.html"), name="confirm_manual"),
    path("webhooks/asaas/", WebhookPlaceholder.as_view(template_name="placeholder.html"), name="webhook_asaas"),
]
