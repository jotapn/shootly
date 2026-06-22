from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from jobs.models import ArquivoFoto, Job

from .forms import FotoUploadForm
from .models import PortalEntrega, Selecao, SelecaoItem


@login_required
def foto_list_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    fotos = job.arquivos.all()
    tem_selecao = hasattr(job, "selecao")
    pode_criar_selecao = (
        fotos.exists()
        and not tem_selecao
        and job.status == Job.STATUS_EM_PRODUCAO
    )
    return render(request, "deliveries/foto_list.html", {
        "job": job,
        "fotos": fotos,
        "tem_selecao": tem_selecao,
        "pode_criar_selecao": pode_criar_selecao,
    })


@login_required
def foto_upload_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    if request.method == "POST":
        form = FotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            tipo = form.cleaned_data["tipo"]
            files = request.FILES.getlist("arquivos")
            for f in files:
                ArquivoFoto.objects.create(job=job, tipo=tipo, arquivo=f)
            messages.success(request, f"{len(files)} foto(s) enviada(s) com sucesso.")
            return redirect("deliveries:foto_list", job_pk=job.pk)
    else:
        form = FotoUploadForm()
    return render(request, "deliveries/foto_upload.html", {"form": form, "job": job})


@login_required
def foto_delete_view(request, foto_pk):
    foto = get_object_or_404(ArquivoFoto, pk=foto_pk, job__fotografo=request.user)
    if request.method != "POST":
        return redirect("deliveries:foto_list", job_pk=foto.job_id)
    job_pk = foto.job_id
    foto.arquivo.delete(save=False)
    foto.delete()
    if request.headers.get("HX-Request"):
        return redirect("deliveries:foto_list", job_pk=job_pk)
    messages.success(request, "Foto removida.")
    return redirect("deliveries:foto_list", job_pk=job_pk)


@login_required
def selecao_create_view(request, job_pk):
    if request.method != "POST":
        return redirect("jobs:detail", pk=job_pk)
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    if hasattr(job, "selecao"):
        messages.warning(request, "Este job já tem uma seleção em andamento.")
        return redirect("jobs:detail", pk=job.pk)
    fotos = job.arquivos.all()
    if not fotos.exists():
        messages.error(request, "Faça upload de fotos antes de criar a seleção.")
        return redirect("deliveries:foto_list", job_pk=job.pk)
    selecao = Selecao.objects.create(job=job)
    SelecaoItem.objects.bulk_create([
        SelecaoItem(selecao=selecao, arquivo_foto=foto, selecionado=False)
        for foto in fotos
    ])
    job.status = Job.STATUS_AGUARDANDO_SELECAO
    job.save(update_fields=["status", "updated_at"])
    messages.success(request, "Seleção criada. Compartilhe o link com o cliente.")
    return redirect("jobs:detail", pk=job.pk)


@login_required
def portal_create_view(request, job_pk):
    if request.method != "POST":
        return redirect("jobs:detail", pk=job_pk)
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    if hasattr(job, "portalentrega"):
        messages.warning(request, "Este job já tem um portal de entrega.")
        return redirect("jobs:detail", pk=job.pk)
    PortalEntrega.objects.create(job=job)
    job.status = Job.STATUS_AGUARDANDO_PAGAMENTO
    job.save(update_fields=["status", "updated_at"])
    messages.success(request, "Portal de entrega criado. Registre o pagamento para liberar.")
    return redirect("jobs:detail", pk=job.pk)


# ---------------------------------------------------------------------------
# Portais públicos (sem autenticação) — placeholders para Fase 5
# ---------------------------------------------------------------------------

def public_selecao_view(request, token):
    selecao = get_object_or_404(Selecao, link_token=token)
    return render(request, "deliveries/public_selecao.html", {"selecao": selecao})


def public_portal_view(request, token):
    portal = get_object_or_404(PortalEntrega, link_token=token)
    return render(request, "deliveries/public_portal.html", {"portal": portal})
