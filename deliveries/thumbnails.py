import io
import logging
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

RAW_EXTENSIONS = {
    ".raw", ".dng", ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".srf", ".sr2",
    ".raf", ".orf", ".rw2", ".pef", ".ptx", ".srw", ".rwl", ".x3f", ".3fr",
}


def gerar_thumbnail(arquivo_foto, max_size=1400):
    """
    Gera um JPEG de preview para imagens comuns e RAWs suportados por rawpy.
    Retorna False quando o arquivo nao pode ser convertido.
    """
    path = Path(arquivo_foto.arquivo.path)
    ext = path.suffix.lower()

    try:
        image = _open_raw(path) if ext in RAW_EXTENSIONS else _open_with_pillow(path)
        if image is None:
            return False

        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "L"):
            background = Image.new("RGB", image.size, "white")
            if "A" in image.getbands():
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
        else:
            image = image.convert("RGB")

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=86, optimize=True)
        buffer.seek(0)

        arquivo_foto.thumbnail.save(
            f"thumb_{arquivo_foto.pk}.jpg",
            ContentFile(buffer.read()),
            save=True,
        )
        return True
    except Exception as exc:
        logger.warning(
            "thumbnail: falha ao gerar preview para foto pk=%s (%s): %s",
            arquivo_foto.pk,
            arquivo_foto.arquivo.name,
            exc,
        )
        return False


def _open_with_pillow(path):
    image = Image.open(path)
    return ImageOps.exif_transpose(image)


def _open_raw(path):
    try:
        import rawpy
    except ImportError:
        logger.warning("thumbnail: rawpy nao instalado; preview RAW indisponivel para %s", path)
        return None

    with rawpy.imread(str(path)) as raw:
        try:
            thumb = raw.extract_thumb()
            if thumb.format == rawpy.ThumbFormat.JPEG:
                return Image.open(io.BytesIO(thumb.data))
            if thumb.format == rawpy.ThumbFormat.BITMAP:
                return Image.fromarray(thumb.data)
        except Exception:
            rgb = raw.postprocess(use_camera_wb=True, half_size=True)
            return Image.fromarray(rgb)
    return None
