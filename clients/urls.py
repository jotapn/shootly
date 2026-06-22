from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("clientes/", views.ClienteListView.as_view(), name="list"),
    path("clientes/novo/", views.ClienteCreateView.as_view(), name="create"),
    path("clientes/<int:pk>/", views.ClienteDetailView.as_view(), name="detail"),
    path("clientes/<int:pk>/editar/", views.ClienteUpdateView.as_view(), name="edit"),
    path("clientes/<int:pk>/excluir/", views.ClienteDeleteView.as_view(), name="delete"),
]
