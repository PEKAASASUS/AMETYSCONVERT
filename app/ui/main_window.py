import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from app.converters.png_to_ico import PROFILES, ALL_SIZES
from app.core.converter_manager import EXISTS_POLICIES
from app.ui import theme
from app.utils.file_utils import app_dir, filter_by_ext

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _Base, HAS_DND = TkinterDnD.Tk, True
except Exception:
    _Base, HAS_DND = tk.Tk, False

CUSTOM = "Personalizado"
SAME_DIR = "Mesma pasta de cada arquivo"


class MainWindow(_Base):
    def __init__(self, manager, settings):
        super().__init__()
        self.manager, self.settings = manager, settings
        self.files: list[Path] = []
        self.events = queue.Queue()
        self.title("Ametista")
        self.geometry("720x620")
        self.minsize(620, 520)
        theme.apply(self)
        self._set_icon()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._close)

    # ---------- construção da interface ----------
    def _set_icon(self):
        icon = app_dir() / "assets" / "icons" / "ametista.ico"
        try:
            self.iconbitmap(icon)
        except tk.TclError:
            pass

    def _build(self):
        pad = {"padx": 20}
        head = ttk.Frame(self)
        head.pack(fill="x", pady=(18, 8), **pad)
        ttk.Label(head, text="Ametista", style="Title.TLabel").pack(side="left")
        ttk.Label(head, text="PNG → ICO", style="Muted.TLabel").pack(side="left", padx=12, pady=(8, 0))

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8), **pad)
        ttk.Button(bar, text="+ Adicionar PNGs", command=self._add_dialog).pack(side="left")
        ttk.Button(bar, text="Remover", command=self._remove).pack(side="left", padx=6)
        ttk.Button(bar, text="Limpar", command=self._clear).pack(side="left")

        box = ttk.Frame(self, style="Panel.TFrame")
        box.pack(fill="both", expand=True, **pad)
        self.tree = ttk.Treeview(box, columns=("file", "status"), show="headings", selectmode="extended")
        self.tree.heading("file", text="Arquivo", anchor="w")
        self.tree.heading("status", text="Resultado", anchor="w")
        self.tree.column("file", width=300)
        self.tree.column("status", width=300)
        self.tree.tag_configure("ok", foreground=theme.OK)
        self.tree.tag_configure("err", foreground=theme.ERR)
        sb = ttk.Scrollbar(box, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.hint = tk.Label(box, bg=theme.PANEL, fg=theme.MUTED, font=theme.FONT,
                             text="Arraste PNGs aqui ou clique em “Adicionar PNGs”" if HAS_DND
                             else "Clique em “Adicionar PNGs” para começar")
        self.hint.place(relx=0.5, rely=0.5, anchor="center")
        if HAS_DND:
            for w in (self.tree, self.hint):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", lambda e: self._add(self.tk.splitlist(e.data)))

        opts = ttk.Frame(self)
        opts.pack(fill="x", pady=(14, 0), **pad)
        opts.columnconfigure(1, weight=1)
        self.out_var = tk.StringVar(value=self.settings.output_dir)
        self.out_label = tk.StringVar()
        ttk.Label(opts, text="Saída").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(opts, textvariable=self.out_label, style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=12)
        ttk.Button(opts, text="Escolher pasta…", command=self._choose_out).grid(row=0, column=2)
        ttk.Button(opts, text="Original", command=lambda: self._set_out("")).grid(row=0, column=3, padx=(6, 0))
        self._set_out(self.settings.output_dir)

        ttk.Label(opts, text="Perfil").grid(row=1, column=0, sticky="w", pady=4)
        self.profile = ttk.Combobox(opts, state="readonly", values=[*PROFILES, CUSTOM], width=16)
        self.profile.set(self.settings.profile if self.settings.profile in [*PROFILES, CUSTOM] else "Padrão")
        self.profile.grid(row=1, column=1, sticky="w", padx=12)
        self.profile.bind("<<ComboboxSelected>>", lambda e: self._sync_profile())
        self.custom = tk.StringVar(value=self.settings.custom_sizes)
        self.custom_entry = ttk.Entry(opts, textvariable=self.custom, width=26)
        self.custom_entry.grid(row=1, column=2, columnspan=2, sticky="e")
        self.sizes_info = ttk.Label(opts, style="Muted.TLabel")
        self.sizes_info.grid(row=2, column=1, columnspan=3, sticky="w", padx=12)
        self._sync_profile()

        ttk.Label(opts, text="Se já existir").grid(row=3, column=0, sticky="w", pady=4)
        self.exists = ttk.Combobox(opts, state="readonly", values=EXISTS_POLICIES, width=16)
        self.exists.set(self.settings.on_exists if self.settings.on_exists in EXISTS_POLICIES else EXISTS_POLICIES[0])
        self.exists.grid(row=3, column=1, sticky="w", padx=12)

        foot = ttk.Frame(self)
        foot.pack(fill="x", pady=16, **pad)
        self.progress = ttk.Progressbar(foot, maximum=1)
        self.progress.pack(fill="x", pady=(0, 10))
        self.status = tk.StringVar(value="Selecione arquivos PNG para começar.")
        ttk.Label(foot, textvariable=self.status, style="Muted.TLabel").pack(side="left")
        self.go = ttk.Button(foot, text="Converter", style="Accent.TButton", command=self._start)
        self.go.pack(side="right")

    # ---------- lista de arquivos ----------
    def _add_dialog(self):
        paths = filedialog.askopenfilenames(title="Selecionar PNGs", filetypes=[("Imagens PNG", "*.png")])
        self._add(paths)

    def _add(self, paths):
        pngs = filter_by_ext(paths, ".png")
        if len(pngs) < len(paths):
            self.status.set("Alguns arquivos foram ignorados: só PNG é aceito.")
        for p in pngs:
            if p not in self.files:
                self.files.append(p)
                self.tree.insert("", "end", iid=str(p), values=(p.name, "Aguardando"))
        self._refresh_hint()
        if pngs:
            self.status.set(f"{len(self.files)} arquivo(s) na lista.")

    def _remove(self):
        for iid in self.tree.selection():
            self.tree.delete(iid)
            self.files.remove(Path(iid))
        self._refresh_hint()

    def _clear(self):
        self.tree.delete(*self.tree.get_children())
        self.files.clear()
        self.progress["value"] = 0
        self._refresh_hint()

    def _refresh_hint(self):
        if self.files:
            self.hint.place_forget()
        else:
            self.hint.place(relx=0.5, rely=0.5, anchor="center")

    # ---------- opções ----------
    def _set_out(self, path):
        self.out_var.set(path)
        text = path or SAME_DIR
        self.out_label.set(text if len(text) < 48 else "…" + text[-46:])

    def _choose_out(self):
        path = filedialog.askdirectory(title="Pasta de saída")
        if path:
            self._set_out(path)

    def _sync_profile(self):
        custom = self.profile.get() == CUSTOM
        self.custom_entry.configure(state="normal" if custom else "disabled")
        if custom:
            self.sizes_info.configure(text=f"Tamanhos separados por vírgula: {', '.join(map(str, ALL_SIZES))}")
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

    # ---------- conversão ----------
    def _start(self):
        if not self.files:
            messagebox.showinfo("Ametista", "Adicione ao menos um arquivo PNG.")
            return
        try:
            sizes = self._sizes()
        except ValueError as e:
            messagebox.showwarning("Tamanhos inválidos", str(e))
            return
        self._save_settings()
        for f in self.files:
            self.tree.item(str(f), values=(f.name, "Aguardando"), tags=())
        self.progress.configure(maximum=len(self.files), value=0)
        self.go.state(["disabled"])
        self.status.set("Convertendo…")
        args = (list(self.files), self.out_var.get(), {"sizes": sizes}, self.exists.get())
        threading.Thread(target=self._worker, args=args, daemon=True).start()
        self.after(60, self._poll)

    def _worker(self, files, out_dir, options, policy):
        for f in files:
            self.events.put(("item", self.manager.convert_file(f, out_dir, ".ico", options, policy)))
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
                text = f"✓ {res.source.name} → {res.message}" if res.ok else f"✕ {res.message}"
                self.tree.item(iid, values=(res.source.name, text), tags=("ok" if res.ok else "err",))
            self.progress["value"] += 1
        if done:
            self._finish()
        else:
            self.after(60, self._poll)

    def _finish(self):
        tags = [self.tree.item(i, "tags") for i in self.tree.get_children()]
        ok, err = sum("ok" in t for t in tags), sum("err" in t for t in tags)
        self.status.set(f"Concluído: {ok} convertido(s), {err} com erro.")
        self.go.state(["!disabled"])
        if err:
            messagebox.showwarning("Ametista", f"{ok} convertido(s) e {err} com erro.\nVeja os detalhes na lista.")
        else:
            messagebox.showinfo("Ametista", f"Conversão concluída: {ok} arquivo(s).")

    # ---------- encerramento ----------
    def _save_settings(self):
        s = self.settings
        s.output_dir, s.profile = self.out_var.get(), self.profile.get()
        s.custom_sizes, s.on_exists = self.custom.get(), self.exists.get()
        s.save()

    def _close(self):
        self._save_settings()
        self.destroy()
