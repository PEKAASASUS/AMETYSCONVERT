from dataclasses import dataclass
from pathlib import Path


class ConversionError(Exception):
    """Erro com mensagem já pronta para o usuário."""


class BaseConverter:
    """Contrato de um conversor.

    Para criar um novo, herde esta classe, implemente handles() para dizer quais
    pares (extensão de entrada, formato de saída) ele resolve, e convert() para
    executar a conversão. Se o formato de entrada permitir vários quadros (como
    GIF animado) e apenas o primeiro for usado, convert() pode retornar uma
    mensagem de aviso (str); caso contrário, retorna None.
    """

    source_ext = ""
    target_ext = ""

    @classmethod
    def handles(cls, source_ext: str, target_label: str) -> bool:
        return source_ext == cls.source_ext and target_label == cls.target_ext.lstrip(".").upper()

    def convert(self, source: Path, target: Path, options: dict):
        raise NotImplementedError


@dataclass
class Result:
    source: Path
    output: Path | None
    ok: bool
    message: str
    warning: bool = False
