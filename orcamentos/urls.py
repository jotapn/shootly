from django.urls import path
from django.views.generic import TemplateView

app_name = "orcamentos"

urlpatterns = [
    path("servicos/", TemplateView.as_view(template_name="placeholder.html"), name="servico_list"),
    path("servicos/novo/", TemplateView.as_view(template_name="placeholder.html"), name="servico_create"),
    path("servicos/<int:pk>/editar/", TemplateView.as_view(template_name="placeholder.html"), name="servico_edit"),
    path("servicos/<int:pk>/excluir/", TemplateView.as_view(template_name="placeholder.html"), name="servico_delete"),
    path("orcamentos/", TemplateView.as_view(template_name="placeholder.html"), name="list"),
    path("orcamentos/novo/", TemplateView.as_view(template_name="placeholder.html"), name="create"),
    path("orcamentos/<int:pk>/", TemplateView.as_view(template_name="placeholder.html"), name="detail"),
    path("orcamentos/<int:pk>/editar/", TemplateView.as_view(template_name="placeholder.html"), name="edit"),
    path("orcamentos/<int:pk>/excluir/", TemplateView.as_view(template_name="placeholder.html"), name="delete"),
    path("orcamentos/<int:pk>/enviar/", TemplateView.as_view(template_name="placeholder.html"), name="send"),
    path("p/orcamento/<uuid:token>/", TemplateView.as_view(template_name="placeholder.html"), name="public_view"),
    path("p/orcamento/<uuid:token>/aprovar/", TemplateView.as_view(template_name="placeholder.html"), name="public_approve"),
    path("p/orcamento/<uuid:token>/recusar/", TemplateView.as_view(template_name="placeholder.html"), name="public_reject"),
]
