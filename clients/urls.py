from django.urls import path
from django.views.generic import TemplateView

app_name = "clients"

urlpatterns = [
    path("clientes/", TemplateView.as_view(template_name="placeholder.html"), name="list"),
    path("clientes/novo/", TemplateView.as_view(template_name="placeholder.html"), name="create"),
    path("clientes/<int:pk>/", TemplateView.as_view(template_name="placeholder.html"), name="detail"),
    path("clientes/<int:pk>/editar/", TemplateView.as_view(template_name="placeholder.html"), name="edit"),
    path("clientes/<int:pk>/excluir/", TemplateView.as_view(template_name="placeholder.html"), name="delete"),
]
