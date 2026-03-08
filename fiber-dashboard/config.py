import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DATA_FILES = {
    "samples": os.path.join(DATA_DIR, "samples.csv"),
    "fibers": os.path.join(DATA_DIR, "fibers.csv"),
    "contacts": os.path.join(DATA_DIR, "contacts.csv"),
    "parameter_sweep": os.path.join(DATA_DIR, "parameter_sweep.csv"),
    "robustness": os.path.join(DATA_DIR, "robustness.csv"),
    "acoustic_thermal": os.path.join(DATA_DIR, "acoustic_thermal.csv"),
    "quality_log": os.path.join(DATA_DIR, "quality_log.csv"),
}

COLORS = {
    "primary": "#2E86AB",
    "accent": "#F24236",
    "success": "#2ECC71",
    "warning": "#F39C12",
    "neutral": "#8B9BB4",
    "bg_dark": "#0F1117",
    "bg_card": "#1A1D2E",
    "bg_sidebar": "#141623",
    "border": "#2A2D3E",
    "text_primary": "#E8EAF0",
    "text_secondary": "#8B9BB4",
}

MATERIAL_COLORS = {
    "Nylon": "#2E86AB",
    "Carbone": "#F24236",
    "Verre": "#2ECC71",
    "Cuivre": "#E67E22",
    "PET recyclé": "#9B59B6",
    "Chanvre": "#27AE60",
}

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": COLORS["bg_card"],
        "plot_bgcolor": COLORS["bg_dark"],
        "font": {"color": COLORS["text_primary"], "family": "Inter, system-ui, sans-serif", "size": 12},
        "colorway": list(MATERIAL_COLORS.values()),
        "xaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickcolor": COLORS["text_secondary"],
        },
        "yaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickcolor": COLORS["text_secondary"],
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": COLORS["border"],
        },
        "margin": {"t": 40, "r": 20, "b": 40, "l": 50},
        "hoverlabel": {
            "bgcolor": COLORS["bg_card"],
            "bordercolor": COLORS["primary"],
            "font": {"color": COLORS["text_primary"]},
        },
    }
}

MATERIALS = ["Nylon", "Carbone", "Verre", "Cuivre", "PET recyclé", "Chanvre"]
BATCHES = ["LOT-A", "LOT-B", "LOT-C"]
STATUSES = ["completed", "in_progress", "failed"]

TABLE_STYLE = {
    "style_header": {
        "backgroundColor": COLORS["bg_sidebar"],
        "color": COLORS["text_primary"],
        "fontWeight": "600",
        "borderBottom": f"1px solid {COLORS['primary']}",
        "fontFamily": "Inter, system-ui, sans-serif",
        "fontSize": "13px",
    },
    "style_cell": {
        "backgroundColor": COLORS["bg_card"],
        "color": COLORS["text_primary"],
        "borderBottom": f"1px solid {COLORS['border']}",
        "fontFamily": "Inter, system-ui, sans-serif",
        "fontSize": "12px",
        "padding": "8px 12px",
    },
    "style_data_conditional": [
        {
            "if": {"row_index": "odd"},
            "backgroundColor": COLORS["bg_dark"],
        }
    ],
}

APP_TITLE = "FiberScope"
APP_SUBTITLE = "MSME — UMR 8208 CNRS · Université Gustave Eiffel"
PORT = int(os.environ.get("PORT", 8050))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
