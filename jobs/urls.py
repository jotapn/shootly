from django.urls import path
from django.views.generic import TemplateView

app_name = "jobs"

urlpatterns = [
    path("jobs/", TemplateView.as_view(template_name="placeholder.html"), name="list"),
    path("jobs/<int:pk>/", TemplateView.as_view(template_name="placeholder.html"), name="detail"),
    path("jobs/<int:pk>/editar/", TemplateView.as_view(template_name="placeholder.html"), name="edit"),
]
