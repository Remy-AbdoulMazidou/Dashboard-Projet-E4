from dash import dcc, html
from config import COLORS, MATERIALS, BATCHES, STATUSES


def _label(text: str) -> html.Label:
    return html.Label(text, style={"color": COLORS["text_secondary"], "fontSize": "11px",
                                    "fontWeight": "600", "marginBottom": "4px",
                                    "textTransform": "uppercase", "letterSpacing": "0.05em"})


def _dropdown(dropdown_id: str, options: list, placeholder: str, multi: bool = True) -> dcc.Dropdown:
    return dcc.Dropdown(
        id=dropdown_id,
        options=[{"label": o, "value": o} for o in options],
        placeholder=placeholder,
        multi=multi,
        style={"fontSize": "13px"},
        className="dash-dropdown-dark",
    )


def material_filter(dropdown_id: str = "filter-material") -> html.Div:
    return html.Div([
        _label("Matériau"),
        _dropdown(dropdown_id, MATERIALS, "Tous les matériaux"),
    ], className="filter-group")


def batch_filter(dropdown_id: str = "filter-batch") -> html.Div:
    return html.Div([
        _label("Lot"),
        _dropdown(dropdown_id, BATCHES, "Tous les lots"),
    ], className="filter-group")


def status_filter(dropdown_id: str = "filter-status") -> html.Div:
    return html.Div([
        _label("Statut"),
        _dropdown(dropdown_id, STATUSES, "Tous les statuts"),
    ], className="filter-group")


def sample_selector(dropdown_id: str, sample_ids: list, multi: bool = False) -> html.Div:
    return html.Div([
        _label("Échantillon"),
        dcc.Dropdown(
            id=dropdown_id,
            options=[{"label": sid, "value": sid} for sid in sample_ids],
            value=sample_ids[0] if sample_ids else None,
            multi=multi,
            clearable=False,
            style={"fontSize": "13px"},
            className="dash-dropdown-dark",
        ),
    ], className="filter-group")


def filter_bar(*filter_components) -> html.Div:
    return html.Div(
        list(filter_components),
        className="filter-bar",
    )
