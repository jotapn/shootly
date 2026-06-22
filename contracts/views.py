from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from jobs.models import Job

from .forms import AssinaturaForm, ContratoForm
from .models import Contrato


@login_required
def contrato_generate_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    if hasattr(job, "contrato"):
        return redirect("contracts:detail", job_pk=job.pk)
    if job.status not in (Job.STATUS_CONTRATO_PENDENTE, Job.STATUS_ORCAMENTO_APROVADO):
        messages.error(request, "Este job não permite gerar contrato neste momento.")
        return redirect("jobs:detail", pk=job.pk)

    if request.method == "POST":
        form = ContratoForm(request.POST)
        if form.is_valid():
            contrato = form.save(commit=False)
            contrato.job = job
            contrato.save()
            if job.status == Job.STATUS_ORCAMENTO_APROVADO:
                job.status = Job.STATUS_CONTRATO_PENDENTE
                job.save(update_fields=["status", "updated_at"])
            messages.success(request, "Contrato gerado. Compartilhe o link com o cliente.")
            return redirect("contracts:detail", job_pk=job.pk)
    else:
        form = ContratoForm(initial={"conteudo": _build_contrato_conteudo(job)})

    return render(request, "contracts/generate.html", {"form": form, "job": job})


@login_required
def contrato_detail_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    contrato = get_object_or_404(Contrato, job=job)
    return render(request, "contracts/detail.html", {"contrato": contrato, "job": job})


def contrato_public_view(request, token):
    contrato = get_object_or_404(Contrato, link_token=token)
    form = AssinaturaForm() if contrato.status == Contrato.STATUS_PENDENTE else None
    return render(request, "contracts/public_view.html", {"contrato": contrato, "form": form})


def contrato_public_sign_view(request, token):
    if request.method != "POST":
        return redirect("contracts:public_view", token=token)
    contrato = get_object_or_404(Contrato, link_token=token)
    if contrato.status == Contrato.STATUS_ASSINADO:
        return render(request, "contracts/public_signed.html", {"contrato": contrato})
    form = AssinaturaForm(request.POST)
    if form.is_valid():
        ip = (
            request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            or request.META.get("REMOTE_ADDR", "")
        )
        contrato.assinar(
            nome=form.cleaned_data["nome"],
            cpf=form.cleaned_data["cpf"],
            ip=ip,
        )
        return render(request, "contracts/public_signed.html", {"contrato": contrato})
    return render(request, "contracts/public_view.html", {"contrato": contrato, "form": form})


def _build_contrato_conteudo(job):
    itens = job.orcamento.itens.select_related("servico").all()
    linhas = []
    for item in itens:
        nome = item.servico.nome if item.servico else item.descricao
        linhas.append(f"  • {nome}: R$ {item.valor:.2f}")
    itens_str = "\n".join(linhas) if linhas else "  (sem itens)"

    data = timezone.localdate().strftime("%d de %B de %Y")
    return (
        f"CONTRATO DE PRESTAÇÃO DE SERVIÇOS FOTOGRÁFICOS\n"
        f"{'=' * 56}\n\n"
        f"PARTES:\n"
        f"  Fotógrafo(a): {job.fotografo.email}\n"
        f"  Cliente:      {job.cliente.nome}\n"
        f"  E-mail:       {job.cliente.email or 'não informado'}\n"
        f"  Empresa:      {job.cliente.empresa or 'não informado'}\n\n"
        f"SERVIÇOS CONTRATADOS:\n"
        f"{itens_str}\n\n"
        f"VALOR TOTAL: R$ {job.valor_total:.2f}\n\n"
        f"CONDIÇÕES GERAIS:\n"
        f"1. O pagamento será realizado conforme combinado entre as partes.\n"
        f"2. As fotografias serão entregues em formato digital.\n"
        f"3. O prazo de entrega será combinado separadamente.\n"
        f"4. Cancelamentos devem ser comunicados com antecedência.\n\n"
        f"PROPRIEDADE E USO DAS IMAGENS:\n"
        f"  As imagens produzidas são de propriedade do(a) fotógrafo(a), sendo\n"
        f"  cedido ao cliente o direito de uso conforme acordado.\n\n"
        f"Data de emissão: {data}\n\n"
        f"Assinatura eletrônica do cliente:\n"
        f"  Nome completo: ___________________________\n"
        f"  CPF:           ___________________________\n"
    )
