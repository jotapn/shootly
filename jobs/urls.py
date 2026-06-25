from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("jobs/", views.JobListView.as_view(), name="list"),
    path("jobs/<int:pk>/", views.JobDetailView.as_view(), name="detail"),
    path("jobs/<int:pk>/editar/", views.JobUpdateView.as_view(), name="edit"),
    path("jobs/<int:pk>/status/", views.job_status_update_view, name="status_update"),
    path("jobs/<int:pk>/producao/agendar/", views.job_producao_agendar_view, name="producao_agendar"),
]
