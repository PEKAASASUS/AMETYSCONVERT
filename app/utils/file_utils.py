import sys
from pathlib import Path


def app_dir() -> Path:
    """Pasta do aplicativo: ao lado do .exe (empacotado) ou raiz do projeto."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def unique_path(path: Path) -> Path:
    """nome.ico -> nome (1).ico -> nome (2).ico ..."""
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def output_path(source: Path, out_dir: str, target_ext: str) -> Path:
    folder = Path(out_dir) if out_dir else source.parent
    return folder / (source.stem + target_ext)


def filter_by_ext(paths, exts):
    """Mantém apenas caminhos cuja extensão está em `exts` (uma string ou uma tupla)."""
    if isinstance(exts, str):
        exts = (exts,)
    exts = tuple(e.lower() for e in exts)
    return [Path(p) for p in paths if str(p).lower().endswith(exts)]
