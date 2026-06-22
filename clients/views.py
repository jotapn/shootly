from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import FotografoMixin

from .forms import ClienteForm
from .models import Cliente


class ClienteListView(FotografoMixin, ListView):
    model = Cliente
    template_name = "clients/list.html"
    context_object_name = "clientes"


class ClienteCreateView(FotografoMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clients/form.html"
    success_url = reverse_lazy("clients:list")

    def form_valid(self, form):
        form.instance.fotografo = self.request.user
        return super().form_valid(form)


class ClienteDetailView(FotografoMixin, DetailView):
    model = Cliente
    template_name = "clients/detail.html"
    context_object_name = "cliente"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["jobs"] = self.object.jobs.filter(fotografo=self.request.user).order_by("-created_at")
        return ctx


class ClienteUpdateView(FotografoMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clients/form.html"
    success_url = reverse_lazy("clients:list")


class ClienteDeleteView(FotografoMixin, DeleteView):
    model = Cliente
    template_name = "clients/confirm_delete.html"
    success_url = reverse_lazy("clients:list")
