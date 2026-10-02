"""Widgets compostos usados pela janela principal."""
import tkinter as tk
from tkinter import ttk

from app.ui import theme


def rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius=16, **kwargs):
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class DropZone(tk.Canvas):
    """Área de arrastar/soltar com cantos arredondados e destaque ao passar o mouse."""

    def __init__(self, master, on_click, has_dnd, height=75):
        super().__init__(master, bg=theme.BG, highlightthickness=0, height=height)
        self.on_click = on_click
        self._hover = False
        self._hint = "Arraste imagens aqui ou " if has_dnd else ""
        self.bind("<Configure>", self._redraw)
        self.bind("<Button-1>", lambda e: self.on_click())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.configure(cursor="hand2")

    def _set_hover(self, value):
        self._hover = value
        self._redraw()

    def _redraw(self, event=None):
        self.delete("all")
        w = max(self.winfo_width(), 40)
        h = max(self.winfo_height(), 40)
        border = theme.ACCENT_HI if self._hover else theme.BORDER
        fill = theme.SURFACE if self._hover else theme.PANEL
        rounded_rect(self, 3, 3, w - 3, h - 3, 18, outline=border, width=2,
                     dash=(6, 4), fill=fill)
        self.create_text(w / 2, h / 2 - 13, text="🖼  " + self._hint + "clique para adicionar imagens",
                          fill=theme.TEXT, font=("Segoe UI Semibold", 11))
        self.create_text(w / 2, h / 2 + 12,
                          text="PNG  ·  JPG  ·  JPEG  ·  WEBP  ·  BMP  ·  GIF  ·  TIFF  ·  ICO",
                          fill=theme.MUTED, font=("Segoe UI", 8))


class QualityControl(ttk.Frame):
    """Controle deslizante de qualidade (0-100%), usado para JPG/JPEG/WEBP."""

    def __init__(self, master, variable: tk.DoubleVar):
        super().__init__(master, style="Panel.TFrame")
        self.var = variable
        head = ttk.Frame(self, style="Panel.TFrame")
        head.pack(fill="x")
        ttk.Label(head, text="Qualidade", style="Muted.TLabel").pack(side="left")
        self.value_lbl = ttk.Label(head, style="Muted.TLabel")
        self.value_lbl.pack(side="right")
        self.scale = ttk.Scale(self, from_=10, to=100, orient="horizontal",
                                variable=variable, command=self._on_change)
        self.scale.pack(fill="x", pady=(2, 0))
        self._on_change(None)

    def _on_change(self, _event):
        self.value_lbl.configure(text=f"{int(round(self.var.get()))}%")
