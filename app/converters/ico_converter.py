from pathlib import Path

from PIL import Image

from app.core.base import BaseConverter, ConversionError
from app.converters.imaging import open_image, is_animated
import logging

PROFILES = {
    "Padrão": [16, 32, 48, 64, 128, 256],
    "Ícone pequeno": [16, 24, 32, 48],
    "Ícone grande": [64, 128, 256],
}
ALL_SIZES = [16, 24, 32, 48, 64, 128, 256]
MAX = 256


class IcoConverter(BaseConverter):
    """Gera arquivos .ico a partir de qualquer formato de imagem suportado.

    Mantém o comportamento da V1: fundo transparente, imagem centralizada em
    tela quadrada e múltiplas resoluções dentro de um único .ico.
    """

    @classmethod
    def handles(cls, source_ext: str, target_label: str) -> bool:
        return target_label == "ICO"

    def convert(self, source: Path, target: Path, options: dict):
        sizes = options.get("sizes") or PROFILES["Padrão"]
        im = open_image(source)
        warning = "GIF animado: apenas o primeiro quadro foi usado." if is_animated(im) else None

        base = self._square(im.convert("RGBA")).resize((MAX, MAX), Image.LANCZOS)
        try:
            base.save(target, format="ICO", sizes=[(s, s) for s in sorted(set(sizes))])
        except PermissionError:
            raise ConversionError("Sem permissão para gravar na pasta de saída.")
        except OSError:
            logging.exception("Falha ao gravar %s", target)
            target.unlink(missing_ok=True)
            raise ConversionError("Não foi possível gravar o arquivo ICO.")
        return warning

    @staticmethod
    def _square(im: Image.Image) -> Image.Image:
        """Centraliza em tela quadrada transparente para não distorcer."""
        w, h = im.size
        if w == h:
            return im
        side = max(w, h)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(im, ((side - w) // 2, (side - h) // 2))
        return canvas
