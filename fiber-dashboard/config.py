import plotly.graph_objects as go

# palette de couleurs par matériau
MAT_COLORS = {
    "Nylon":       "#3B82F6",
    "Carbone":     "#EF4444",
    "Verre":       "#22C55E",
    "Cuivre":      "#F59E0B",
    "PET recyclé": "#8B5CF6",
    "Chanvre":     "#10B981",
}
FALLBACK = ["#3B82F6","#EF4444","#22C55E","#F59E0B","#8B5CF6","#10B981",
            "#F97316","#06B6D4","#EC4899","#84CC16"]

PALETTE = FALLBACK

def mat_color(mat, i=0):
    return MAT_COLORS.get(mat, FALLBACK[i % len(FALLBACK)])

# couleurs et labels des onglets
TABS = {
    "overview":   {"bg": "#1D4ED8", "light": "#EFF6FF", "border": "#BFDBFE", "label": "Vue d'ensemble"},
    "morphology": {"bg": "#6D28D9", "light": "#F5F3FF", "border": "#DDD6FE", "label": "Morphologie des fibres"},
    "contacts":   {"bg": "#047857", "light": "#ECFDF5", "border": "#A7F3D0", "label": "Liaisons inter-fibres"},
    "acoustics":  {"bg": "#B45309", "light": "#FFFBEB", "border": "#FDE68A", "label": "Propriétés acoustiques"},
    "correlations": {"bg": "#0F766E", "light": "#F0FDFA", "border": "#99F6E4", "label": "Comparaison"},
}

# style de base des onglets
BASE_TAB = {
    "fontFamily": "Inter, system-ui, sans-serif",
    "fontWeight": 600,
    "fontSize":   "13px",
    "padding":    "11px 22px",
    "borderRadius": "10px 10px 0 0",
    "backgroundColor": "#F1F5F9",
    "color":      "#64748B",
    "border":     "1px solid #E2E8F0",
    "borderBottom": "none",
    "marginRight": "4px",
    "cursor":     "pointer",
}

def sel_tab(key):
    return {**BASE_TAB,
            "backgroundColor": TABS[key]["bg"],
            "color":           "white",
            "border":          f"1px solid {TABS[key]['bg']}",
            "boxShadow":       f"0 -3px 0 0 {TABS[key]['bg']} inset"}

# configuration des graphiques Plotly
PLOT_CONFIG = {
    "displayModeBar": "hover",
    "responsive": True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

PLOT_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#F8FAFC",
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#334155"),
    margin=dict(l=70, r=24, t=54, b=60),
    hoverlabel=dict(bgcolor="#1E293B", bordercolor="#0F172A", font_size=12, font_color="white"),
)

AXIS_STYLE = dict(
    showgrid=True,  gridcolor="#94A3B8",  gridwidth=1,
    zeroline=True,  zerolinecolor="#64748B", zerolinewidth=1.5,
    showline=True,  linecolor="#64748B",  linewidth=1,
    title_font=dict(size=13, color="#1E293B", family="Inter, system-ui, sans-serif"),
    tickfont=dict(size=11, color="#334155"),
)

LEGEND_STYLE = dict(
    bgcolor="rgba(248,250,252,0.95)",
    bordercolor="#CBD5E1",
    borderwidth=1,
    font=dict(size=11, color="#334155"),
    itemclick="toggle",
    itemdoubleclick="toggleothers",
    tracegroupgap=3,
)

def apply_grid(fig):
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

def _legend_h():
    return dict(**LEGEND_STYLE, orientation="h", y=1.22, x=0)

def _legend_v():
    return dict(**LEGEND_STYLE, orientation="v", x=1.02, y=1)
