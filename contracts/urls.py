from django.urls import path
from django.views.generic import TemplateView

app_name = "contracts"

urlpatterns = [
    path("jobs/<int:job_pk>/contrato/gerar/", TemplateView.as_view(template_name="placeholder.html"), name="generate"),
    path("jobs/<int:job_pk>/contrato/", TemplateView.as_view(template_name="placeholder.html"), name="detail"),
    path("p/contrato/<uuid:token>/", TemplateView.as_view(template_name="placeholder.html"), name="public_view"),
    path("p/contrato/<uuid:token>/assinar/", TemplateView.as_view(template_name="placeholder.html"), name="public_sign"),
]
