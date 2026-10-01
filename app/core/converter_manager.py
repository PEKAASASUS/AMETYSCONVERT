import logging
from pathlib import Path

from app.converters.formats import SUPPORTED
from app.converters.ico_converter import IcoConverter
from app.converters.image_converter import GenericImageConverter
from app.core.base import BaseConverter, ConversionError, Result
from app.utils.file_utils import output_path, unique_path

OVERWRITE, RENAME, SKIP = "Sobrescrever", "Criar novo nome", "Pular"
EXISTS_POLICIES = [RENAME, OVERWRITE, SKIP]


class ConverterManager:
    def __init__(self):
        self._converters: list[BaseConverter] = []
        self.register(IcoConverter())            # regras próprias de tamanhos/perfis
        self.register(GenericImageConverter())    # demais formatos de imagem
        # novos grupos futuros (documentos, áudio, vídeo) se registram aqui,
        # sem precisar alterar o restante do aplicativo.

    def register(self, converter: BaseConverter):
        self._converters.append(converter)

    def get(self, source_ext: str, target_label: str) -> BaseConverter:
        for converter in self._converters:
            if converter.handles(source_ext, target_label):
                return converter
        raise ConversionError("Conversão não suportada.")

    def convert_file(self, source: Path, out_dir: str, target_label: str,
                     options: dict, on_exists: str = RENAME) -> Result:
        try:
            converter = self.get(source.suffix.lower(), target_label)
            ext = SUPPORTED[target_label]
            target = output_path(source, out_dir, ext)

            same_file = target.resolve() == source.resolve()
            if target.exists() or same_file:
                if on_exists == SKIP:
                    reason = "Mesmo arquivo de origem — pulado." if same_file else "Já existe — pulado."
                    return Result(source, None, False, reason)
                if on_exists == RENAME:
                    target = unique_path(target)
                # OVERWRITE com same_file: a imagem já foi lida por completo em
                # open_image() antes de qualquer gravação, então é seguro regravar.

            if not target.parent.exists():
                target.parent.mkdir(parents=True, exist_ok=True)

            warning = converter.convert(source, target, dict(options, target_format=target_label))
            message = target.name if not warning else f"{target.name} — {warning}"
            return Result(source, target, True, message, warning=bool(warning))
        except ConversionError as e:
            return Result(source, None, False, str(e))
        except PermissionError:
            return Result(source, None, False, "Sem permissão na pasta de saída.")
        except Exception:
            logging.exception("Erro inesperado em %s", source)
            return Result(source, None, False, "Erro inesperado (veja o log).")
