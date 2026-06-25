from collections import defaultdict

from django import forms as django_forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from core.mixins import FotografoMixin

from .models import Job


class JobTituloForm(django_forms.ModelForm):
    class Meta:
        model = Job
        fields = ["titulo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["titulo"].widget.attrs.update({
            "class": (
                "block w-full rounded-md border border-slate-300 px-3 py-2 "
                "text-sm outline-none ring-blue-400 focus:ring"
            )
        })


class JobProducaoForm(django_forms.ModelForm):
    class Meta:
        model = Job
        fields = ["data_producao"]
        widgets = {
            "data_producao": django_forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": (
                        "rounded-md border border-slate-300 px-3 py-2 text-sm "
                        "outline-none ring-blue-400 focus:ring"
                    ),
                },
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_producao"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["data_producao"].label = "Data da producao"


class JobListView(FotografoMixin, ListView):
    model = Job
    template_name = "jobs/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        jobs = self.get_queryset().select_related("cliente", "orcamento")
        kanban_map = defaultdict(list)
        for job in jobs:
            kanban_map[job.status].append(job)
        ctx["kanban"] = [
            {"status": s, "label": l, "jobs": kanban_map[s]}
            for s, l in Job.STATUS_CHOICES
        ]
        return ctx


class JobDetailView(FotografoMixin, DetailView):
    model = Job
    template_name = "jobs/detail.html"
    context_object_name = "job"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job = self.object
        ctx["tem_contrato"] = hasattr(job, "contrato")
        ctx["tem_selecao"] = hasattr(job, "selecao")
        ctx["tem_portal"] = hasattr(job, "portal_entrega")
        ctx["portal"] = job.portal_entrega if hasattr(job, "portal_entrega") else None
        ctx["tem_pagamento"] = hasattr(job, "pagamento")
        ctx["producao_form"] = JobProducaoForm(instance=job)
        return ctx


class JobUpdateView(FotografoMixin, UpdateView):
    model = Job
    form_class = JobTituloForm
    template_name = "jobs/edit.html"

    def get_success_url(self):
        return reverse_lazy("jobs:detail", kwargs={"pk": self.object.pk})


MANUAL_TRANSITIONS = {
    Job.STATUS_CONTRATO_ASSINADO: Job.STATUS_EM_PRODUCAO,
    Job.STATUS_SELECAO_CONCLUIDA: Job.STATUS_EM_EDICAO,
    Job.STATUS_ENTREGUE: Job.STATUS_CONCLUIDO,
}


@login_required
def job_status_update_view(request, pk):
    if request.method != "POST":
        return redirect("jobs:list")
    job = get_object_or_404(Job, pk=pk, fotografo=request.user)
    new_status = request.POST.get("new_status")
    if MANUAL_TRANSITIONS.get(job.status) == new_status:
        job.status = new_status
        job.save(update_fields=["status", "updated_at"])
    if request.headers.get("HX-Request"):
        return render(request, "jobs/_job_card.html", {"job": job})
    next_url = request.POST.get("next", "")
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("jobs:detail", pk=job.pk)


@login_required
def job_producao_agendar_view(request, pk):
    job = get_object_or_404(Job, pk=pk, fotografo=request.user)
    if request.method != "POST":
        return redirect("jobs:detail", pk=job.pk)
    if job.status not in (Job.STATUS_CONTRATO_ASSINADO, Job.STATUS_EM_PRODUCAO):
        messages.error(request, "A producao so pode ser agendada depois do contrato assinado.")
        return redirect("jobs:detail", pk=job.pk)
    form = JobProducaoForm(request.POST, instance=job)
    if form.is_valid():
        form.save()
        messages.success(request, "Producao agendada.")
    else:
        messages.error(request, "Nao foi possivel salvar a data de producao.")
    return redirect("jobs:detail", pk=job.pk)
