from collections import defaultdict

from django import forms as django_forms
from django.contrib.auth.decorators import login_required
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
        ctx["tem_portal"] = hasattr(job, "portalentrega")
        ctx["tem_pagamento"] = hasattr(job, "pagamento")
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
    return redirect("jobs:list")
