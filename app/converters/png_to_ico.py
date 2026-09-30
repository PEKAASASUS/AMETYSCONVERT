import logging
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.base import BaseConverter, ConversionError

PROFILES = {
    "Padrão": [16, 32, 48, 64, 128, 256],
    "Ícone pequeno": [16, 24, 32, 48],
    "Ícone grande": [64, 128, 256],
}
ALL_SIZES = [16, 24, 32, 48, 64, 128, 256]
MAX = 256


class PngToIco(BaseConverter):
    source_ext = ".png"
    target_ext = ".ico"

    def convert(self, source: Path, target: Path, options: dict) -> None:
        sizes = options.get("sizes") or PROFILES["Padrão"]
        image = self._load(source)
        base = self._square(image).resize((MAX, MAX), Image.LANCZOS)
        try:
            base.save(target, format="ICO", sizes=[(s, s) for s in sorted(set(sizes))])
        except PermissionError:
            raise ConversionError("Sem permissão para gravar na pasta de saída.")
        except OSError:
            logging.exception("Falha ao gravar %s", target)
            target.unlink(missing_ok=True)
            raise ConversionError("Não foi possível gravar o arquivo ICO.")

    @staticmethod
    def _load(source: Path) -> Image.Image:
        try:
            with Image.open(source) as im:
                if im.format != "PNG":
                    raise ConversionError("O arquivo não é um PNG válido.")
                im.load()
                return im.convert("RGBA")
        except ConversionError:
            raise
        except FileNotFoundError:
            raise ConversionError("Arquivo não encontrado.")
        except PermissionError:
            raise ConversionError("Sem permissão para ler o arquivo.")
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
            logging.exception("PNG inválido: %s", source)
            raise ConversionError("PNG corrompido ou incompatível.")

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
