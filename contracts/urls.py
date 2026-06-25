from django.urls import path

from . import views

app_name = "contracts"

urlpatterns = [
    path("jobs/<int:job_pk>/contrato/gerar/", views.contrato_generate_view, name="generate"),
    path("jobs/<int:job_pk>/contrato/", views.contrato_detail_view, name="detail"),
    path("contratos/", views.contrato_list_view, name="list"),
    path("configuracoes/modelos-contrato/", views.modelo_list_view, name="modelo_list"),
    path("configuracoes/modelos-contrato/novo/", views.modelo_create_view, name="modelo_create"),
    path("configuracoes/modelos-contrato/<int:pk>/editar/", views.modelo_update_view, name="modelo_edit"),
    path("configuracoes/modelos-contrato/<int:pk>/excluir/", views.modelo_delete_view, name="modelo_delete"),
    path("p/contrato/<uuid:token>/", views.contrato_public_view, name="public_view"),
    path("p/contrato/<uuid:token>/assinar/", views.contrato_public_sign_view, name="public_sign"),
]
