from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from jobs.models import Job

from .forms import PagamentoConfirmForm, PagamentoCreateForm
from .models import Pagamento


@login_required
def pagamento_detail_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    pagamento = getattr(job, "pagamento", None)
    if pagamento is None:
        return redirect("payments:create", job_pk=job.pk)
    form = PagamentoConfirmForm() if pagamento.status == Pagamento.STATUS_PENDENTE else None
    return render(request, "payments/detail.html", {"job": job, "pagamento": pagamento, "form": form})


@login_required
def pagamento_create_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    if hasattr(job, "pagamento"):
        return redirect("payments:detail", job_pk=job.pk)
    if request.method == "POST":
        form = PagamentoCreateForm(request.POST)
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.job = job
            pagamento.save()
            messages.success(request, "Pagamento registrado. Confirme quando receber.")
            return redirect("payments:detail", job_pk=job.pk)
    else:
        form = PagamentoCreateForm(initial={"valor": job.valor_total})
    return render(request, "payments/create.html", {"form": form, "job": job})


@login_required
@require_POST
def pagamento_confirm_manual_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    pagamento = get_object_or_404(Pagamento, job=job)
    if pagamento.status == Pagamento.STATUS_CONFIRMADO:
        messages.info(request, "Pagamento já confirmado.")
        return redirect("payments:detail", job_pk=job.pk)
    form = PagamentoConfirmForm(request.POST)
    if form.is_valid():
        pagamento.confirmar(
            origem=Pagamento.CONFIRMADO_MANUAL,
            metodo=form.cleaned_data["metodo"],
            provider_payment_id=form.cleaned_data.get("provider_payment_id", ""),
        )
        messages.success(request, "Pagamento confirmado. Portal de entrega liberado.")
        return redirect("jobs:detail", pk=job.pk)
    return redirect("payments:detail", job_pk=job.pk)


@csrf_exempt
def webhook_asaas_view(request):
    # Placeholder — validação de assinatura entra na Fase 8
    return JsonResponse({"status": "ok"})
