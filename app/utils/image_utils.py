"""Miniaturas e informações de arquivo para a lista da interface.

Usa apenas leitura leve (sem carregar a imagem em resolução máxima), para não
pesar a memória quando muitos arquivos grandes forem adicionados de uma vez.
"""
from pathlib import Path

from PIL import Image, ImageTk

from app.converters.formats import EXT_TO_LABEL


def probe(path: Path):
    """Retorna (rótulo_do_formato, largura, altura). Dimensões None se ilegível."""
    label = EXT_TO_LABEL.get(path.suffix.lower(), path.suffix.lstrip(".").upper() or "?")
    try:
        with Image.open(path) as im:
            return EXT_TO_LABEL.get(path.suffix.lower(), im.format or label), im.size[0], im.size[1]
    except Exception:
        return label, None, None


def make_thumbnail(path: Path, size=(34, 34)):
    """Miniatura como PhotoImage, ou None se o arquivo não puder ser lido."""
    try:
        with Image.open(path) as im:
            im = im.convert("RGBA")
            im.thumbnail(size, Image.LANCZOS)
            canvas = Image.new("RGBA", size, (0, 0, 0, 0))
            canvas.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2), im)
            return ImageTk.PhotoImage(canvas)
    except Exception:
        return None
