import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from jobs.models import Job

from .forms import AssinaturaForm, ContratoForm, ModeloContratoForm
from .models import Contrato, ModeloContrato


@login_required
def contrato_generate_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    if hasattr(job, "contrato"):
        return redirect("contracts:detail", job_pk=job.pk)
    if job.status not in (Job.STATUS_CONTRATO_PENDENTE, Job.STATUS_ORCAMENTO_APROVADO):
        messages.error(request, "Este job não permite gerar contrato neste momento.")
        return redirect("jobs:detail", pk=job.pk)

    modelos = ModeloContrato.objects.filter(fotografo=request.user)
    variaveis_job = _build_variaveis_job(job)
    modelos_json = json.dumps({str(m.pk): m.conteudo_template for m in modelos})
    variaveis_json = json.dumps(variaveis_job)

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

    return render(request, "contracts/generate.html", {
        "form": form,
        "job": job,
        "modelos": modelos,
        "modelos_json": modelos_json,
        "variaveis_json": variaveis_json,
    })


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


@login_required
def contrato_list_view(request):
    contratos = (
        Contrato.objects.filter(job__fotografo=request.user)
        .select_related("job", "job__cliente")
        .order_by("-created_at")
    )
    return render(request, "contracts/list.html", {"contratos": contratos})


@login_required
def modelo_list_view(request):
    modelos = ModeloContrato.objects.filter(fotografo=request.user)
    return render(request, "contracts/modelo_list.html", {"modelos": modelos})


@login_required
def modelo_create_view(request):
    form = ModeloContratoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        modelo = form.save(commit=False)
        modelo.fotografo = request.user
        modelo.save()
        messages.success(request, "Modelo criado com sucesso.")
        return redirect("contracts:modelo_list")
    return render(request, "contracts/modelo_form.html", {"form": form, "acao": "Novo"})


@login_required
def modelo_update_view(request, pk):
    modelo = get_object_or_404(ModeloContrato, pk=pk, fotografo=request.user)
    form = ModeloContratoForm(request.POST or None, instance=modelo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Modelo atualizado.")
        return redirect("contracts:modelo_list")
    return render(request, "contracts/modelo_form.html", {"form": form, "acao": "Editar", "modelo": modelo})


@login_required
def modelo_delete_view(request, pk):
    modelo = get_object_or_404(ModeloContrato, pk=pk, fotografo=request.user)
    if request.method == "POST":
        modelo.delete()
        messages.success(request, "Modelo excluído.")
        return redirect("contracts:modelo_list")
    return render(request, "contracts/modelo_confirm_delete.html", {"modelo": modelo})


def _build_variaveis_job(job):
    perfil = getattr(job.fotografo, "perfil", None)
    itens = job.orcamento.itens.select_related("servico").all()
    quantidade_fotos = job.quantidade_fotos_incluidas or "nao definido"
    valor_foto_extra = f"R$ {job.valor_foto_extra:.2f}"
    servicos_str = "\n".join([
        f"  • {i.descricao or (i.servico.nome if i.servico else '')}: R$ {i.valor:.2f}"
        for i in itens
    ])
    return {
        "{{nome_cliente}}": job.cliente.nome,
        "{{empresa_cliente}}": job.cliente.empresa or "",
        "{{valor_total}}": f"R$ {job.valor_total:.2f}",
        "{{data_hoje}}": timezone.localdate().strftime("%d/%m/%Y"),
        "{{servicos}}": servicos_str,
        "{{nome_fotografo}}": job.fotografo.email,
        "{{nome_empresa}}": perfil.nome_empresa if perfil else "",
        "{{quantidade_fotos_incluidas}}": str(quantidade_fotos),
        "{{valor_foto_extra}}": valor_foto_extra,
    }


def _build_contrato_conteudo(job):
    itens = job.orcamento.itens.select_related("servico").all()
    linhas = []
    for item in itens:
        nome = item.servico.nome if item.servico else item.descricao
        linhas.append(f"  • {nome}: R$ {item.valor:.2f}")
    itens_str = "\n".join(linhas) if linhas else "  (sem itens)"
    quantidade_fotos = job.quantidade_fotos_incluidas or "nao definido"
    valor_foto_extra = f"R$ {job.valor_foto_extra:.2f}"

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
        f"SELECAO DE FOTOS E EXTRAS:\n"
        f"  Fotos incluidas no pacote: {quantidade_fotos}\n"
        f"  Valor por foto extra: {valor_foto_extra}\n"
        f"  O cliente fara a selecao pelo portal da contratada. Quando houver grupo\n"
        f"  de bracketing, a capa representa todas as fotos internas do grupo e\n"
        f"  contabiliza como uma unica escolha para o limite contratado.\n\n"
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
