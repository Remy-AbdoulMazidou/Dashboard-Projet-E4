import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from config import PLOT_LAYOUT, apply_grid, mat_color

BASE = os.path.dirname(__file__)

def _load(filename):
    path = os.path.join(BASE, "data", filename)
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

# chargement des données brutes
samples  = _load("samples.csv")
fibers   = _load("fibers.csv")
contacts = _load("contacts.csv")
acoustic = _load("acoustic_thermal.csv")

def _has(df, *cols):
    return all(c in df.columns for c in cols)

# fusion des colonnes material et batch dans les dataframes dépendants
if _has(samples, "sample_id", "material", "batch"):
    _meta = samples[["sample_id", "material", "batch"]]
    for df_name, df_obj in [("fibers", fibers), ("contacts", contacts), ("acoustic", acoustic)]:
        if not df_obj.empty and "sample_id" in df_obj.columns:
            if df_name == "fibers":
                fibers   = df_obj.merge(_meta, on="sample_id", how="left")
            elif df_name == "contacts":
                contacts = df_obj.merge(_meta, on="sample_id", how="left")
            else:
                acoustic = df_obj.merge(_meta, on="sample_id", how="left")

MATERIALS = sorted(samples["material"].unique().tolist()) if _has(samples, "material") else []

FREQ_VALS = [250, 500, 1000, 2000, 4000]
FREQ_COLS = ["absorption_250hz", "absorption_500hz", "absorption_1000hz",
             "absorption_2000hz", "absorption_4000hz"]

def _empty_fig(msg="Données non disponibles"):
    fig = go.Figure()
    fig.update_layout(
        **PLOT_LAYOUT,
        annotations=[dict(
            text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=13, color="#94A3B8"),
        )],
    )
    return apply_grid(fig)

def _filter_ids(mat_list, bat_sel):
    sel = mat_list if mat_list is not None else MATERIALS
    if samples.empty:
        return [], pd.DataFrame()
    mask = samples["material"].isin(sel)
    if bat_sel:
        mask &= samples["batch"].isin(bat_sel)
    sf = samples[mask]
    return sf["sample_id"].tolist(), sf

def _sub(df, id_list):
    if df.empty or "sample_id" not in df.columns:
        return pd.DataFrame()
    return df[df["sample_id"].isin(id_list)]

def _boxplot(df, y_col, y_title="", unit=""):
    if df.empty or not _has(df, y_col, "material"):
        return _empty_fig(f"Colonne '{y_col}' non disponible dans les données")
    u = f" {unit}" if unit else ""
    fig = go.Figure()
    for i, mat in enumerate(sorted(df["material"].dropna().unique())):
        vals = df[df["material"] == mat][y_col].dropna()
        if vals.empty:
            continue
        q1_v   = vals.quantile(0.25)
        med_v  = vals.median()
        q3_v   = vals.quantile(0.75)
        iqr_v  = q3_v - q1_v
        low_v  = max(vals.min(), q1_v - 1.5 * iqr_v)
        high_v = min(vals.max(), q3_v + 1.5 * iqr_v)
        n_v    = len(vals)

        tooltip = (
            f"<b>{mat}</b><br>"
            f"Valeur typique : <b>{med_v:.2f}{u}</b><br>"
            f"La moitié des fibres : {q1_v:.2f} – {q3_v:.2f}{u}<br>"
            f"Plage habituelle : {low_v:.2f} – {high_v:.2f}{u}<br>"
            f"Fibres mesurées : {n_v:,}"
            "<extra></extra>"
        )

        fig.add_trace(go.Box(
            y=vals, name=mat,
            marker_color=mat_color(mat, i),
            boxpoints=False,
            line_width=1.8,
            hoverinfo="none",
        ))

        for y_pos in [low_v, q1_v, med_v, q3_v, high_v]:
            fig.add_trace(go.Scatter(
                x=[mat], y=[y_pos],
                mode="markers",
                showlegend=False,
                marker=dict(size=14, opacity=0),
                hovertemplate=tooltip,
            ))

    fig.update_layout(**PLOT_LAYOUT, yaxis_title=y_title, showlegend=False)
    return apply_grid(fig)
