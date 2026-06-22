from django.urls import path

from . import views

app_name = "contracts"

urlpatterns = [
    path("jobs/<int:job_pk>/contrato/gerar/", views.contrato_generate_view, name="generate"),
    path("jobs/<int:job_pk>/contrato/", views.contrato_detail_view, name="detail"),
    path("p/contrato/<uuid:token>/", views.contrato_public_view, name="public_view"),
    path("p/contrato/<uuid:token>/assinar/", views.contrato_public_sign_view, name="public_sign"),
]
