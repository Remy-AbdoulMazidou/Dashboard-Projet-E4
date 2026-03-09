import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DATA_FILES = {
    "samples":          os.path.join(DATA_DIR, "samples.csv"),
    "fibers":           os.path.join(DATA_DIR, "fibers.csv"),
    "contacts":         os.path.join(DATA_DIR, "contacts.csv"),
    "parameter_sweep":  os.path.join(DATA_DIR, "parameter_sweep.csv"),
    "robustness":       os.path.join(DATA_DIR, "robustness.csv"),
    "acoustic_thermal": os.path.join(DATA_DIR, "acoustic_thermal.csv"),
    "quality_log":      os.path.join(DATA_DIR, "quality_log.csv"),
}

# ── Palette principale (thème clair professionnel) ───────────────────────────
COLORS = {
    "primary":          "#2563EB",   # bleu vif principal
    "primary_light":    "#EFF6FF",   # fond bleu très léger
    "primary_mid":      "#BFDBFE",   # bordure bleue légère
    "accent":           "#0EA5E9",   # bleu ciel secondaire
    "success":          "#10B981",   # vert émeraude
    "warning":          "#F59E0B",   # ambre
    "danger":           "#EF4444",   # rouge
    "neutral":          "#64748B",   # ardoise

    # Backgrounds
    "bg_page":          "#F1F5F9",   # fond de page (gris-bleu clair)
    "bg_card":          "#FFFFFF",   # fond des cartes
    "bg_sidebar":       "#1E2D40",   # sidebar marine foncée
    "bg_input":         "#FFFFFF",   # fond des inputs

    # Borders
    "border":           "#E2E8F0",   # bordure légère
    "border_strong":    "#CBD5E1",   # bordure plus visible

    # Text
    "text_primary":     "#0F172A",   # texte foncé principal
    "text_secondary":   "#64748B",   # texte secondaire
    "text_muted":       "#94A3B8",   # texte atténué
    "text_sidebar":     "#94A3B8",   # texte sidebar
}

# ── Couleurs par matériau ────────────────────────────────────────────────────
MATERIAL_COLORS = {
    "Nylon":        "#2563EB",   # bleu
    "Carbone":      "#EF4444",   # rouge
    "Verre":        "#10B981",   # vert émeraude
    "Cuivre":       "#F59E0B",   # ambre
    "PET recyclé":  "#8B5CF6",   # violet
    "Chanvre":      "#059669",   # vert foncé
}

# ── Template Plotly (thème clair) ────────────────────────────────────────────
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor":  "#F8FAFD",
        "font": {
            "color":  "#0F172A",
            "family": "Inter, system-ui, sans-serif",
            "size":   12,
        },
        "colorway": list(MATERIAL_COLORS.values()),
        "xaxis": {
            "gridcolor":     "#E8EEF6",
            "linecolor":     "#CBD5E1",
            "tickcolor":     "#64748B",
            "zerolinecolor": "#E2E8F0",
        },
        "yaxis": {
            "gridcolor":     "#E8EEF6",
            "linecolor":     "#CBD5E1",
            "tickcolor":     "#64748B",
            "zerolinecolor": "#E2E8F0",
        },
        "legend": {
            "bgcolor":     "rgba(255,255,255,0.95)",
            "bordercolor": "#E2E8F0",
            "borderwidth": 1,
        },
        "margin": {"t": 40, "r": 20, "b": 40, "l": 55},
        "hoverlabel": {
            "bgcolor":    "#FFFFFF",
            "bordercolor": "#2563EB",
            "font": {"color": "#0F172A"},
        },
    }
}

MATERIALS = ["Nylon", "Carbone", "Verre", "Cuivre", "PET recyclé", "Chanvre"]
BATCHES   = ["LOT-A", "LOT-B", "LOT-C"]
STATUSES  = ["completed", "in_progress", "failed"]

TABLE_STYLE = {
    "style_header": {
        "backgroundColor": "#F8FAFC",
        "color":           "#0F172A",
        "fontWeight":      "600",
        "borderBottom":    "2px solid #E2E8F0",
        "fontFamily":      "Inter, system-ui, sans-serif",
        "fontSize":        "12px",
        "padding":         "10px 14px",
    },
    "style_cell": {
        "backgroundColor": "#FFFFFF",
        "color":           "#0F172A",
        "borderBottom":    "1px solid #E2E8F0",
        "fontFamily":      "Inter, system-ui, sans-serif",
        "fontSize":        "12px",
        "padding":         "9px 14px",
    },
    "style_data_conditional": [
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "#F8FAFC",
        }
    ],
}

APP_TITLE    = "FiberScope"
APP_SUBTITLE = "MSME — UMR 8208 CNRS · Université Gustave Eiffel"
PORT  = int(os.environ.get("PORT", 8050))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
