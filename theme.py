"""One place for how the app looks: the palette, the fonts and the widget defaults.

`Theme.apply(root)` is called once on the main window. It fills the Tk option
database, so a plain `tk.Label(...)` or `tk.Entry(...)` anywhere in the app -
popups included - comes out themed without passing colors around. A widget that
wants to stand out spreads one of the dicts below instead, e.g.
`tk.Button(frame, text="Ask", **Theme.PRIMARY_BUTTON)`.
"""

import tkinter as tk
from tkinter import ttk


class Theme:
    # ---- palette ----
    BG = "#151a21"           # the window itself
    SURFACE = "#1c232c"      # anything the user types in or reads from
    SURFACE_ALT = "#232c37"  # buttons, table headings
    BORDER = "#2e3946"
    TEXT = "#e6edf3"
    TEXT_MUTED = "#8b98a5"   # hints, secondary lines
    ACCENT = "#3d7eff"
    ACCENT_HOVER = "#5590ff"
    ACCENT_TEXT = "#ffffff"
    SUCCESS = "#3fb950"
    WARNING = "#d29922"
    DANGER = "#f85149"
    INFO = "#58a6ff"

    # ---- fonts ----
    FONT = ("Segoe UI", 10)
    FONT_SMALL = ("Segoe UI", 9)
    FONT_BOLD = ("Segoe UI Semibold", 10)
    FONT_SUBTITLE = ("Segoe UI Semibold", 11)
    FONT_HEADING = ("Segoe UI Semibold", 14)
    FONT_TITLE = ("Segoe UI Semibold", 18)
    FONT_MONO = ("Consolas", 10)  # the log and the model's answer

    # ---- widget recipes ----
    # Tk shows `activebackground` while the pointer is over the button, so the
    # hover color is just that.
    BUTTON = {
        "bg": SURFACE_ALT,
        "fg": TEXT,
        "activebackground": BORDER,
        "activeforeground": TEXT,
        "relief": tk.FLAT,
        "bd": 0,
        "highlightthickness": 0,
        "padx": 12,
        "pady": 6,
        "cursor": "hand2",
        "font": FONT,
    }
    PRIMARY_BUTTON = {
        **BUTTON,
        "bg": ACCENT,
        "fg": ACCENT_TEXT,
        "activebackground": ACCENT_HOVER,
        "activeforeground": ACCENT_TEXT,
        "font": FONT_BOLD,
    }
    # A panel that holds a page of its own inside a bigger page.
    CARD = {
        "bg": BG,
        "highlightbackground": BORDER,
        "highlightcolor": BORDER,
        "highlightthickness": 1,
        "bd": 0,
    }

    @staticmethod
    def font_spec(font) -> str:
        """A font tuple as the string the option database wants."""
        family, size, *rest = font
        return " ".join(["{%s}" % family, str(size), *rest])

    @classmethod
    def apply(cls, root):
        """Theme this window and everything built in it from now on."""
        root.configure(bg=cls.BG)
        cls._widget_defaults(root)
        cls._ttk_styles(root)

    # ---- classic tk widgets ----
    @classmethod
    def _widget_defaults(cls, root):
        font = cls.font_spec(cls.FONT)
        options = {
            "*Frame.background": cls.BG,
            "*Toplevel.background": cls.BG,
            "*Canvas.background": cls.BG,
            "*Canvas.highlightThickness": 0,

            "*Label.background": cls.BG,
            "*Label.foreground": cls.TEXT,
            "*Label.font": font,

            "*Button.background": cls.SURFACE_ALT,
            "*Button.foreground": cls.TEXT,
            "*Button.activeBackground": cls.BORDER,
            "*Button.activeForeground": cls.TEXT,
            "*Button.relief": "flat",
            "*Button.borderWidth": 0,
            "*Button.highlightThickness": 0,
            "*Button.padX": 12,
            "*Button.padY": 6,
            "*Button.cursor": "hand2",
            "*Button.font": font,

            # borderWidth is what gives an entry its inside padding, and the
            # highlight ring is what marks the box the cursor is in.
            "*Entry.background": cls.SURFACE,
            "*Entry.foreground": cls.TEXT,
            "*Entry.insertBackground": cls.ACCENT,
            "*Entry.selectBackground": cls.ACCENT,
            "*Entry.selectForeground": cls.ACCENT_TEXT,
            "*Entry.relief": "flat",
            "*Entry.borderWidth": 6,
            "*Entry.highlightThickness": 1,
            "*Entry.highlightBackground": cls.BORDER,
            "*Entry.highlightColor": cls.ACCENT,
            "*Entry.font": font,

            "*Text.background": cls.SURFACE,
            "*Text.foreground": cls.TEXT,
            "*Text.insertBackground": cls.ACCENT,
            "*Text.selectBackground": cls.ACCENT,
            "*Text.selectForeground": cls.ACCENT_TEXT,
            "*Text.relief": "flat",
            "*Text.borderWidth": 10,
            "*Text.highlightThickness": 1,
            "*Text.highlightBackground": cls.BORDER,
            "*Text.highlightColor": cls.BORDER,
            "*Text.font": cls.font_spec(cls.FONT_MONO),

            "*Listbox.background": cls.SURFACE,
            "*Listbox.foreground": cls.TEXT,
            "*Listbox.selectBackground": cls.ACCENT,
            "*Listbox.selectForeground": cls.ACCENT_TEXT,
            "*Listbox.relief": "flat",
            "*Listbox.borderWidth": 8,
            "*Listbox.highlightThickness": 1,
            "*Listbox.highlightBackground": cls.BORDER,
            "*Listbox.activeStyle": "none",
            "*Listbox.font": font,

            "*Checkbutton.background": cls.BG,
            "*Checkbutton.foreground": cls.TEXT,
            "*Checkbutton.activeBackground": cls.BG,
            "*Checkbutton.activeForeground": cls.TEXT,
            "*Checkbutton.selectColor": cls.SURFACE_ALT,
            "*Checkbutton.highlightThickness": 0,
            "*Checkbutton.cursor": "hand2",
            "*Checkbutton.font": font,

            "*Scrollbar.background": cls.SURFACE_ALT,
            "*Scrollbar.activeBackground": cls.BORDER,
            "*Scrollbar.troughColor": cls.BG,
            "*Scrollbar.relief": "flat",
            "*Scrollbar.borderWidth": 0,
            "*Scrollbar.highlightThickness": 0,
            "*Scrollbar.width": 12,

            # The list a combobox drops down is a plain Tk listbox.
            "*TCombobox*Listbox.background": cls.SURFACE,
            "*TCombobox*Listbox.foreground": cls.TEXT,
            "*TCombobox*Listbox.selectBackground": cls.ACCENT,
            "*TCombobox*Listbox.selectForeground": cls.ACCENT_TEXT,
            "*TCombobox*Listbox.font": font,
        }
        for pattern, value in options.items():
            root.option_add(pattern, value)

    # ---- ttk widgets ----
    @classmethod
    def _ttk_styles(cls, root):
        style = ttk.Style(root)
        # clam is the one built-in theme that lets every color be set.
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=cls.SURFACE,
            fieldbackground=cls.SURFACE,
            foreground=cls.TEXT,
            bordercolor=cls.BORDER,
            # clam draws the frame of the table from these, and lights them up
            # when it has focus - left alone that is a white box on a dark page.
            lightcolor=cls.BORDER,
            darkcolor=cls.BORDER,
            borderwidth=1,
            relief="flat",
            rowheight=26,
            font=cls.FONT,
        )
        style.map(
            "Treeview",
            background=[("selected", cls.ACCENT)],
            foreground=[("selected", cls.ACCENT_TEXT)],
            bordercolor=[("focus", cls.BORDER), ("!focus", cls.BORDER)],
            lightcolor=[("focus", cls.BORDER), ("!focus", cls.BORDER)],
            darkcolor=[("focus", cls.BORDER), ("!focus", cls.BORDER)],
        )
        style.configure(
            "Treeview.Heading",
            background=cls.SURFACE_ALT,
            foreground=cls.TEXT_MUTED,
            relief="flat",
            borderwidth=0,
            padding=(8, 6),
            font=cls.FONT_BOLD,
        )
        style.map(
            "Treeview.Heading",
            background=[("active", cls.BORDER)],
            foreground=[("active", cls.TEXT)],
        )

        style.configure(
            "TCombobox",
            fieldbackground=cls.SURFACE,
            background=cls.SURFACE_ALT,
            foreground=cls.TEXT,
            arrowcolor=cls.TEXT_MUTED,
            bordercolor=cls.BORDER,
            lightcolor=cls.BORDER,
            darkcolor=cls.BORDER,
            selectbackground=cls.SURFACE,
            selectforeground=cls.TEXT,
            padding=5,
        )
        style.map(
            "TCombobox",
            # The arrow button is drawn from `background`, and it only follows
            # the theme once every state names a color of its own.
            background=[("readonly", cls.SURFACE_ALT), ("active", cls.BORDER), ("!disabled", cls.SURFACE_ALT)],
            fieldbackground=[("readonly", cls.SURFACE), ("!disabled", cls.SURFACE)],
            foreground=[("readonly", cls.TEXT), ("!disabled", cls.TEXT)],
            arrowcolor=[("active", cls.ACCENT), ("!disabled", cls.TEXT_MUTED)],
            bordercolor=[("focus", cls.ACCENT), ("hover", cls.ACCENT), ("!disabled", cls.BORDER)],
            lightcolor=[("!disabled", cls.BORDER)],
            darkcolor=[("!disabled", cls.BORDER)],
        )

        for name in ("TProgressbar", "Horizontal.TProgressbar"):
            style.configure(
                name,
                troughcolor=cls.SURFACE,
                background=cls.ACCENT,
                bordercolor=cls.SURFACE,
                lightcolor=cls.ACCENT,
                darkcolor=cls.ACCENT,
                borderwidth=0,
                thickness=8,
            )

        for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            style.configure(
                name,
                background=cls.SURFACE_ALT,
                troughcolor=cls.BG,
                bordercolor=cls.BG,
                lightcolor=cls.SURFACE_ALT,
                darkcolor=cls.SURFACE_ALT,
                arrowcolor=cls.TEXT_MUTED,
                borderwidth=0,
            )
            style.map(name, background=[("active", cls.BORDER)])

    # ---- small building blocks ----
    @classmethod
    def title(cls, parent, text, **kwargs):
        return tk.Label(parent, text=text, font=cls.FONT_TITLE, **kwargs)

    @classmethod
    def heading(cls, parent, text, **kwargs):
        return tk.Label(parent, text=text, font=cls.FONT_HEADING, **kwargs)

    @classmethod
    def hint(cls, parent, text, **kwargs):
        """A quiet line of explanation under something louder."""
        return tk.Label(parent, text=text, fg=cls.TEXT_MUTED, font=cls.FONT_SMALL, **kwargs)

    @classmethod
    def separator(cls, parent):
        return tk.Frame(parent, height=1, bg=cls.BORDER)

    # ---- matplotlib ----
    @classmethod
    def style_figure(cls, figure, ax):
        """Paint a chart in the same colors as the window around it."""
        figure.patch.set_facecolor(cls.BG)
        ax.set_facecolor(cls.SURFACE)
        for spine in ax.spines.values():
            spine.set_color(cls.BORDER)
        ax.tick_params(colors=cls.TEXT_MUTED, labelsize=9)
        ax.xaxis.label.set_color(cls.TEXT_MUTED)
        ax.yaxis.label.set_color(cls.TEXT_MUTED)
        ax.title.set_color(cls.TEXT)
        ax.grid(True, color=cls.BORDER, linewidth=0.6, alpha=0.6)
