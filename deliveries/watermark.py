import io
import logging
import math

from django.core.files.base import ContentFile
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)


def aplicar_marca_dagua(arquivo_foto, config):
    """
    Aplica marca d'agua no arquivo original ou, para RAWs, no thumbnail gerado.
    Salva o resultado em arquivo_foto.arquivo_protegido.
    """
    foto = _abrir_imagem_base(arquivo_foto)
    if foto is None:
        return False

    try:
        marca = Image.open(config.arquivo_png.path).convert("RGBA")
    except Exception as exc:
        logger.warning(
            "watermark: nao foi possivel abrir marca d'agua pk=%s (%s): %s",
            config.pk,
            config.arquivo_png.name,
            exc,
        )
        return False

    nova_larg = max(1, int(foto.width * config.tamanho_pct / 100))
    nova_alt = max(1, int(marca.height * nova_larg / marca.width))
    marca = marca.resize((nova_larg, nova_alt), Image.Resampling.LANCZOS)

    r, g, b, a = marca.split()
    a = ImageEnhance.Brightness(a).enhance(config.opacidade / 100)
    marca.putalpha(a)

    if config.modo == "grade":
        overlay = _montar_grade(foto.size, marca, config)
    else:
        overlay = _montar_unico(foto.size, marca, config)

    resultado = Image.alpha_composite(foto, overlay).convert("RGB")

    buf = io.BytesIO()
    resultado.save(buf, format="JPEG", quality=90)
    buf.seek(0)

    nome = f"protegido_{arquivo_foto.pk}.jpg"
    arquivo_foto.arquivo_protegido.save(nome, ContentFile(buf.read()), save=True)
    return True


def _abrir_imagem_base(arquivo_foto):
    try:
        return Image.open(arquivo_foto.arquivo.path).convert("RGBA")
    except Exception as exc:
        if arquivo_foto.thumbnail:
            try:
                return Image.open(arquivo_foto.thumbnail.path).convert("RGBA")
            except Exception as thumb_exc:
                logger.warning(
                    "watermark: nao foi possivel abrir thumbnail pk=%s (%s): %s",
                    arquivo_foto.pk,
                    arquivo_foto.thumbnail.name,
                    thumb_exc,
                )
                return None
        logger.warning(
            "watermark: nao foi possivel abrir foto pk=%s (%s): %s",
            arquivo_foto.pk,
            arquivo_foto.arquivo.name,
            exc,
        )
        return None


def _montar_unico(size, marca, config):
    fw, fh = size
    mw, mh = marca.size
    pos_map = {
        "centro": ((fw - mw) // 2, (fh - mh) // 2),
        "superior_esq": (10, 10),
        "superior_dir": (fw - mw - 10, 10),
        "inferior_esq": (10, fh - mh - 10),
        "inferior_dir": (fw - mw - 10, fh - mh - 10),
    }
    pos = pos_map.get(config.posicao, pos_map["inferior_dir"])
    pos = (max(0, pos[0]), max(0, pos[1]))
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay.paste(marca, pos, marca)
    return overlay


def _montar_grade(size, marca, config):
    fw, fh = size
    mw, mh = marca.size
    espacamento_px = max(0, int(fw * config.espacamento_pct / 100))
    step_x = mw + espacamento_px
    step_y = mh + espacamento_px

    diag = int(math.sqrt(fw ** 2 + fh ** 2)) + max(mw, mh) * 2
    canvas = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))

    for y in range(0, diag, step_y):
        for x in range(0, diag, step_x):
            canvas.paste(marca, (x, y), marca)

    if config.rotacao:
        canvas = canvas.rotate(config.rotacao, resample=Image.Resampling.BILINEAR, expand=False)

    left = (canvas.width - fw) // 2
    top = (canvas.height - fh) // 2
    overlay = canvas.crop((left, top, left + fw, top + fh))
    return overlay
