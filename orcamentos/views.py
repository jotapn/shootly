import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.mixins import FotografoMixin

from .forms import OrcamentoForm, OrcamentoItemForm, OrcamentoItemFormSet, ServicoForm
from .models import Orcamento, OrcamentoItem, Servico

# ---------------------------------------------------------------------------
# Serviços
# ---------------------------------------------------------------------------


class ServicoListView(FotografoMixin, ListView):
    model = Servico
    template_name = "orcamentos/servico_list.html"
    context_object_name = "servicos"


class ServicoCreateView(FotografoMixin, CreateView):
    model = Servico
    form_class = ServicoForm
    template_name = "orcamentos/servico_form.html"
    success_url = reverse_lazy("orcamentos:servico_list")

    def form_valid(self, form):
        form.instance.fotografo = self.request.user
        return super().form_valid(form)


class ServicoUpdateView(FotografoMixin, UpdateView):
    model = Servico
    form_class = ServicoForm
    template_name = "orcamentos/servico_form.html"
    success_url = reverse_lazy("orcamentos:servico_list")


class ServicoDeleteView(FotografoMixin, DeleteView):
    model = Servico
    template_name = "orcamentos/servico_confirm_delete.html"
    success_url = reverse_lazy("orcamentos:servico_list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if request.headers.get("HX-Request"):
            return HttpResponse("")
        return response


# ---------------------------------------------------------------------------
# Orçamentos
# ---------------------------------------------------------------------------


@login_required
def orcamento_list(request):
    orcamentos = (
        Orcamento.objects.filter(fotografo=request.user)
        .select_related("cliente")
        .order_by("-created_at")
    )
    return render(request, "orcamentos/list.html", {"orcamentos": orcamentos})


def _servicos_prices_json(user):
    return json.dumps({
        s.pk: float(s.valor_padrao) if s.valor_padrao is not None else None
        for s in Servico.objects.filter(fotografo=user)
    })


@login_required
def orcamento_create(request):
    if request.method == "POST":
        form = OrcamentoForm(request.POST, fotografo=request.user)
        formset = OrcamentoItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            orcamento = form.save(commit=False)
            orcamento.fotografo = request.user
            orcamento.save()
            itens = formset.save(commit=False)
            for item in itens:
                item.orcamento = orcamento
                item.save()
            for item in formset.deleted_objects:
                item.delete()
            _recalcular_total(orcamento)
            messages.success(request, "Orçamento criado com sucesso.")
            return redirect("orcamentos:detail", pk=orcamento.pk)
    else:
        form = OrcamentoForm(fotografo=request.user)
        formset = OrcamentoItemFormSet()
    return render(request, "orcamentos/form.html", {
        "form": form,
        "formset": formset,
        "object": None,
        "servicos_prices_json": _servicos_prices_json(request.user),
    })


@login_required
def orcamento_detail(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk, fotografo=request.user)
    itens = orcamento.itens.select_related("servico").all()
    return render(request, "orcamentos/detail.html", {"orcamento": orcamento, "itens": itens})


@login_required
def orcamento_edit(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk, fotografo=request.user)
    was_recusado = orcamento.status == Orcamento.STATUS_RECUSADO
    if request.method == "POST":
        form = OrcamentoForm(request.POST, instance=orcamento, fotografo=request.user)
        formset = OrcamentoItemFormSet(request.POST, instance=orcamento)
        if form.is_valid() and formset.is_valid():
            form.save()
            itens = formset.save(commit=False)
            for item in itens:
                item.orcamento = orcamento
                item.save()
            for item in formset.deleted_objects:
                item.delete()
            _recalcular_total(orcamento)
            if was_recusado:
                orcamento.status = Orcamento.STATUS_RASCUNHO
                orcamento.respondido_em = None
                orcamento.save(update_fields=["status", "respondido_em"])
                messages.success(request, "Orçamento atualizado e reaberto como rascunho — pronto para reenvio.")
            else:
                messages.success(request, "Orçamento atualizado.")
            return redirect("orcamentos:detail", pk=orcamento.pk)
    else:
        form = OrcamentoForm(instance=orcamento, fotografo=request.user)
        formset = OrcamentoItemFormSet(instance=orcamento)
    return render(request, "orcamentos/form.html", {
        "form": form,
        "formset": formset,
        "object": orcamento,
        "was_recusado": was_recusado,
        "servicos_prices_json": _servicos_prices_json(request.user),
    })


@login_required
def orcamento_delete(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk, fotografo=request.user)
    if request.method == "POST":
        orcamento.delete()
        messages.success(request, "Orçamento excluído.")
        return redirect("orcamentos:list")
    return render(request, "orcamentos/confirm_delete.html", {"orcamento": orcamento})


@login_required
def orcamento_send(request, pk):
    if request.method != "POST":
        return redirect("orcamentos:detail", pk=pk)
    orcamento = get_object_or_404(Orcamento, pk=pk, fotografo=request.user)
    if orcamento.status == Orcamento.STATUS_RASCUNHO:
        orcamento.status = Orcamento.STATUS_ENVIADO
        orcamento.enviado_em = timezone.now()
        orcamento.save()
        messages.success(request, "Orçamento enviado. Compartilhe o link com o cliente.")
    return redirect("orcamentos:detail", pk=pk)


@login_required
def orcamento_item_empty_form(request):
    """Retorna um fragment HTML com uma linha vazia do formset (HTMX add-row)."""
    total_forms = int(request.GET.get("total_forms", 0))
    form = OrcamentoItemForm(fotografo=request.user, prefix=f"itens-{total_forms}")
    return render(request, "orcamentos/_item_form_row.html", {"form": form, "index": total_forms})


# ---------------------------------------------------------------------------
# Portais públicos (sem autenticação)
# ---------------------------------------------------------------------------


def orcamento_public_view(request, token):
    orcamento = get_object_or_404(Orcamento, link_token=token)
    itens = orcamento.itens.select_related("servico").all()
    return render(request, "orcamentos/public_view.html", {"orcamento": orcamento, "itens": itens})


def orcamento_public_approve(request, token):
    if request.method != "POST":
        return redirect("orcamentos:public_view", token=token)
    orcamento = get_object_or_404(Orcamento, link_token=token)
    if orcamento.status != Orcamento.STATUS_ENVIADO:
        return render(request, "orcamentos/public_responded.html", {"orcamento": orcamento})
    orcamento.aprovar()
    from jobs.models import Job
    Job.objects.create(
        fotografo=orcamento.fotografo,
        cliente=orcamento.cliente,
        orcamento=orcamento,
        titulo=f"Job — {orcamento.cliente.nome}",
        valor_total=orcamento.valor_total,
        status=Job.STATUS_CONTRATO_PENDENTE,
    )
    return render(request, "orcamentos/public_responded.html", {"orcamento": orcamento, "aprovado": True})


def orcamento_public_reject(request, token):
    if request.method != "POST":
        return redirect("orcamentos:public_view", token=token)
    orcamento = get_object_or_404(Orcamento, link_token=token)
    if orcamento.status == Orcamento.STATUS_ENVIADO:
        orcamento.status = Orcamento.STATUS_RECUSADO
        orcamento.respondido_em = timezone.now()
        orcamento.save()
    return render(request, "orcamentos/public_responded.html", {"orcamento": orcamento, "aprovado": False})


# ---------------------------------------------------------------------------
# Helper interno
# ---------------------------------------------------------------------------


def _recalcular_total(orcamento):
    total = sum(item.valor for item in orcamento.itens.all()) or Decimal("0")
    orcamento.valor_total = total
    orcamento.save(update_fields=["valor_total"])
