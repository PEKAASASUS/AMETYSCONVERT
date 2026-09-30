import logging
from pathlib import Path

from app.core.base import BaseConverter, ConversionError, Result
from app.converters.png_to_ico import PngToIco
from app.utils.file_utils import output_path, unique_path

OVERWRITE, RENAME, SKIP = "Sobrescrever", "Criar novo nome", "Pular"
EXISTS_POLICIES = [RENAME, OVERWRITE, SKIP]


class ConverterManager:
    def __init__(self):
        self._converters: dict[tuple[str, str], BaseConverter] = {}
        self.register(PngToIco())  # novos conversores: registrar aqui

    def register(self, converter: BaseConverter):
        self._converters[(converter.source_ext, converter.target_ext)] = converter

    def get(self, source_ext: str, target_ext: str) -> BaseConverter:
        try:
            return self._converters[(source_ext, target_ext)]
        except KeyError:
            raise ConversionError("Conversão não suportada.")

    def convert_file(self, source: Path, out_dir: str, target_ext: str,
                     options: dict, on_exists: str = RENAME) -> Result:
        try:
            converter = self.get(source.suffix.lower(), target_ext)
            target = output_path(source, out_dir, target_ext)
            if target.exists():
                if on_exists == SKIP:
                    return Result(source, None, False, "Já existe — pulado.")
                if on_exists == RENAME:
                    target = unique_path(target)
            if not target.parent.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
            converter.convert(source, target, options)
            return Result(source, target, True, target.name)
        except ConversionError as e:
            return Result(source, None, False, str(e))
        except PermissionError:
            return Result(source, None, False, "Sem permissão na pasta de saída.")
        except Exception:
            logging.exception("Erro inesperado em %s", source)
            return Result(source, None, False, "Erro inesperado (veja o log).")
