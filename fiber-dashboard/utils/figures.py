import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import copy

from config import COLORS, PLOTLY_TEMPLATE, MATERIAL_COLORS


def apply_theme(fig: go.Figure, title: str = None) -> go.Figure:
    """Apply the light dashboard theme to any figure."""
    template = copy.deepcopy(PLOTLY_TEMPLATE["layout"])
    fig.update_layout(**template)
    if title:
        fig.update_layout(
            title={"text": title, "font": {"size": 14, "color": COLORS["text_primary"]}, "x": 0.01}
        )
    return fig


def histogram(df: pd.DataFrame, col: str, title: str, xlabel: str,
              color: str = None, nbins: int = 40) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df[col].dropna(),
        nbinsx=nbins,
        marker_color=color or COLORS["primary"],
        opacity=0.80,
        name=xlabel,
    ))
    fig.update_layout(bargap=0.05, xaxis_title=xlabel, yaxis_title="Fréquence")
    return apply_theme(fig, title)


def boxplot_by_group(df: pd.DataFrame, value_col: str, group_col: str,
                     title: str, ylabel: str) -> go.Figure:
    fig = go.Figure()
    for group in sorted(df[group_col].dropna().unique()):
        subset = df[df[group_col] == group][value_col].dropna()
        color = MATERIAL_COLORS.get(group, COLORS["primary"])
        fig.add_trace(go.Box(
            y=subset,
            name=group,
            marker_color=color,
            line_color=color,
            fillcolor=color + "26",
            boxmean="sd",
            line_width=1.8,
        ))
    fig.update_layout(yaxis_title=ylabel, showlegend=False, boxgap=0.3)
    return apply_theme(fig, title)


def scatter(df: pd.DataFrame, x_col: str, y_col: str, color_col: str = None,
            size_col: str = None, title: str = "", xlabel: str = None,
            ylabel: str = None) -> go.Figure:
    kwargs = dict(x=x_col, y=y_col, title="")
    if color_col and color_col in df.columns:
        kwargs["color"] = color_col
        kwargs["color_discrete_map"] = MATERIAL_COLORS
    if size_col and size_col in df.columns:
        kwargs["size"] = size_col
        kwargs["size_max"] = 18

    fig = px.scatter(df, **kwargs)
    fig.update_traces(marker=dict(opacity=0.80, line=dict(width=0.5, color="white"), size=8))
    fig.update_layout(
        xaxis_title=xlabel or x_col,
        yaxis_title=ylabel or y_col,
    )
    return apply_theme(fig, title)


def heatmap_corr(corr_matrix: pd.DataFrame, title: str) -> go.Figure:
    cols = corr_matrix.columns.tolist()
    fig = go.Figure(go.Heatmap(
        z=corr_matrix.values,
        x=cols,
        y=cols,
        colorscale=[
            [0.0, "#EF4444"],
            [0.5, "#FFFFFF"],
            [1.0, "#2563EB"],
        ],
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}",
        textfont={"size": 9, "color": "#0F172A"},
        hoverongaps=False,
        colorbar=dict(
            title="r",
            tickfont=dict(color=COLORS["text_secondary"]),
            tickvals=[-1, -0.5, 0, 0.5, 1],
        ),
    ))
    fig.update_layout(
        xaxis=dict(tickangle=-45, tickfont=dict(size=10, color=COLORS["text_primary"])),
        yaxis=dict(tickfont=dict(size=10, color=COLORS["text_primary"])),
    )
    return apply_theme(fig, title)


def heatmap_2d(z_matrix, x_labels, y_labels, title: str,
               xlabel: str = "", ylabel: str = "") -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=z_matrix,
        x=x_labels,
        y=y_labels,
        colorscale="Blues",
        text=np.round(z_matrix, 1) if z_matrix is not None else None,
        texttemplate="%{text}",
        textfont={"size": 9, "color": "#0F172A"},
        colorbar=dict(tickfont=dict(color=COLORS["text_secondary"])),
    ))
    fig.update_layout(xaxis_title=xlabel, yaxis_title=ylabel)
    return apply_theme(fig, title)


def bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str,
              color_col: str = None, xlabel: str = None, ylabel: str = None,
              orientation: str = "v") -> go.Figure:
    kwargs = dict(x=x_col, y=y_col, title="")
    if color_col and color_col in df.columns:
        kwargs["color"] = color_col
        kwargs["color_discrete_map"] = MATERIAL_COLORS
    fig = px.bar(df, **kwargs, orientation=orientation)
    fig.update_layout(xaxis_title=xlabel or x_col, yaxis_title=ylabel or y_col, bargap=0.25)
    fig.update_traces(marker_opacity=0.88)
    return apply_theme(fig, title)


def line_chart(df: pd.DataFrame, x_col: str, y_col: str, color_col: str = None,
               title: str = "", xlabel: str = None, ylabel: str = None) -> go.Figure:
    kwargs = dict(x=x_col, y=y_col, title="")
    if color_col and color_col in df.columns:
        kwargs["color"] = color_col
        kwargs["color_discrete_map"] = MATERIAL_COLORS
    fig = px.line(df, **kwargs, markers=True)
    fig.update_traces(line_width=2.2, marker_size=6, marker_line_width=1.5,
                      marker_line_color="white")
    fig.update_layout(xaxis_title=xlabel or x_col, yaxis_title=ylabel or y_col)
    return apply_theme(fig, title)


def pie_chart(labels, values, title: str) -> go.Figure:
    STATUS_COLORS = {
        "completed":  COLORS["success"],
        "in_progress": COLORS["warning"],
        "failed":     COLORS["danger"],
    }
    colors = [STATUS_COLORS.get(label, COLORS["primary"]) for label in labels]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textfont=dict(color=COLORS["text_primary"], size=12),
    ))
    fig.update_layout(showlegend=True)
    return apply_theme(fig, title)


def empty_figure(message: str = "Aucune donnée disponible") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=COLORS["text_secondary"], size=14),
    )
    return apply_theme(fig)


# ─── Scientific / publication style ─────────────────────────────────────────

_SCI_LAYOUT = {
    "paper_bgcolor": "white",
    "plot_bgcolor":  "white",
    "font": {"color": "#1a1a2e", "family": "Inter, Arial, sans-serif", "size": 11},
    "xaxis": {
        "gridcolor": "#e8eef6",
        "linecolor": "#CBD5E1",
        "tickcolor": "#64748B",
        "mirror":    True,
        "showline":  True,
        "ticks":     "outside",
        "gridwidth": 0.5,
    },
    "yaxis": {
        "gridcolor": "#e8eef6",
        "linecolor": "#CBD5E1",
        "tickcolor": "#64748B",
        "mirror":    True,
        "showline":  True,
        "ticks":     "outside",
        "gridwidth": 0.5,
    },
    "legend": {
        "bgcolor":     "rgba(255,255,255,0.95)",
        "bordercolor": "#E2E8F0",
        "borderwidth": 1,
        "font": {"size": 10, "color": "#1a1a2e"},
    },
    "margin": {"t": 12, "r": 20, "b": 55, "l": 65},
    "hoverlabel": {
        "bgcolor":    "white",
        "bordercolor": "#2563EB",
        "font": {"color": "#0F172A"},
    },
}

