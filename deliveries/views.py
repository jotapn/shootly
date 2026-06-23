from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from jobs.models import ArquivoFoto, Job

from .forms import FotoUploadForm
from .models import PortalEntrega, Selecao, SelecaoItem
from .watermark import aplicar_marca_dagua


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
    fotos = job.arquivos.filter(tipo=ArquivoFoto.TIPO_BRUTA)
    if not fotos.exists():
        messages.error(request, "Faça upload de fotos brutas antes de criar a seleção.")
        return redirect("deliveries:foto_list", job_pk=job.pk)

    max_fotos_raw = request.POST.get("max_fotos", "").strip()
    max_fotos = int(max_fotos_raw) if max_fotos_raw.isdigit() and int(max_fotos_raw) > 0 else None

    selecao = Selecao.objects.create(job=job, max_fotos=max_fotos)
    SelecaoItem.objects.bulk_create([
        SelecaoItem(selecao=selecao, arquivo_foto=foto, selecionado=False)
        for foto in fotos
    ])

    config = getattr(request.user, "marca_dagua", None)
    if config and config.arquivo_png:
        fotos_list = list(fotos)  # materializa para reusar sem novo SQL
        aplicados = sum(1 for f in fotos_list if aplicar_marca_dagua(f, config))
        total = len(fotos_list)
        if aplicados == total:
            messages.info(request, f"Marca d'água aplicada em {aplicados} foto(s).")
        elif aplicados > 0:
            messages.warning(request, f"Marca d'água aplicada em {aplicados} de {total} foto(s). Os demais arquivos podem não ser JPEG/PNG.")
        else:
            messages.warning(request, "Marca d'água configurada mas nenhuma foto foi processada. Verifique se os uploads são JPEG ou PNG.")

    job.status = Job.STATUS_AGUARDANDO_SELECAO
    job.save(update_fields=["status", "updated_at"])
    messages.success(request, "Seleção criada. Compartilhe o link com o cliente.")
    return redirect("jobs:detail", pk=job.pk)


@login_required
def portal_create_view(request, job_pk):
    if request.method != "POST":
        return redirect("jobs:detail", pk=job_pk)
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    if hasattr(job, "portal_entrega"):
        messages.warning(request, "Este job já tem um portal de entrega.")
        return redirect("jobs:detail", pk=job.pk)
    PortalEntrega.objects.create(job=job)
    job.status = Job.STATUS_AGUARDANDO_PAGAMENTO
    job.save(update_fields=["status", "updated_at"])
    messages.success(request, "Portal de entrega criado. Registre o pagamento para liberar.")
    return redirect("jobs:detail", pk=job.pk)


# ---------------------------------------------------------------------------
# Portais públicos (sem autenticação)
# ---------------------------------------------------------------------------

@login_required
def portal_liberar_view(request, job_pk):
    if request.method != "POST":
        return redirect("jobs:detail", pk=job_pk)
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    portal = get_object_or_404(PortalEntrega, job=job)
    if portal.status == PortalEntrega.STATUS_BLOQUEADO:
        portal.status = PortalEntrega.STATUS_LIBERADO
        portal.save(update_fields=["status"])
        job.status = Job.STATUS_ENTREGUE
        job.save(update_fields=["status", "updated_at"])
        messages.success(request, "Portal liberado! O cliente já pode acessar e baixar as fotos.")
    return redirect("jobs:detail", pk=job.pk)


def public_selecao_view(request, token):
    selecao = get_object_or_404(Selecao, link_token=token)
    perfil = getattr(selecao.job.fotografo, "perfil", None)
    cor_primaria = perfil.cor_primaria if perfil else "#1d4ed8"
    # Filtra só BRUTA — garante que fotos editadas não apareçam mesmo em seleções antigas
    itens = (
        selecao.itens
        .select_related("arquivo_foto")
        .filter(arquivo_foto__tipo=ArquivoFoto.TIPO_BRUTA)
    )
    return render(request, "deliveries/public_selecao.html", {
        "selecao": selecao,
        "itens": itens,
        "perfil": perfil,
        "cor_primaria": cor_primaria,
    })


def public_selecao_confirm_view(request, token):
    if request.method != "POST":
        return redirect("deliveries:public_selecao", token=token)
    selecao = get_object_or_404(Selecao, link_token=token)
    perfil = getattr(selecao.job.fotografo, "perfil", None)
    cor_primaria = perfil.cor_primaria if perfil else "#1d4ed8"
    if selecao.status == Selecao.STATUS_CONCLUIDA:
        fotos_selecionadas = selecao.itens.filter(selecionado=True).count()
        return render(request, "deliveries/public_selecao_concluida.html", {
            "selecao": selecao,
            "perfil": perfil,
            "cor_primaria": cor_primaria,
            "fotos_selecionadas": fotos_selecionadas,
        })
    ids_selecionados = set(request.POST.getlist("selecionados"))
    selecao.itens.all().update(selecionado=False)
    if ids_selecionados:
        selecao.itens.filter(arquivo_foto_id__in=ids_selecionados).update(selecionado=True)
    selecao.concluir()
    fotos_selecionadas = len(ids_selecionados)
    return render(request, "deliveries/public_selecao_concluida.html", {
        "selecao": selecao,
        "perfil": perfil,
        "cor_primaria": cor_primaria,
        "fotos_selecionadas": fotos_selecionadas,
    })


def public_portal_view(request, token):
    portal = get_object_or_404(PortalEntrega, link_token=token)
    perfil = getattr(portal.job.fotografo, "perfil", None)
    cor_primaria = perfil.cor_primaria if perfil else "#1d4ed8"
    fotos_editadas = []
    if portal.status == PortalEntrega.STATUS_LIBERADO:
        fotos_editadas = list(portal.job.arquivos.filter(tipo=ArquivoFoto.TIPO_EDITADA))
    return render(request, "deliveries/public_portal.html", {
        "portal": portal,
        "fotos_editadas": fotos_editadas,
        "perfil": perfil,
        "cor_primaria": cor_primaria,
    })
