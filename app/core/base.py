from dataclasses import dataclass
from pathlib import Path


class ConversionError(Exception):
    """Erro com mensagem já pronta para o usuário."""


class BaseConverter:
    """Contrato de um conversor. Para criar um novo, herde e implemente convert()."""

    source_ext = ""
    target_ext = ""

    def convert(self, source: Path, target: Path, options: dict) -> None:
        raise NotImplementedError


@dataclass
class Result:
    source: Path
    output: Path | None
    ok: bool
    message: str
