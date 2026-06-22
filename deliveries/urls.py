from django.urls import path

from . import views

app_name = "deliveries"

urlpatterns = [
    path("jobs/<int:job_pk>/fotos/", views.foto_list_view, name="foto_list"),
    path("jobs/<int:job_pk>/fotos/upload/", views.foto_upload_view, name="foto_upload"),
    path("fotos/<int:foto_pk>/delete/", views.foto_delete_view, name="foto_delete"),
    path("jobs/<int:job_pk>/selecao/criar/", views.selecao_create_view, name="selecao_create"),
    path("jobs/<int:job_pk>/entrega/criar/", views.portal_create_view, name="portal_create"),
    path("p/selecao/<uuid:token>/", views.public_selecao_view, name="public_selecao"),
    path("p/entrega/<uuid:token>/", views.public_portal_view, name="public_portal"),
]
