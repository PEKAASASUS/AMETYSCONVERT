from pathlib import Path
import logging

from app.core.base import BaseConverter, ConversionError
from app.converters.formats import PILLOW_FORMAT, NON_ALPHA
from app.converters.imaging import open_image, is_animated, flatten


class GenericImageConverter(BaseConverter):
    """Converte entre os formatos de imagem comuns (PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF).

    A criação de .ico continua com regras próprias em IcoConverter.
    """

    @classmethod
    def handles(cls, source_ext: str, target_label: str) -> bool:
        return target_label in PILLOW_FORMAT and target_label != "ICO"

    def convert(self, source: Path, target: Path, options: dict):
        target_label = options["target_format"]
        pillow_format = PILLOW_FORMAT[target_label]
        quality = int(options.get("quality", 90))

        im = open_image(source)
        warning = "GIF animado: apenas o primeiro quadro foi convertido." if is_animated(im) else None

        # Normaliza modos indiretos (paleta, luminância+alfa) para poder decidir sobre transparência
        if im.mode in ("P", "LA", "PA") or ("transparency" in im.info and im.mode != "RGBA"):
            im = im.convert("RGBA")

        if pillow_format in NON_ALPHA and im.mode in ("RGBA", "LA"):
            im = flatten(im)
        elif pillow_format == "JPEG" and im.mode not in ("RGB", "L"):
            im = im.convert("RGB")

        save_kwargs = {}
        if pillow_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = max(1, min(100, quality))
        if pillow_format == "JPEG":
            save_kwargs["optimize"] = True

        try:
            im.save(target, format=pillow_format, **save_kwargs)
        except PermissionError:
            raise ConversionError("Sem permissão para gravar na pasta de saída.")
        except (OSError, ValueError):
            logging.exception("Falha ao converter %s", source)
            target.unlink(missing_ok=True)
            raise ConversionError(f"Não foi possível gerar um {target_label} válido a partir deste arquivo.")
        return warning
