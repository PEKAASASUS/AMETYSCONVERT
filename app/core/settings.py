import json
import logging
from dataclasses import dataclass, asdict

from app.utils.file_utils import app_dir

FILE = app_dir() / "config" / "settings.json"


@dataclass
class Settings:
    output_dir: str = ""          # vazio = mesma pasta de cada arquivo
    profile: str = "Padrão"
    custom_sizes: str = "16, 32, 48, 256"
    on_exists: str = "Criar novo nome"  # | Sobrescrever | Pular
    target_format: str = "ICO"    # formato de saída selecionado por último
    quality: int = 90             # qualidade para JPG/JPEG/WEBP
    open_after: bool = False      # abrir a pasta de saída ao concluir

    @classmethod
    def load(cls):
        try:
            data = json.loads(FILE.read_text(encoding="utf-8"))
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self):
        try:
            FILE.parent.mkdir(exist_ok=True)
            FILE.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            logging.exception("Não foi possível salvar as configurações")
