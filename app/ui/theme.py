from tkinter import ttk

BG, PANEL, SURFACE, BORDER = "#0e0e12", "#17171d", "#20202a", "#32323f"
TEXT, MUTED = "#ebe8f2", "#8c889b"
ACCENT, ACCENT_HI, DEEP = "#9b5de5", "#b47df0", "#4c1d8a"
OK, ERR = "#5fd38d", "#ff6b81"
FONT = ("Segoe UI", 10)


def apply(root):
    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.background", SURFACE)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=BG, foreground=TEXT, font=FONT, bordercolor=BORDER)
    s.configure("TFrame", background=BG)
    s.configure("Panel.TFrame", background=PANEL)
    s.configure("TLabel", background=BG, foreground=TEXT)
    s.configure("Muted.TLabel", foreground=MUTED)
    s.configure("Title.TLabel", font=("Segoe UI Semibold", 20), foreground=ACCENT_HI)
    s.configure("TButton", background=SURFACE, foreground=TEXT, padding=(12, 7), borderwidth=0, focusthickness=0)
    s.map("TButton", background=[("active", BORDER), ("disabled", PANEL)], foreground=[("disabled", MUTED)])
    s.configure("Accent.TButton", background=ACCENT, foreground="white", font=("Segoe UI Semibold", 11), padding=(22, 9))
    s.map("Accent.TButton", background=[("active", ACCENT_HI), ("disabled", DEEP)], foreground=[("disabled", MUTED)])
    s.configure("TCombobox", fieldbackground=SURFACE, background=SURFACE, foreground=TEXT,
                arrowcolor=ACCENT_HI, borderwidth=0, padding=5)
    s.map("TCombobox", fieldbackground=[("readonly", SURFACE)], foreground=[("readonly", TEXT)])
    s.configure("TEntry", fieldbackground=SURFACE, foreground=TEXT, borderwidth=0, padding=5)
    s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                rowheight=28, borderwidth=0)
    s.map("Treeview", background=[("selected", DEEP)], foreground=[("selected", "white")])
    s.configure("Treeview.Heading", background=SURFACE, foreground=MUTED, borderwidth=0, padding=6)
    s.configure("Horizontal.TProgressbar", troughcolor=SURFACE, background=ACCENT, borderwidth=0, thickness=8)
    s.configure("Vertical.TScrollbar", background=SURFACE, troughcolor=PANEL, borderwidth=0, arrowcolor=MUTED)