_SCI_PALETTE = ["#2563EB", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#0EA5E9"]
_SCI_SYMBOLS = ["circle", "square", "diamond", "cross", "triangle-up", "star"]


def apply_scientific_theme(fig: go.Figure, xlabel: str = "", ylabel: str = "") -> go.Figure:
    """White-background theme — style publication."""
    layout = copy.deepcopy(_SCI_LAYOUT)
    fig.update_layout(**layout)
    if xlabel:
        fig.update_layout(xaxis_title={"text": xlabel, "font": {"size": 12}})
    if ylabel:
        fig.update_layout(yaxis_title={"text": ylabel, "font": {"size": 12}})
    return fig


def kde_values(data: np.ndarray, n_points: int = 300):
    """Gaussian KDE with Silverman's rule of thumb. Returns (x, y) arrays."""
    arr = np.asarray(data, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 3:
        return np.array([]), np.array([])
    h = 1.06 * np.std(arr) * len(arr) ** (-0.2)
    if h <= 0:
        h = 1e-6
    x = np.linspace(arr.min() - 2 * h, arr.max() + 2 * h, n_points)
    z = (x[:, None] - arr[None, :]) / h
    y = np.sum(np.exp(-0.5 * z ** 2), axis=1) / (len(arr) * h * np.sqrt(2 * np.pi))
    return x, y


def pdf_overlay(data_by_group: dict, xlabel: str = "", mean_line: bool = True) -> go.Figure:
    """Courbes KDE par groupe. data_by_group = {label: array}."""
    fig = go.Figure()
    for i, (label, data) in enumerate(data_by_group.items()):
        arr = np.asarray(data, dtype=float)
        arr = arr[~np.isnan(arr)]
        if len(arr) < 3:
            continue
        color = MATERIAL_COLORS.get(label, _SCI_PALETTE[i % len(_SCI_PALETTE)])
        x_kde, y_kde = kde_values(arr)
        fig.add_trace(go.Scatter(
            x=x_kde, y=y_kde,
            mode="lines",
            name=label,
            line=dict(color=color, width=2.2),
            fill="tozeroy",
            fillcolor=color + "14",
        ))
        if mean_line:
            mean_val = float(arr.mean())
            fig.add_vline(
                x=mean_val,
                line=dict(color=color, width=1.4, dash="dot"),
                annotation_text=f"μ={mean_val:.1f}",
                annotation_font=dict(size=8, color=color),
                annotation_position="top right",
            )
    return apply_scientific_theme(fig, xlabel=xlabel, ylabel="Densité de probabilité")


def pole_figure_pub(df: pd.DataFrame, theta_col: str, psi_col: str,
                    color_col: str = None, size_col: str = None) -> go.Figure:
    """Pole figure stéréographique : r = θ, angle = ψ, couleurs par groupe."""
    fig = go.Figure()
    groups = (
        sorted(df[color_col].dropna().unique(), key=str)
        if (color_col and color_col in df.columns)
        else [None]
    )

    for i, group in enumerate(groups):
        sub = df if group is None else df[df[color_col] == group]
        r_vals = sub[theta_col].dropna().values
        theta_vals = sub[psi_col].dropna().values
        color = MATERIAL_COLORS.get(str(group), _SCI_PALETTE[i % len(_SCI_PALETTE)])

        sizes = None
        if size_col and size_col in df.columns:
            raw = sub.loc[sub[theta_col].notna(), size_col].values.astype(float)
            if len(raw) > 0 and raw.max() > raw.min():
                sizes = (3 + 9 * (raw - raw.min()) / (raw.max() - raw.min())).clip(3, 12).tolist()

        fig.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=theta_vals,
            mode="markers",
            name=str(group) if group is not None else "Fibres",
            marker=dict(
                color=color,
                size=sizes if sizes is not None else 4,
                opacity=0.55,
                line=dict(width=0),
            ),
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="#F8FAFD",
            radialaxis=dict(
                color="#64748B",
                gridcolor="#E2E8F0",
                tickfont=dict(size=9, color="#64748B"),
                range=[0, 90],
                dtick=30,
                title=dict(text="θ (°)", font=dict(size=10, color="#64748B")),
                linecolor="#CBD5E1",
            ),
            angularaxis=dict(
                color="#64748B",
                gridcolor="#E2E8F0",
                tickfont=dict(size=9, color="#64748B"),
                direction="clockwise",
                dtick=45,
                linecolor="#CBD5E1",
            ),
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0F172A", family="Inter, system-ui, sans-serif"),
        legend=dict(
            font=dict(size=10, color="#0F172A"),
            itemsizing="constant",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
        ),
        margin=dict(t=20, r=20, b=20, l=20),
    )
    return fig
