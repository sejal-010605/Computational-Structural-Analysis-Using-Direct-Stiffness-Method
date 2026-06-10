import customtkinter as ctk

#  Design tokens
class Theme:
    BG = "#F5F6F8"            
    SURFACE = "#FFFFFF"       
    ACCENT = "#3B82F6"        
    ACCENT_HOVER = "#2F6FE0"
    ACCENT_SOFT = "#60A5FA"   
    TEXT = "#0F172A"          
    TEXT_MUTED = "#64748B"    
    BORDER = "#E2E8F0"        
    SUCCESS = "#16A34A"
    DANGER = "#DC2626"
    TABLE_STRIPE = "#F8FAFC"
    BADGE_BG = "#EAF2FE"

    FONT = "Inter"
    FONT_FALLBACK = "Segoe UI"


def font(size, weight="normal"):
    family = Theme.FONT
    try:
        return ctk.CTkFont(family=family, size=size, weight=weight)
    except Exception:  # noqa: BLE001
        return ctk.CTkFont(family=Theme.FONT_FALLBACK, size=size, weight=weight)



#  Card
class Card(ctk.CTkFrame):
    """A white rounded surface with a subtle border."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", Theme.SURFACE)
        kwargs.setdefault("corner_radius", 16)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Theme.BORDER)
        super().__init__(master, **kwargs)


class StatCard(Card):
    """A compact metric card: small label on top, large value below."""

    def __init__(self, master, label, value, accent=False, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            self, text=label.upper(), font=font(11, "bold"),
            text_color=Theme.ACCENT if accent else Theme.TEXT_MUTED,
            anchor="w",
        )
        self.label.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 0))

        self.value = ctk.CTkLabel(
            self, text=str(value), font=font(28, "bold"),
            text_color=Theme.TEXT, anchor="w",
        )
        self.value.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 16))

    def set_value(self, value):
        self.value.configure(text=str(value))


class InfoRow(ctk.CTkFrame):
    """A label : value row used inside the analysis summary card."""

    def __init__(self, master, label, value, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text=label, font=font(13), text_color=Theme.TEXT_MUTED, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.value_lbl = ctk.CTkLabel(
            self, text=str(value), font=font(13, "bold"),
            text_color=Theme.TEXT, anchor="e",
        )
        self.value_lbl.grid(row=0, column=1, sticky="e")

    def set_value(self, value, color=None):
        self.value_lbl.configure(text=str(value))
        if color:
            self.value_lbl.configure(text_color=color)



#  DataFrame table
class DataTable(ctk.CTkScrollableFrame):
    """Render a pandas DataFrame as a clean, striped, scrollable table."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", Theme.SURFACE)
        kwargs.setdefault("corner_radius", 14)
        super().__init__(master, **kwargs)
        self._empty_label = None

    def render(self, df, float_cols=None, decimals=4):
        for child in self.winfo_children():
            child.destroy()

        if df is None or df.empty:
            self._empty_label = ctk.CTkLabel(
                self, text="No data available for this view.",
                font=font(13), text_color=Theme.TEXT_MUTED,
            )
            self._empty_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return

        float_cols = float_cols or []
        columns = list(df.columns)
        for c in range(len(columns)):
            self.grid_columnconfigure(c, weight=1, uniform="cols")

        # Header
        for c, col in enumerate(columns):
            cell = ctk.CTkLabel(
                self, text=str(col), font=font(12, "bold"),
                text_color=Theme.TEXT, anchor="w",
            )
            cell.grid(row=0, column=c, sticky="nsew", padx=14, pady=(10, 8))

        # Header divider
        divider = ctk.CTkFrame(self, height=1, fg_color=Theme.BORDER)
        divider.grid(row=1, column=0, columnspan=len(columns), sticky="ew", padx=8)

        # Body
        for r, (_, row) in enumerate(df.iterrows()):
            stripe = Theme.TABLE_STRIPE if r % 2 else Theme.SURFACE
            for c, col in enumerate(columns):
                val = row[col]
                if isinstance(val, float) or col in float_cols:
                    try:
                        text = f"{float(val):.{decimals}f}"
                    except (ValueError, TypeError):
                        text = str(val)
                else:
                    text = str(val)

                cell = ctk.CTkLabel(
                    self, text=text, font=font(12),
                    text_color=Theme.TEXT, anchor="w", fg_color=stripe,
                    corner_radius=0,
                )
                cell.grid(row=r + 2, column=c, sticky="nsew", padx=14, pady=6)



#  Badge
class Badge(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        kwargs.setdefault("fg_color", Theme.BADGE_BG)
        kwargs.setdefault("text_color", Theme.ACCENT)
        kwargs.setdefault("corner_radius", 20)
        kwargs.setdefault("font", font(12, "bold"))
        super().__init__(master, text=f"  {text}  ", height=30, **kwargs)
