from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render

from jobs.models import ArquivoFoto, Job

from .forms import FotoUploadForm
from .models import GrupoBracketing, GrupoBracketingFoto, PortalEntrega, Selecao, SelecaoItem
from .thumbnails import gerar_thumbnail
from .watermark import aplicar_marca_dagua


@login_required
def foto_list_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    fotos = list(job.arquivos.all())
    grupos_bracketing = list(job.grupos_bracketing.prefetch_related("fotos", "fotos__arquivo_foto").all())
    fotos_agrupadas_ids = set(
        GrupoBracketingFoto.objects.filter(grupo__job=job)
        .values_list("arquivo_foto_id", flat=True)
    )
    fotos_brutas = [
        {
            "foto": foto,
            "lightbox_index": index,
            "agrupada": foto.pk in fotos_agrupadas_ids,
        }
        for index, foto in enumerate(fotos)
        if foto.tipo == ArquivoFoto.TIPO_BRUTA
    ]
    fotos_editadas = [
        {"foto": foto, "lightbox_index": index}
        for index, foto in enumerate(fotos)
        if foto.tipo == ArquivoFoto.TIPO_EDITADA
    ]
    tem_selecao = hasattr(job, "selecao")
    pode_criar_selecao = (
        bool(fotos_brutas)
        and not tem_selecao
        and job.status == Job.STATUS_EM_PRODUCAO
    )
    return render(request, "deliveries/foto_list.html", {
        "job": job,
        "fotos": fotos,
        "fotos_brutas": fotos_brutas,
        "fotos_editadas": fotos_editadas,
        "grupos_bracketing": grupos_bracketing,
        "fotos_agrupadas_ids": fotos_agrupadas_ids,
        "tem_selecao": tem_selecao,
        "pode_criar_selecao": pode_criar_selecao,
    })


@login_required
def foto_upload_view(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    tipo_url = request.GET.get("tipo")
    tipos_validos = {choice[0] for choice in ArquivoFoto.TIPO_CHOICES}
    tipo_fixo = tipo_url if tipo_url in tipos_validos else None
    tipo_label = dict(ArquivoFoto.TIPO_CHOICES).get(tipo_fixo, "")

    if request.method == "POST":
        post_data = request.POST.copy()
        if tipo_fixo:
            post_data["tipo"] = tipo_fixo
        form = FotoUploadForm(post_data, request.FILES)
        if form.is_valid():
            tipo = form.cleaned_data["tipo"]
            files = request.FILES.getlist("arquivos")
            thumbnails_criados = 0
            for f in files:
                foto = ArquivoFoto.objects.create(job=job, tipo=tipo, arquivo=f)
                if gerar_thumbnail(foto):
                    thumbnails_criados += 1
            messages.success(request, f"{len(files)} foto(s) enviada(s) com sucesso.")
            if thumbnails_criados < len(files):
                messages.warning(
                    request,
                    "Alguns previews nao puderam ser gerados. Para RAW/CR3, confirme se a dependencia rawpy esta instalada.",
                )
            return redirect("deliveries:foto_list", job_pk=job.pk)
    else:
        form = FotoUploadForm(initial={"tipo": tipo_fixo or ArquivoFoto.TIPO_BRUTA})
    return render(request, "deliveries/foto_upload.html", {
        "form": form,
        "job": job,
        "tipo_fixo": tipo_fixo,
        "tipo_label": tipo_label,
    })


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
def bracketing_create_view(request, job_pk):
    if request.method != "POST":
        return redirect("deliveries:foto_list", job_pk=job_pk)
    job = get_object_or_404(Job, pk=job_pk, fotografo=request.user)
    foto_ids = request.POST.getlist("fotos")
    capa_id = request.POST.get("capa")
    nome = request.POST.get("nome", "").strip()

    fotos = list(
        ArquivoFoto.objects.filter(
            pk__in=foto_ids,
            job=job,
            tipo=ArquivoFoto.TIPO_BRUTA,
        ).order_by("uploaded_at", "id")
    )
    foto_ids_validos = {str(f.pk) for f in fotos}
    if len(fotos) < 2:
        messages.error(request, "Selecione pelo menos duas fotos brutas para agrupar.")
        return redirect("deliveries:foto_list", job_pk=job.pk)
    if capa_id not in foto_ids_validos:
        messages.error(request, "Escolha uma capa dentro das fotos selecionadas.")
        return redirect("deliveries:foto_list", job_pk=job.pk)
    fotos_ja_agrupadas = GrupoBracketingFoto.objects.filter(
        grupo__job=job,
        arquivo_foto_id__in=[foto.pk for foto in fotos],
    ).exists()
    if fotos_ja_agrupadas:
        messages.error(request, "Uma das fotos selecionadas ja pertence a outro grupo de bracketing.")
        return redirect("deliveries:foto_list", job_pk=job.pk)

    capa = next(foto for foto in fotos if str(foto.pk) == capa_id)
    grupo = GrupoBracketing.objects.create(job=job, capa=capa, nome=nome)
    GrupoBracketingFoto.objects.bulk_create([
        GrupoBracketingFoto(grupo=grupo, arquivo_foto=foto, ordem=index)
        for index, foto in enumerate(fotos)
    ])
    messages.success(request, f"Grupo de bracketing criado com {len(fotos)} fotos.")
    return redirect("deliveries:foto_list", job_pk=job.pk)


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
    if max_fotos_raw:
        max_fotos = int(max_fotos_raw) if max_fotos_raw.isdigit() and int(max_fotos_raw) > 0 else None
    else:
        max_fotos = job.quantidade_fotos_incluidas

    selecao = Selecao.objects.create(job=job, max_fotos=max_fotos)
    grupos = list(job.grupos_bracketing.prefetch_related("fotos").all())
    fotos_em_grupos = set(
        GrupoBracketingFoto.objects.filter(grupo__job=job)
        .values_list("arquivo_foto_id", flat=True)
    )
    itens = [SelecaoItem(selecao=selecao, grupo=grupo, selecionado=False) for grupo in grupos]
    itens += [
        SelecaoItem(selecao=selecao, arquivo_foto=foto, selecionado=False)
        for foto in fotos
        if foto.pk not in fotos_em_grupos
    ]
    SelecaoItem.objects.bulk_create(itens)

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
        .select_related("arquivo_foto", "grupo", "grupo__capa")
        .filter(models.Q(arquivo_foto__tipo=ArquivoFoto.TIPO_BRUTA) | models.Q(grupo__isnull=False))
        .order_by("id")
    )
    valor_foto_extra = selecao.job.valor_foto_extra
    valor_foto_extra_js = str(valor_foto_extra or 0).replace(",", ".")
    return render(request, "deliveries/public_selecao.html", {
        "selecao": selecao,
        "itens": itens,
        "perfil": perfil,
        "cor_primaria": cor_primaria,
        "valor_foto_extra": valor_foto_extra,
        "valor_foto_extra_js": valor_foto_extra_js,
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
        selecao.itens.filter(id__in=ids_selecionados).update(selecionado=True)
    selecao.concluir()
    fotos_selecionadas = selecao.itens.filter(selecionado=True).count()
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
