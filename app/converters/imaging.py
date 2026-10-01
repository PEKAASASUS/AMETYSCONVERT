"""Utilidades de abertura/tratamento de imagem compartilhadas pelos conversores."""
import logging
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.base import ConversionError

# O Ametista é um app local: o próprio usuário escolhe os arquivos que abre,
# então não aplicamos o limite de "bomba de descompressão" da Pillow.
Image.MAX_IMAGE_PIXELS = None


def open_image(source: Path) -> Image.Image:
    """Abre e carrega a imagem por completo (necessário antes de regravar no mesmo caminho)."""
    try:
        im = Image.open(source)
        im.load()
        return im
    except FileNotFoundError:
        raise ConversionError("Arquivo não encontrado.")
    except PermissionError:
        raise ConversionError("Sem permissão para ler o arquivo.")
    except MemoryError:
        raise ConversionError("Memória insuficiente para processar esta imagem.")
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        logging.exception("Imagem inválida: %s", source)
        raise ConversionError("Imagem corrompida ou em formato incompatível.")


def is_animated(im: Image.Image) -> bool:
    return getattr(im, "n_frames", 1) > 1


def flatten(im: Image.Image, bg=(255, 255, 255)) -> Image.Image:
    """Achata transparência sobre um fundo sólido, para formatos sem canal alfa."""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    canvas = Image.new("RGB", im.size, bg)
    canvas.paste(im, mask=im.split()[-1])
    return canvas
