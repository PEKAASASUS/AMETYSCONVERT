"""Tabela única de formatos suportados. Usada pelos conversores e pela interface."""

# rótulo mostrado na interface -> extensão gravada em disco
SUPPORTED = {
    "PNG": ".png",
    "JPG": ".jpg",
    "JPEG": ".jpeg",
    "WEBP": ".webp",
    "BMP": ".bmp",
    "GIF": ".gif",
    "TIFF": ".tiff",
    "ICO": ".ico",
}

# rótulo -> nome do formato para a Pillow
PILLOW_FORMAT = {
    "PNG": "PNG", "JPG": "JPEG", "JPEG": "JPEG", "WEBP": "WEBP",
    "BMP": "BMP", "GIF": "GIF", "TIFF": "TIFF", "ICO": "ICO",
}

# extensão de um arquivo já existente -> rótulo (para detectar o formato de entrada)
EXT_TO_LABEL = {
    ".png": "PNG", ".jpg": "JPG", ".jpeg": "JPEG", ".webp": "WEBP",
    ".bmp": "BMP", ".gif": "GIF", ".tiff": "TIFF", ".tif": "TIFF", ".ico": "ICO",
}

INPUT_EXTS = tuple(EXT_TO_LABEL)
OUTPUT_LABELS = list(SUPPORTED)  # ordem de exibição no seletor

# formatos sem canal alfa: transparência precisa ser resolvida antes de salvar
NON_ALPHA = {"JPEG", "BMP", "GIF"}
