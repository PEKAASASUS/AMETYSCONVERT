import logging
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

from app.converters.formats import INPUT_EXTS, OUTPUT_LABELS
from app.converters.ico_converter import ALL_SIZES, PROFILES
from app.core.converter_manager import EXISTS_POLICIES
from app.ui import theme
from app.ui.widgets import DropZone, QualityControl
from app.utils.file_utils import app_dir, filter_by_ext
from app.utils.image_utils import make_thumbnail, probe

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _Base, HAS_DND = TkinterDnD.Tk, True
except Exception:
    _Base, HAS_DND = tk.Tk, False

CUSTOM = "Personalizado"
QUALITY_FORMATS = ("JPG", "JPEG", "WEBP")
APP_VERSION = "1.2"


class MainWindow(_Base):
    def __init__(self, manager, settings):
        super().__init__()
        self.manager, self.settings = manager, settings
        self.files: list[Path] = []
        self._info: dict[str, tuple] = {}      # str(path) -> (rotulo, largura, altura)
        self._thumbs: dict[str, object] = {}   # mantem referencia as miniaturas
        self.events = queue.Queue()

        self.title("Ametista")
        self.geometry("760x680")
        self.minsize(660, 560)
        theme.apply(self)
        self._logo_img = self._load_image(app_dir() / "assets" / "icons" / "ametista.png", (40, 40))
        self._blank_thumb = self._load_image(app_dir() / "assets" / "icons" / "generic_image.png", (34, 34))
        self._set_window_icon()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._close)

    # ---------- utilidades de imagem ----------
    @staticmethod
    def _load_image(path: Path, size):
        try:
            im = Image.open(path).convert("RGBA")
            im.thumbnail(size, Image.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception:
            return None

    def _set_window_icon(self):
        try:
            self.iconbitmap(app_dir() / "assets" / "icons" / "ametista.ico")
        except tk.TclError:
            pass

    # ---------- construcao da interface ----------
    def _build(self):
        pad = {"padx": 24}
        self._build_header(pad)
        self._build_dropzone(pad)
        self._build_files_card(pad)
        self._build_options_card(pad)
        self._build_output_card(pad)
        self._build_footer(pad)
        self._sync_target()

    def _build_header(self, pad):
        head = ttk.Frame(self)
        head.pack(fill="x", pady=(20, 8), **pad)
        if self._logo_img:
            tk.Label(head, image=self._logo_img, bg=theme.BG).pack(side="left", padx=(0, 12))
        titles = ttk.Frame(head)
        titles.pack(side="left")
        ttk.Label(titles, text="Ametista", style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text="Conversor de imagens", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(head, text=f"v{APP_VERSION}", style="Muted.TLabel").pack(side="right", anchor="n")

    def _build_dropzone(self, pad):
        wrap = ttk.Frame(self)
        wrap.pack(fill="x", pady=(0, 12), **pad)
        self.dropzone = DropZone(wrap, on_click=self._add_dialog, has_dnd=HAS_DND)
        self.dropzone.pack(fill="x")
        if HAS_DND:
            self.dropzone.drop_target_register(DND_FILES)
            self.dropzone.dnd_bind("<<Drop>>", lambda e: self._add(self.tk.splitlist(e.data)))

    def _build_files_card(self, pad):
        card = theme.card(self)
        card.pack(fill="both", expand=True, pady=(0, 12), **pad)

        head = ttk.Frame(card, style="Panel.TFrame")
        head.pack(fill="x", padx=16, pady=(12, 6))
        self.files_title = ttk.Label(head, text="Nenhuma imagem selecionada", style="Muted.TLabel")
        self.files_title.pack(side="left")
        ttk.Button(head, text="Limpar tudo", style="Link.TButton", command=self._clear).pack(side="right")
        ttk.Button(head, text="Remover selecionadas", style="Link.TButton",
                  command=self._remove).pack(side="right", padx=(0, 4))

        wrap = ttk.Frame(card, style="Panel.TFrame")
        wrap.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.tree = ttk.Treeview(wrap, columns=("info", "status"), show="tree headings",
                                 selectmode="extended", height=8)
        self.tree.heading("#0", text="Arquivo", anchor="w")
        self.tree.heading("info", text="Formato", anchor="w")
        self.tree.heading("status", text="Resultado", anchor="w")
        self.tree.column("#0", width=260, anchor="w")
        self.tree.column("info", width=140, anchor="w")
        self.tree.column("status", width=220, anchor="w")
        self.tree.tag_configure("ok", foreground=theme.OK)
        self.tree.tag_configure("warn", foreground=theme.WARN)
        self.tree.tag_configure("err", foreground=theme.ERR)
        sb = ttk.Scrollbar(wrap, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    def _build_options_card(self, pad):
        card = theme.card(self)
        card.pack(fill="x", pady=(0, 12), **pad)

        row1 = ttk.Frame(card, style="Panel.TFrame")
        row1.pack(fill="x", padx=16, pady=(14, 6))
        self.from_label = ttk.Label(row1, text="Adicione imagens para comecar", style="Muted.TLabel")
        self.from_label.pack(side="left")
        ttk.Label(row1, text="Converter para", style="Muted.TLabel").pack(side="right", padx=(0, 8))
        self.target = ttk.Combobox(row1, state="readonly", values=OUTPUT_LABELS, width=9)
        self.target.set(self.settings.target_format if self.settings.target_format in OUTPUT_LABELS else "PNG")
        self.target.pack(side="right")
        self.target.bind("<<ComboboxSelected>>", lambda e: self._sync_target())

        self.dynamic = ttk.Frame(card, style="Panel.TFrame")
        self.dynamic.pack(fill="x", padx=16, pady=(2, 6))

        row3 = ttk.Frame(card, style="Panel.TFrame")
        row3.pack(fill="x", padx=16, pady=(2, 14))
        ttk.Label(row3, text="Se ja existir", style="Muted.TLabel").pack(side="left")
        self.exists = ttk.Combobox(row3, state="readonly", values=EXISTS_POLICIES, width=16)
        self.exists.set(self.settings.on_exists if self.settings.on_exists in EXISTS_POLICIES else EXISTS_POLICIES[0])
        self.exists.pack(side="left", padx=12)

    def _build_output_card(self, pad):
        card = theme.card(self)
        card.pack(fill="x", pady=(0, 12), **pad)

        row = ttk.Frame(card, style="Panel.TFrame")
        row.pack(fill="x", padx=16, pady=(14, 6))
        ttk.Label(row, text="\U0001F4C1 Pasta de saida", style="Muted.TLabel").pack(side="left")
        ttk.Button(row, text="Escolher pasta...", command=self._choose_out).pack(side="right")
        ttk.Button(row, text="Original", command=lambda: self._set_out("")).pack(side="right", padx=(0, 6))

        path_row = ttk.Frame(card, style="Panel.TFrame")
        path_row.pack(fill="x", padx=16, pady=(0, 6))
        self.out_var = tk.StringVar(value=self.settings.output_dir)
        self.out_label = tk.StringVar()
        ttk.Label(path_row, textvariable=self.out_label, style="Muted.TLabel").pack(side="left")
        self._set_out(self.settings.output_dir)

        chk_row = ttk.Frame(card, style="Panel.TFrame")
        chk_row.pack(fill="x", padx=16, pady=(0, 14))
        self.open_after = tk.BooleanVar(value=self.settings.open_after)
        ttk.Checkbutton(chk_row, text="Abrir pasta apos a conversao",
                        variable=self.open_after, style="TCheckbutton").pack(side="left")

    def _build_footer(self, pad):
        foot = ttk.Frame(self)
        foot.pack(fill="x", pady=(0, 20), **pad)
        self.progress = ttk.Progressbar(foot, maximum=1)
        self.progress.pack(fill="x", pady=(0, 8))
        row = ttk.Frame(foot)
        row.pack(fill="x")
        self.status = tk.StringVar(value="Selecione imagens para comecar.")
        ttk.Label(row, textvariable=self.status, style="Muted.TLabel").pack(side="left")
        self.go = ttk.Button(row, text="\u2726 CONVERTER IMAGENS", style="Accent.TButton", command=self._start)
        self.go.pack(side="right")

    # ---------- opcoes dinamicas conforme o formato de saida ----------
    def _sync_target(self):
        for w in self.dynamic.winfo_children():
            w.destroy()
        target = self.target.get()
        if target == "ICO":
            self._build_ico_options(self.dynamic)
        elif target in QUALITY_FORMATS:
            self.quality_var = tk.DoubleVar(value=self.settings.quality)
            QualityControl(self.dynamic, self.quality_var).pack(fill="x")
        else:
            ttk.Label(self.dynamic, text="Este formato nao tem opcoes adicionais.",
                     style="Muted.TLabel").pack(anchor="w")
        self._refresh_from_label()

    def _build_ico_options(self, parent):
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Perfil", style="Muted.TLabel").pack(side="left")
        self.profile = ttk.Combobox(row, state="readonly", values=[*PROFILES, CUSTOM], width=15)
        self.profile.set(self.settings.profile if self.settings.profile in [*PROFILES, CUSTOM] else "Padrão")
        self.profile.pack(side="left", padx=12)
        self.profile.bind("<<ComboboxSelected>>", lambda e: self._sync_profile())
        self.custom = tk.StringVar(value=self.settings.custom_sizes)
        self.custom_entry = ttk.Entry(row, textvariable=self.custom, width=22)
        self.custom_entry.pack(side="left")
        self.sizes_info = ttk.Label(parent, style="Muted.TLabel")
        self.sizes_info.pack(anchor="w", pady=(4, 0))
        self._sync_profile()

    def _sync_profile(self):
        custom = self.profile.get() == CUSTOM
        self.custom_entry.configure(state="normal" if custom else "disabled")
        if custom:
            self.sizes_info.configure(text=f"Tamanhos separados por virgula: {', '.join(map(str, ALL_SIZES))}")
        else:
            self.sizes_info.configure(text="Tamanhos: " + ", ".join(map(str, PROFILES[self.profile.get()])))

    def _sizes(self):
        if self.profile.get() != CUSTOM:
            return PROFILES[self.profile.get()]
        try:
            sizes = sorted({int(x) for x in self.custom.get().replace(";", ",").split(",") if x.strip()})
        except ValueError:
            sizes = []
        if not sizes or any(s not in ALL_SIZES for s in sizes):
            raise ValueError(f"Use apenas: {', '.join(map(str, ALL_SIZES))}")
        return sizes

    def _refresh_from_label(self):
        if not self.files:
            self.from_label.configure(text="Adicione imagens para comecar")
            return
        labels = {self._info.get(str(f), ("?", None, None))[0] for f in self.files}
        if len(labels) == 1:
            self.from_label.configure(text=f"Converter de {next(iter(labels))}")
        else:
            self.from_label.configure(text=f"{len(self.files)} imagens selecionadas")

    # ---------- lista de arquivos ----------
    def _add_dialog(self):
        filetypes = [("Imagens", " ".join(f"*{e}" for e in INPUT_EXTS)), ("Todos os arquivos", "*.*")]
        paths = filedialog.askopenfilenames(title="Selecionar imagens", filetypes=filetypes)
        self._add(paths)

    def _add(self, paths):
        images = filter_by_ext(paths, INPUT_EXTS)
        if len(images) < len(paths):
            self.status.set("Alguns arquivos foram ignorados: formato nao suportado.")
        added = 0
        for p in images:
            key = str(p)
            if key in self._info:
                continue
            label, w, h = probe(p)
            self._info[key] = (label, w, h)
            info_text = f"{label}" + (f" - {w}x{h}" if w and h else "")
            thumb = make_thumbnail(p) or self._blank_thumb
            self._thumbs[key] = thumb
            self.files.append(p)
            self.tree.insert("", "end", iid=key, text=f" {p.name}", image=thumb,
                             values=(info_text, "Aguardando"))
            added += 1
        self.files_title.configure(
            text=f"{len(self.files)} imagem(ns) selecionada(s)" if self.files else "Nenhuma imagem selecionada")
        self._refresh_from_label()
        if added:
            self.status.set(f"{len(self.files)} arquivo(s) na lista.")

    def _remove(self):
        for iid in self.tree.selection():
            self.tree.delete(iid)
            self.files.remove(Path(iid))
            self._info.pop(iid, None)
            self._thumbs.pop(iid, None)
        self.files_title.configure(
            text=f"{len(self.files)} imagem(ns) selecionada(s)" if self.files else "Nenhuma imagem selecionada")
        self._refresh_from_label()

    def _clear(self):
        self.tree.delete(*self.tree.get_children())
        self.files.clear()
        self._info.clear()
        self._thumbs.clear()
        self.progress["value"] = 0
        self.files_title.configure(text="Nenhuma imagem selecionada")
        self._refresh_from_label()

    # ---------- pasta de saida ----------
    def _set_out(self, path):
        self.out_var.set(path)
        text = path or "Mesma pasta de cada arquivo"
        self.out_label.set(text if len(text) < 54 else "..." + text[-52:])

    def _choose_out(self):
        path = filedialog.askdirectory(title="Pasta de saida")
        if path:
            self._set_out(path)

    # ---------- conversao ----------
    def _start(self):
        if not self.files:
            messagebox.showinfo("Ametista", "Adicione ao menos uma imagem.")
            return
        target = self.target.get()
        options = {}
        if target == "ICO":
            try:
                options["sizes"] = self._sizes()
            except ValueError as e:
                messagebox.showwarning("Tamanhos invalidos", str(e))
                return
        elif target in QUALITY_FORMATS:
            options["quality"] = int(round(self.quality_var.get()))

        self._save_settings()
        for f in self.files:
            key = str(f)
            info_text = self.tree.item(key, "values")[0]
            self.tree.item(key, values=(info_text, "Aguardando"), tags=())
        self.progress.configure(maximum=len(self.files), value=0)
        self.go.state(["disabled"])
        self.status.set("Convertendo...")

        args = (list(self.files), self.out_var.get(), target, options, self.exists.get())
        threading.Thread(target=self._worker, args=args, daemon=True).start()
        self.after(60, self._poll)

    def _worker(self, files, out_dir, target, options, policy):
        for f in files:
            self.events.put(("item", self.manager.convert_file(f, out_dir, target, options, policy)))
        self.events.put(("done", None))

    def _poll(self):
        done = False
        while not self.events.empty():
            kind, res = self.events.get()
            if kind == "done":
                done = True
                continue
            iid = str(res.source)
            if self.tree.exists(iid):
                info_text = self.tree.item(iid, "values")[0]
                if res.ok and res.warning:
                    text, tag = f"\u26A0 {res.message}", "warn"
                elif res.ok:
                    text, tag = f"\u2713 {res.message}", "ok"
                else:
                    text, tag = f"\u2715 {res.message}", "err"
                self.tree.item(iid, values=(info_text, text), tags=(tag,))
            self.progress["value"] += 1
        if done:
            self._finish()
        else:
            self.after(60, self._poll)

    def _finish(self):
        tags = [self.tree.item(i, "tags") for i in self.tree.get_children()]
        ok = sum(("ok" in t) or ("warn" in t) for t in tags)
        warn = sum("warn" in t for t in tags)
        err = sum("err" in t for t in tags)
        parts = [f"{ok} convertido(s)"]
        if warn:
            parts.append(f"{warn} com aviso")
        parts.append(f"{err} com erro")
        self.status.set("Concluido: " + ", ".join(parts) + ".")
        self.go.state(["!disabled"])
        if self.open_after.get() and ok:
            self._open_output_folder()
        if err:
            messagebox.showwarning("Ametista", f"{ok} convertido(s) e {err} com erro.\nVeja os detalhes na lista.")
        else:
            messagebox.showinfo("Ametista", f"Conversao concluida: {ok} arquivo(s).")

    def _open_output_folder(self):
        folder = Path(self.out_var.get()) if self.out_var.get() else (self.files[0].parent if self.files else None)
        if not folder or not folder.exists():
            return
        try:
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except OSError:
            logging.exception("Nao foi possivel abrir a pasta %s", folder)

    # ---------- encerramento ----------
    def _save_settings(self):
        s = self.settings
        s.output_dir = self.out_var.get()
        s.on_exists = self.exists.get()
        s.target_format = self.target.get()
        if hasattr(self, "quality_var"):
            s.quality = int(round(self.quality_var.get()))
        if hasattr(self, "profile"):
            s.profile = self.profile.get()
        if hasattr(self, "custom"):
            s.custom_sizes = self.custom.get()
        s.open_after = self.open_after.get()
        s.save()

    def _close(self):
        self._save_settings()
        self.destroy()
