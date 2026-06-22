from django.urls import path
from django.views.generic import TemplateView

app_name = "deliveries"

urlpatterns = [
    path("jobs/<int:job_pk>/fotos/", TemplateView.as_view(template_name="placeholder.html"), name="foto_list"),
    path("jobs/<int:job_pk>/fotos/upload/", TemplateView.as_view(template_name="placeholder.html"), name="foto_upload"),
    path("jobs/<int:job_pk>/selecao/criar/", TemplateView.as_view(template_name="placeholder.html"), name="selecao_create"),
    path("jobs/<int:job_pk>/entrega/criar/", TemplateView.as_view(template_name="placeholder.html"), name="portal_create"),
    path("p/selecao/<uuid:token>/", TemplateView.as_view(template_name="placeholder.html"), name="public_selecao"),
    path("p/entrega/<uuid:token>/", TemplateView.as_view(template_name="placeholder.html"), name="public_portal"),
]
