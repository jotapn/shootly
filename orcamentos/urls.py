from django.urls import path

from . import views

app_name = "orcamentos"

urlpatterns = [
    # Serviços
    path("servicos/", views.ServicoListView.as_view(), name="servico_list"),
    path("servicos/novo/", views.ServicoCreateView.as_view(), name="servico_create"),
    path("servicos/<int:pk>/editar/", views.ServicoUpdateView.as_view(), name="servico_edit"),
    path("servicos/<int:pk>/excluir/", views.ServicoDeleteView.as_view(), name="servico_delete"),
    # Orçamentos — painel
    path("orcamentos/", views.orcamento_list, name="list"),
    path("orcamentos/novo/", views.orcamento_create, name="create"),
    path("orcamentos/item-form/", views.orcamento_item_empty_form, name="item_form"),
    path("orcamentos/<int:pk>/", views.orcamento_detail, name="detail"),
    path("orcamentos/<int:pk>/editar/", views.orcamento_edit, name="edit"),
    path("orcamentos/<int:pk>/excluir/", views.orcamento_delete, name="delete"),
    path("orcamentos/<int:pk>/enviar/", views.orcamento_send, name="send"),
    # Portais públicos
    path("p/orcamento/<uuid:token>/", views.orcamento_public_view, name="public_view"),
    path("p/orcamento/<uuid:token>/aprovar/", views.orcamento_public_approve, name="public_approve"),
    path("p/orcamento/<uuid:token>/recusar/", views.orcamento_public_reject, name="public_reject"),
]
