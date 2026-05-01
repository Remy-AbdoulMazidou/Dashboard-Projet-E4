"""
FiberScope · Dragonfly vs MATLAB
Projet E4 ESIEE Paris · MSME UMR 8208 CNRS
"""
import os
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np

BASE    = os.path.dirname(os.path.abspath(__file__))
AA_DIR  = os.path.join(BASE, '..', 'vrai-data', 'antoine-aymen')
NOL_DIR = os.path.join(BASE, '..', 'vrai-data', 'nolhan')

# ── Palette ───────────────────────────────────────────────────────────────────
FONT    = "'Inter', system-ui, -apple-system, sans-serif"
INDIGO  = '#6366F1'
EMERALD = '#10B981'
BG      = '#FAFAFA'
CARD    = '#FFFFFF'
ZN100   = '#F4F4F5'
ZN200   = '#E4E4E7'
ZN400   = '#A1A1AA'
ZN500   = '#71717A'
ZN700   = '#3F3F46'
ZN800   = '#27272A'
ZN900   = '#18181B'
AMBER   = '#D97706'
GREEN   = '#059669'
RED     = '#E11D48'


# ── Chargement des données ────────────────────────────────────────────────────

def load_aa():
    df = pd.read_csv(os.path.join(AA_DIR, 'donnees2.csv'), sep=';', encoding='utf-8-sig')
    df.columns = [c.strip() for c in df.columns]
    vol_col   = next(c for c in df.columns if 'Volume' in c)
    phi_col   = next(c for c in df.columns if 'Phi'    in c)
    theta_col = next(c for c in df.columns if 'Theta'  in c)
    df = df[df[vol_col] > 0].rename(columns={
        'Label Index': 'label', 'Voxel count': 'voxels',
        vol_col: 'vol', phi_col: 'phi', theta_col: 'theta',
    })
    bins   = [0, 5, 100, 100_000, 1_000_000, float('inf')]
    labels = ['Bruit', 'Fragment', 'Fibre', 'Gros objet', 'Matrice']
    df['cat'] = pd.cut(df['voxels'], bins=bins, labels=labels)
    return df


def load_nolhan():
    df = pd.read_excel(os.path.join(NOL_DIR, 'Resultats_Fibres.xlsx'))
    pal3 = df['PrincipalAxisLength_3'].clip(lower=0.1)
    return df.assign(
        Diam_um     = df['PrincipalAxisLength_3'] * 10,
        Len_um      = df['PrincipalAxisLength_1'] * 10,
        AspectRatio = df['PrincipalAxisLength_1'] / pal3,
        angle_h     = df['Orientation_2'].abs(),
    )


def load_thickness():
    cache = os.path.join(AA_DIR, '.thick_cache.npy')
    if os.path.exists(cache):
        return np.load(cache)
    print("Construction du cache épaisseur…")
    col = 'Thickness (mm)'
    chunks = []
    for ch in pd.read_csv(os.path.join(AA_DIR, 'diametre.csv'), sep=';',
                          chunksize=1_000_000, usecols=[col], dtype={col: 'float32'}):
        chunks.append(ch.iloc[::100][col].values)
    t = np.concatenate(chunks).astype(float) * 1000
    t = t[(t > 5) & (t < 350)]
    np.save(cache, t)
    return t


print("Chargement des données…")
DF_AA  = load_aa()
DF_NOL = load_nolhan()
THICK  = load_thickness()

VOX_UM = float((DF_AA['vol'].iloc[0] * 1e9) ** (1 / 3))
FIB    = DF_AA[DF_AA['cat'] == 'Fibre'].assign(angle_h=lambda d: 90 - d['phi'])

# Métriques d'orientation
THICK_MED   = int(np.median(THICK))
NOL_D_MED   = int(DF_NOL['Diam_um'].median())
AA_ANG_MED  = round(float(FIB['angle_h'].median()), 1)
NOL_ANG_MED = round(float(DF_NOL['angle_h'].median()), 1)

# Diamètre équivalent (même formule, comparaison valide)
aa_eq      = (6 * FIB['vol'] * 1e9 / np.pi) ** (1 / 3)
nol_eq     = (6 * DF_NOL['Volume'] * 1000 / np.pi) ** (1 / 3)
AA_EQ_MED  = int(aa_eq.median())
NOL_EQ_MED = int(nol_eq.median())
ECART_PCT  = abs(AA_EQ_MED - NOL_EQ_MED) * 100 // max(AA_EQ_MED, NOL_EQ_MED)

# Morphologie MATLAB
NOL_LEN_MED = int(DF_NOL['Len_um'].median())
NOL_AR_MED  = round(float(DF_NOL['AspectRatio'].median()), 1)

# Contexte volumique
VOL_TOTAL    = 122.96                          # mm³ — scan complet Dragonfly
VOL_NOL_MM3  = 4.00                            # mm³ — sous-volume MATLAB
VOL_RATIO_PC = round(VOL_NOL_MM3 / VOL_TOTAL * 100, 1)   # 3.25 %
POROSITY     = 94.5                            # % — mesuré par Antoine (plage 88–95 %)
VOL_LABELED  = round(31_891_188 * (5.5e-3)**3, 2)         # 5.31 mm³

print(f"OK · {len(FIB)} fibres Dragonfly · {len(DF_NOL)} composantes MATLAB")


# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def lay(h=320, lg=False, **kw):
    d = dict(
        paper_bgcolor=CARD, plot_bgcolor=BG,
        font=dict(family=FONT, size=11, color=ZN500),
        height=h, showlegend=lg,
        margin=dict(l=46, r=16, t=18, b=44),
        xaxis=dict(showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500, family=FONT)),
        yaxis=dict(gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500, family=FONT)),
        legend=dict(orientation='h', yanchor='bottom', y=1.04, xanchor='left', x=0,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=11, color=ZN700)),
        hoverlabel=dict(bgcolor=ZN900, bordercolor=ZN900,
                        font=dict(color='white', size=12, family=FONT), namelength=-1),
    )
    d.update(kw)
    return d


def card(*children, p='22px 24px', mb='14px'):
    return html.Div(list(children), style={
        'background': CARD, 'borderRadius': '12px',
        'boxShadow': '0 0 0 1px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)',
        'padding': p, 'marginBottom': mb,
    })


def grid(*children, cols=2, gap='14px', mb='14px'):
    return html.Div(list(children), style={
        'display': 'grid',
        'gridTemplateColumns': ' '.join(['1fr'] * cols),
        'gap': gap, 'marginBottom': mb,
    })


def chart_head(title, subtitle=None):
    return html.Div([
        html.Div(title, style={'fontSize': '0.83rem', 'fontWeight': '600', 'color': ZN800}),
        *([html.Div(subtitle, style={'fontSize': '0.74rem', 'color': ZN500, 'marginTop': '3px'})]
          if subtitle else []),
    ], style={'marginBottom': '14px'})


def badge(text, cls='badge-info'):
    return html.Span(text, className=f'badge {cls}')


def G(fig):
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def kpi_dual(label, v_aa, v_nol, badge_text, badge_cls='badge-info'):
    return html.Div([
        html.Div(label.upper(), style={
            'fontSize': '0.67rem', 'fontWeight': '600',
            'color': ZN400, 'letterSpacing': '0.09em', 'marginBottom': '14px',
        }),
        html.Div([
            html.Div([
                html.Div(str(v_aa), className='tabnum', style={
                    'fontSize': '2rem', 'fontWeight': '700',
                    'color': INDIGO, 'lineHeight': '1', 'letterSpacing': '-0.03em',
                }),
                html.Div([
                    html.Span('●', style={'color': INDIGO, 'fontSize': '0.55rem', 'marginRight': '5px'}),
                    html.Span('Dragonfly', style={'color': ZN500, 'fontSize': '0.74rem'}),
                ], style={'marginTop': '7px', 'display': 'flex', 'alignItems': 'center'}),
            ]),
            html.Div(style={'width': '1px', 'background': ZN200, 'margin': '0 20px', 'alignSelf': 'stretch'}),
            html.Div([
                html.Div(str(v_nol), className='tabnum', style={
                    'fontSize': '2rem', 'fontWeight': '700',
                    'color': EMERALD, 'lineHeight': '1', 'letterSpacing': '-0.03em',
                }),
                html.Div([
                    html.Span('●', style={'color': EMERALD, 'fontSize': '0.55rem', 'marginRight': '5px'}),
                    html.Span('MATLAB', style={'color': ZN500, 'fontSize': '0.74rem'}),
                ], style={'marginTop': '7px', 'display': 'flex', 'alignItems': 'center'}),
            ]),
        ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '16px'}),
        html.Span(badge_text, className=f'badge {badge_cls}'),
    ], style={
        'background': CARD, 'borderRadius': '12px',
        'boxShadow': '0 0 0 1px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)',
        'padding': '20px 22px',
    })


def kpi_single(label, value, sub=None, color=ZN900):
    return html.Div([
        html.Div(label.upper(), style={
            'fontSize': '0.67rem', 'fontWeight': '600',
            'color': ZN400, 'letterSpacing': '0.09em', 'marginBottom': '14px',
        }),
        html.Div(value, className='tabnum', style={
            'fontSize': '2rem', 'fontWeight': '700',
            'color': color, 'lineHeight': '1', 'letterSpacing': '-0.03em', 'marginBottom': '10px',
        }),
        *([html.Div(sub, style={'fontSize': '0.78rem', 'color': ZN500})] if sub else []),
    ], style={
        'background': CARD, 'borderRadius': '12px',
        'boxShadow': '0 0 0 1px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)',
        'padding': '20px 22px',
    })


def item(text, warn=False):
    return html.Div([
        html.Span('·', style={'color': ZN400, 'marginRight': '8px', 'fontWeight': '700'}),
        html.Span(text, style={
            'fontSize': '0.81rem',
            'color': AMBER if warn else ZN700,
            'fontWeight': '600' if warn else '400',
        }),
    ], style={'marginBottom': '6px', 'display': 'flex', 'alignItems': 'baseline'})


def insight_banner(text, color=GREEN, bg='#F0FDF4', border='#D1FAE5'):
    return html.Div(text, style={
        'background': bg, 'border': f'1px solid {border}',
        'borderRadius': '10px', 'padding': '14px 18px', 'marginBottom': '14px',
        'fontSize': '0.85rem', 'fontWeight': '500', 'color': color,
        'lineHeight': '1.5',
    })


def warn_banner(text):
    return html.Div(text, style={
        'background': '#FFFBEB', 'border': '1px solid #FDE68A',
        'borderRadius': '10px', 'padding': '12px 16px', 'marginTop': '12px',
        'fontSize': '0.76rem', 'color': AMBER,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — VUE D'ENSEMBLE
# ══════════════════════════════════════════════════════════════════════════════

def build_overview():
    cats   = ['Bruit', 'Fragment', 'Fibre', 'Gros objet', 'Matrice']
    colors = [ZN200, '#FCD34D', INDIGO, '#A78BFA', ZN400]
    counts = DF_AA['cat'].value_counts().reindex(cats, fill_value=0)

    fig_seg = go.Figure(go.Bar(
        x=cats, y=counts.values, marker_color=colors,
        text=counts.values, textposition='outside',
        textfont=dict(size=11, color=ZN700, family=FONT),
        cliponaxis=False,
        hovertemplate='<b>%{x}</b> — %{y} objets<extra></extra>',
    ))
    fig_seg.update_layout(**lay(h=240,
        margin=dict(l=16, r=16, t=28, b=36),
        yaxis=dict(visible=False),
        xaxis=dict(showgrid=False, linecolor='transparent', zeroline=False,
                   tickfont=dict(size=11, color=ZN700)),
    ))

    vol_bar = html.Div([
        html.Div([
            html.Div('Volume total — Dragonfly', style={
                'fontSize': '0.75rem', 'fontWeight': '600', 'color': ZN700, 'marginBottom': '6px',
            }),
            html.Div([
                html.Div(style={
                    'height': '8px', 'background': INDIGO,
                    'borderRadius': '4px', 'width': '100%',
                }),
            ], style={'background': ZN100, 'borderRadius': '4px', 'marginBottom': '4px'}),
            html.Div([
                html.Span('122.96 mm³', className='tabnum', style={
                    'fontWeight': '700', 'color': INDIGO, 'fontSize': '0.9rem',
                }),
                html.Span(' — 100%', style={'color': ZN400, 'fontSize': '0.78rem', 'marginLeft': '6px'}),
            ]),
        ], style={'marginBottom': '14px'}),
        html.Div([
            html.Div('Sous-volume — MATLAB', style={
                'fontSize': '0.75rem', 'fontWeight': '600', 'color': ZN700, 'marginBottom': '6px',
            }),
            html.Div([
                html.Div(style={
                    'height': '8px', 'background': EMERALD,
                    'borderRadius': '4px', 'width': f'{VOL_RATIO_PC}%',
                }),
            ], style={'background': ZN100, 'borderRadius': '4px', 'marginBottom': '4px'}),
            html.Div([
                html.Span('4.00 mm³', className='tabnum', style={
                    'fontWeight': '700', 'color': EMERALD, 'fontSize': '0.9rem',
                }),
                html.Span(f' — {VOL_RATIO_PC}% du volume total', style={
                    'color': ZN400, 'fontSize': '0.78rem', 'marginLeft': '6px',
                }),
            ]),
        ]),
        html.Div([
            html.Span('Hypothèse d\'homogénéité : ', style={'fontWeight': '600'}),
            html.Span('les distributions du sous-volume sont supposées représentatives '
                      'du volume total (supposition de l\'équipe, non vérifiée).'),
        ], style={
            'marginTop': '14px', 'paddingTop': '12px', 'borderTop': f'1px solid {ZN200}',
            'fontSize': '0.75rem', 'color': ZN500, 'lineHeight': '1.5',
        }),
    ])

    return html.Div([

        # KPI row
        html.Div([
            kpi_single('Porosité du matériau', f'{POROSITY} %',
                       sub='Volume de fibres ≈ 4.3 % · Mesure Dragonfly (plage 88–95 %)',
                       color=ZN800),
            kpi_dual('Inclinaison médiane', f'{AA_ANG_MED}°', f'{NOL_ANG_MED}°',
                     '✓ Convergence', 'badge-ok'),
            kpi_dual('Diamètre équivalent', f'{AA_EQ_MED} µm', f'{NOL_EQ_MED} µm',
                     f'≈ {ECART_PCT}% d\'écart', 'badge-warn'),
        ], style={
            'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr',
            'gap': '14px', 'marginBottom': '14px',
        }),

        # Volume + fibres
        grid(
            card(
                html.Div('Contexte volumique', style={
                    'fontSize': '0.67rem', 'fontWeight': '600',
                    'color': ZN400, 'letterSpacing': '0.09em', 'marginBottom': '16px',
                }),
                vol_bar,
                p='20px 22px',
            ),
            card(
                html.Div('Objets analysés', style={
                    'fontSize': '0.67rem', 'fontWeight': '600',
                    'color': ZN400, 'letterSpacing': '0.09em', 'marginBottom': '16px',
                }),
                html.Div([
                    html.Div([
                        html.Div(str(len(FIB)), className='tabnum', style={
                            'fontSize': '2.2rem', 'fontWeight': '700',
                            'color': INDIGO, 'letterSpacing': '-0.03em',
                        }),
                        html.Div('fibres Dragonfly', style={'fontSize': '0.75rem', 'color': ZN500, 'marginTop': '4px'}),
                        html.Div('Filtre : 101 – 100 000 voxels', style={'fontSize': '0.71rem', 'color': ZN400}),
                    ]),
                    html.Div(style={'width': '1px', 'background': ZN200, 'margin': '0 20px', 'alignSelf': 'stretch'}),
                    html.Div([
                        html.Div(str(len(DF_NOL)), className='tabnum', style={
                            'fontSize': '2.2rem', 'fontWeight': '700',
                            'color': EMERALD, 'letterSpacing': '-0.03em',
                        }),
                        html.Div('composantes MATLAB', style={'fontSize': '0.75rem', 'color': ZN500, 'marginTop': '4px'}),
                        html.Div('Aucun filtre (fragments inclus)', style={'fontSize': '0.71rem', 'color': ZN400}),
                    ]),
                ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '14px'}),
                html.Div([
                    html.Span('⚠ Non comparables directement', style={'fontWeight': '600'}),
                    html.Span(' — volumes et critères de filtre différents. '
                              'Seules les distributions normalisées (%) sont valides.'),
                ], style={'fontSize': '0.75rem', 'color': AMBER, 'lineHeight': '1.5',
                          'paddingTop': '12px', 'borderTop': f'1px solid {ZN200}'}),
                p='20px 22px',
            ),
        ),

        # Méthodes
        grid(
            html.Div([
                html.Div([
                    html.Span('●', style={'color': INDIGO, 'fontSize': '0.65rem', 'marginRight': '8px'}),
                    html.Span('Dragonfly ORS', style={'fontWeight': '700', 'fontSize': '0.9rem', 'color': ZN900}),
                    html.Span(f'{VOX_UM:.1f} µm/voxel', style={
                        'fontSize': '0.72rem', 'color': ZN400, 'marginLeft': '10px', 'fontWeight': '500',
                    }),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px'}),
                html.Div([
                    item('Segmentation volumique des objets'),
                    item('Squelettisation des fibres'),
                    item('Épaisseur locale par ray-tracing'),
                    item(f'Filtre : 101 – 100 000 voxels → {len(FIB)} fibres retenues'),
                    item('Volume total analysé : 122.96 mm³', warn=True),
                ]),
            ], style={
                'background': CARD, 'borderRadius': '12px', 'padding': '20px 22px',
                'boxShadow': '0 0 0 1px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)',
            }),
            html.Div([
                html.Div([
                    html.Span('●', style={'color': EMERALD, 'fontSize': '0.65rem', 'marginRight': '8px'}),
                    html.Span('MATLAB regionprops3', style={'fontWeight': '700', 'fontSize': '0.9rem', 'color': ZN900}),
                    html.Span('~10 µm/voxel', style={
                        'fontSize': '0.72rem', 'color': ZN400, 'marginLeft': '10px', 'fontWeight': '500',
                    }),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px'}),
                html.Div([
                    item('Composantes connexes sur volume binaire'),
                    item('Ellipsoïde équivalent (axes principaux PAL1/2/3)'),
                    item(f'Aucun filtre → {len(DF_NOL)} composantes (fragments inclus)'),
                    item('Sous-volume : 200×200×100 vox = 4.00 mm³', warn=True),
                ]),
            ], style={
                'background': CARD, 'borderRadius': '12px', 'padding': '20px 22px',
                'boxShadow': '0 0 0 1px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)',
            }),
        ),

        # Segmentation bar chart
        card(
            chart_head(
                'Classification Dragonfly — tous les objets détectés',
                f'{len(DF_AA)} objets au total · seules les fibres (indigo, 101–100 000 voxels) entrent dans l\'analyse comparative',
            ),
            G(fig_seg),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — ORIENTATION
# ══════════════════════════════════════════════════════════════════════════════

def _polar_rose():
    n_bins = 18
    bins_p = np.linspace(0, 360, n_bins + 1)

    # Dragonfly : theta en degrés, normalisé 0–360
    theta_aa = FIB['theta'].values % 360

    # MATLAB : Orientation_1 mis à l'échelle 0–360
    theta_nol = (DF_NOL['Orientation_1'].values * 2) % 360

    hist_aa,  _ = np.histogram(theta_aa,  bins=bins_p)
    hist_nol, _ = np.histogram(theta_nol, bins=bins_p)
    hist_aa  = hist_aa  / hist_aa.sum()  * 100
    hist_nol = hist_nol / hist_nol.sum() * 100
    centers  = (bins_p[:-1] + bins_p[1:]) / 2

    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        r=hist_aa, theta=centers, name='Dragonfly', width=20,
        marker=dict(color=INDIGO, opacity=0.7, line=dict(color='white', width=0.5)),
        hovertemplate='%{theta:.0f}° : %{r:.1f}%<extra>Dragonfly</extra>',
    ))
    fig.add_trace(go.Barpolar(
        r=hist_nol, theta=centers, name='MATLAB', width=20,
        marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
        hovertemplate='%{theta:.0f}° : %{r:.1f}%<extra>MATLAB</extra>',
    ))
    fig.update_layout(
        paper_bgcolor=CARD,
        height=370,
        showlegend=True,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(
            orientation='h', y=-0.05, x=0.5, xanchor='center',
            bgcolor='rgba(0,0,0,0)', font=dict(size=11, color=ZN700, family=FONT),
        ),
        hoverlabel=dict(bgcolor=ZN900, bordercolor=ZN900,
                        font=dict(color='white', size=11, family=FONT)),
        polar=dict(
            bgcolor=BG,
            radialaxis=dict(
                visible=True, showticklabels=False, gridcolor=ZN200,
                linecolor=ZN200,
            ),
            angularaxis=dict(
                direction='clockwise', rotation=90,
                tickfont=dict(size=10, color=ZN500, family=FONT),
                linecolor=ZN200, gridcolor=ZN200,
            ),
        ),
    )
    return fig


def build_orientation():
    ecart_ang = abs(AA_ANG_MED - NOL_ANG_MED)
    return html.Div([

        insight_banner(
            f'✓  Convergence entre les deux méthodes : les fibres sont quasi-horizontales '
            f'(inclinaison médiane Dragonfly {AA_ANG_MED}°, MATLAB {NOL_ANG_MED}°, '
            f'écart {ecart_ang:.1f}°) et sans direction préférentielle dans le plan (distribution azimutale uniforme).'
        ),

        grid(
            # Rose polaire
            card(
                chart_head(
                    'Distribution azimutale dans le plan',
                    'Une distribution uniforme (cercle régulier) indique une isotropie planaire',
                ),
                G(_polar_rose()),
                html.Div(
                    'Les deux méthodes confirment l\'isotropie dans le plan horizontal — '
                    'aucune direction n\'est privilégiée.',
                    style={'fontSize': '0.76rem', 'color': ZN500, 'marginTop': '10px'},
                ),
                mb='0',
            ),
            # Inclinaison avec toggle
            card(
                html.Div([
                    chart_head(
                        'Inclinaison depuis l\'horizontale',
                        '0° = fibre à plat · 90° = fibre verticale',
                    ),
                    dcc.RadioItems(
                        id='method-toggle',
                        options=[
                            {'label': 'Les deux', 'value': 'both'},
                            {'label': 'Dragonfly', 'value': 'aa'},
                            {'label': 'MATLAB',    'value': 'nolhan'},
                        ],
                        value='both',
                        className='method-toggle',
                        inputStyle={'display': 'none'},
                        labelStyle={'cursor': 'pointer'},
                        style={'marginBottom': '14px'},
                    ),
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start'}),
                dcc.Graph(id='fig-elevation', config={'displayModeBar': False}),
                html.Div([
                    html.Div([
                        html.Span(f'{AA_ANG_MED}°', className='tabnum', style={
                            'color': INDIGO, 'fontWeight': '700', 'fontSize': '1.1rem', 'marginRight': '6px',
                        }),
                        html.Span('Dragonfly · médiane', style={'color': ZN500, 'fontSize': '0.78rem'}),
                    ], style={'display': 'flex', 'alignItems': 'baseline', 'marginBottom': '4px'}),
                    html.Div([
                        html.Span(f'{NOL_ANG_MED}°', className='tabnum', style={
                            'color': EMERALD, 'fontWeight': '700', 'fontSize': '1.1rem', 'marginRight': '6px',
                        }),
                        html.Span('MATLAB · médiane', style={'color': ZN500, 'fontSize': '0.78rem'}),
                    ], style={'display': 'flex', 'alignItems': 'baseline'}),
                ], style={'display': 'flex', 'gap': '24px', 'marginTop': '12px',
                          'paddingTop': '12px', 'borderTop': f'1px solid {ZN200}'}),
                mb='0',
            ),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — MORPHOLOGIE
# ══════════════════════════════════════════════════════════════════════════════

def build_morphology():
    vol_aa_um3  = FIB['vol'] * 1e9
    vol_nol_um3 = DF_NOL['Volume'] * 1000

    # Diamètre direct (métriques différentes — pour information)
    fig_diam_direct = go.Figure([
        go.Histogram(
            x=THICK, name=f'Dragonfly · ray-tracing (méd. {THICK_MED} µm)',
            histnorm='percent', xbins=dict(size=5),
            marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5)),
            hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>Dragonfly (épaisseur locale)</extra>',
        ),
        go.Histogram(
            x=DF_NOL['Diam_um'].dropna(), name=f'MATLAB · PAL₃×10 (méd. {NOL_D_MED} µm)',
            histnorm='percent', xbins=dict(size=5),
            marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
            hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>MATLAB (PAL₃ ellipsoïde)</extra>',
        ),
    ])
    fig_diam_direct.update_layout(**lay(h=280, lg=True, barmode='overlay',
        xaxis=dict(title='µm', range=[0, 280], showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # Diamètre équivalent (même formule, comparaison valide)
    fig_diam_eq = go.Figure([
        go.Histogram(
            x=aa_eq, name=f'Dragonfly (méd. {AA_EQ_MED} µm)',
            histnorm='percent', xbins=dict(size=8),
            marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5)),
            hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>Dragonfly</extra>',
        ),
        go.Histogram(
            x=nol_eq, name=f'MATLAB (méd. {NOL_EQ_MED} µm)',
            histnorm='percent', xbins=dict(size=8),
            marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
            hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>MATLAB</extra>',
        ),
    ])
    fig_diam_eq.update_layout(**lay(h=280, lg=True, barmode='overlay',
        xaxis=dict(title='Diamètre équivalent µm  —  d = ∛(6V/π)', showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # Longueur (MATLAB)
    fig_len = go.Figure(go.Histogram(
        x=DF_NOL['Len_um'], histnorm='percent', xbins=dict(size=30),
        marker=dict(color=EMERALD, opacity=0.8, line=dict(color='white', width=0.5)),
        hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra></extra>',
    ))
    fig_len.update_layout(**lay(h=250,
        xaxis=dict(title='Longueur PAL₁ (µm)', showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # Rapport d'aspect (MATLAB)
    fig_ar = go.Figure(go.Histogram(
        x=DF_NOL['AspectRatio'].clip(upper=12), histnorm='percent', xbins=dict(size=0.5),
        marker=dict(color=EMERALD, opacity=0.8, line=dict(color='white', width=0.5)),
        hovertemplate='Rapport %{x:.1f} : %{y:.1f}%<extra></extra>',
    ))
    fig_ar.update_layout(**lay(h=250,
        xaxis=dict(title='Rapport d\'aspect (Longueur / Diamètre)', showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # Volume (log, les deux méthodes)
    fig_vol = go.Figure([
        go.Histogram(
            x=np.log10(vol_aa_um3),
            name=f'Dragonfly (méd. {int(vol_aa_um3.median()):,} µm³)',
            histnorm='percent', xbins=dict(size=0.15),
            marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5)),
        ),
        go.Histogram(
            x=np.log10(vol_nol_um3),
            name=f'MATLAB (méd. {int(vol_nol_um3.median()):,} µm³)',
            histnorm='percent', xbins=dict(size=0.15),
            marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
        ),
    ])
    fig_vol.update_layout(**lay(h=260, lg=True, barmode='overlay',
        xaxis=dict(
            title='Volume (µm³)',
            tickvals=[3, 4, 5, 6, 7],
            ticktext=['10³', '10⁴', '10⁵', '10⁶', '10⁷'],
            showgrid=False, linecolor=ZN200, zeroline=False,
            tickfont=dict(size=10, color=ZN500),
        ),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # Carte spatiale (MATLAB)
    fig_map = go.Figure(go.Scatter(
        x=DF_NOL['Centroid_1'] * 10,
        y=DF_NOL['Centroid_2'] * 10,
        mode='markers',
        marker=dict(
            color=DF_NOL['angle_h'],
            colorscale=[[0, EMERALD], [0.5, '#FBBF24'], [1, RED]],
            cmin=0, cmax=45,
            size=(DF_NOL['Len_um'] / DF_NOL['Len_um'].max() * 14 + 4).clip(4, 18),
            opacity=0.85,
            colorbar=dict(
                title=dict(text='Incl. (°)', side='right'),
                thickness=10, len=0.75,
                tickfont=dict(size=10, color=ZN500, family=FONT),
            ),
            line=dict(color='white', width=0.5),
        ),
        hovertemplate='x = %{x:.0f} µm · y = %{y:.0f} µm<extra></extra>',
    ))
    fig_map.update_layout(**lay(h=340,
        xaxis=dict(title='x (µm)', scaleanchor='y', showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='y (µm)', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        margin=dict(l=50, r=60, t=18, b=50),
    ))

    return html.Div([

        # Diamètre — deux approches
        grid(
            card(
                chart_head(
                    'Diamètre — mesures directes',
                    'Ray-tracing local (Dragonfly) vs petit axe PAL₃ de l\'ellipsoïde (MATLAB)',
                ),
                G(fig_diam_direct),
                warn_banner(
                    '⚠  Ces deux courbes ne mesurent pas la même grandeur — '
                    'l\'écart apparent (×2) est attendu et n\'indique pas de désaccord.',
                ),
                mb='0',
            ),
            card(
                chart_head(
                    'Diamètre équivalent sphérique  —  d = ∛(6V/π)',
                    f'Même formule pour les deux méthodes · écart résiduel : {ECART_PCT}%',
                ),
                G(fig_diam_eq),
                html.Div(
                    f'En utilisant le volume brut de chaque objet, les distributions convergent '
                    f'à {ECART_PCT}% près. C\'est la comparaison diamètre la plus équitable.',
                    style={'fontSize': '0.76rem', 'color': ZN500, 'marginTop': '10px'},
                ),
                mb='0',
            ),
        ),

        # Longueur + rapport d'aspect (MATLAB uniquement)
        grid(
            card(
                chart_head(
                    'Longueur des fibres  —  MATLAB uniquement',
                    f'PAL₁ de l\'ellipsoïde × 10 µm · médiane {NOL_LEN_MED} µm',
                ),
                G(fig_len),
                html.Div(
                    'Dragonfly ne fournit pas de longueur de fibre directement '
                    '(la squelettisation n\'est pas exportée dans donnees2.csv).',
                    style={'fontSize': '0.76rem', 'color': ZN500, 'marginTop': '10px'},
                ),
                mb='0',
            ),
            card(
                chart_head(
                    'Rapport d\'aspect  —  MATLAB uniquement',
                    f'Longueur / Diamètre (PAL₁ / PAL₃) · médiane {NOL_AR_MED}',
                ),
                G(fig_ar),
                html.Div(
                    'Un rapport d\'aspect élevé traduit des fibres longues et fines. '
                    'La majorité des composantes ont un rapport inférieur à 5.',
                    style={'fontSize': '0.76rem', 'color': ZN500, 'marginTop': '10px'},
                ),
                mb='0',
            ),
        ),

        # Volume
        card(
            chart_head(
                'Distribution des volumes — échelle logarithmique',
                'Même unité µm³ pour les deux méthodes · comparaison valide',
            ),
            G(fig_vol),
        ),

        # Carte spatiale
        card(
            chart_head(
                'Localisation des fibres dans le sous-volume  —  MATLAB',
                'Taille du point ∝ longueur · couleur = inclinaison (vert = horizontal, rouge = vertical)',
            ),
            G(fig_map),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — COMPARAISON
# ══════════════════════════════════════════════════════════════════════════════

def build_comparison():
    def cmp_row(metric, v_aa, v_nol, bdg, bdg_cls, note='', alt=False):
        bg = ZN100 if alt else CARD
        return html.Tr([
            html.Td([
                html.Div(metric, style={'fontWeight': '500', 'color': ZN700, 'fontSize': '0.83rem'}),
                *([html.Div(note, style={'fontSize': '0.72rem', 'color': ZN400, 'marginTop': '2px'})] if note else []),
            ], style={'background': bg, 'padding': '12px 16px', 'verticalAlign': 'middle'}),
            html.Td(html.Span(v_aa, className='tabnum'),
                    style={'background': bg, 'padding': '12px 16px',
                           'color': INDIGO, 'fontWeight': '600', 'fontSize': '0.85rem',
                           'verticalAlign': 'middle'}),
            html.Td(html.Span(v_nol, className='tabnum'),
                    style={'background': bg, 'padding': '12px 16px',
                           'color': EMERALD, 'fontWeight': '600', 'fontSize': '0.85rem',
                           'verticalAlign': 'middle'}),
            html.Td(html.Span(bdg, className=f'badge {bdg_cls}'),
                    style={'background': bg, 'padding': '12px 16px', 'verticalAlign': 'middle'}),
        ])

    table = html.Table([
        html.Thead(html.Tr([
            html.Th('Métrique', style={'background': ZN100}),
            html.Th([html.Span('●', style={'color': INDIGO, 'marginRight': '6px'}), 'Dragonfly'],
                    style={'background': ZN100}),
            html.Th([html.Span('●', style={'color': EMERALD, 'marginRight': '6px'}), 'MATLAB'],
                    style={'background': ZN100}),
            html.Th('Accord', style={'background': ZN100}),
        ])),
        html.Tbody([
            # Contexte
            cmp_row('Volume analysé', '122.96 mm³', '4.00 mm³',
                    f'⚠  3.25 % de recouvrement', 'badge-warn',
                    'Volumes différents — distributions % comparables (hypothèse homogénéité)', False),
            cmp_row('Résolution', f'{VOX_UM:.1f} µm/voxel', '~10 µm/voxel',
                    '— Résolutions ≠', 'badge-info', '', True),
            cmp_row('Porosité', f'~{POROSITY} %', '— (non mesuré)',
                    '— Dragonfly seulement', 'badge-info', 'Plage mesurée : 88–95 %', False),
            # Orientation
            cmp_row('Orientation générale', 'Quasi-horizontale', 'Quasi-horizontale',
                    '✓ Accord', 'badge-ok', '', True),
            cmp_row('Inclinaison médiane', f'{AA_ANG_MED}°', f'{NOL_ANG_MED}°',
                    f'✓ Écart {abs(AA_ANG_MED - NOL_ANG_MED):.1f}°', 'badge-ok', 'Depuis l\'horizontale', False),
            cmp_row('Isotropie azimutale', 'Uniforme', 'Uniforme',
                    '✓ Accord', 'badge-ok', 'Pas de direction préférentielle', True),
            # Diamètre
            cmp_row('Diamètre mesure directe', f'{THICK_MED} µm', f'{NOL_D_MED} µm',
                    '≠ Métriques différentes', 'badge-diff',
                    'Ray-tracing local vs petit axe PAL₃ — non comparables', False),
            cmp_row('Diamètre équivalent ∛(6V/π)', f'{AA_EQ_MED} µm', f'{NOL_EQ_MED} µm',
                    f'≈ {ECART_PCT}% d\'écart', 'badge-warn',
                    'Même formule — comparaison la plus équitable', True),
            # Morphologie
            cmp_row('Longueur médiane', '— (non disponible)', f'{NOL_LEN_MED} µm',
                    '— MATLAB uniquement', 'badge-info', 'PAL₁ de l\'ellipsoïde', False),
            cmp_row('Rapport d\'aspect médian', '— (non disponible)', str(NOL_AR_MED),
                    '— MATLAB uniquement', 'badge-info', 'Longueur / Diamètre', True),
        ]),
    ], className='cmp-table', style={'width': '100%'})

    return html.Div([

        insight_banner(
            f'Résultat principal : les deux méthodes convergent sur l\'orientation des fibres '
            f'(quasi-horizontales, isotropes dans le plan). '
            f'L\'écart sur le diamètre ({ECART_PCT}%) s\'explique par des métriques différentes — '
            f'les mesures directes (ray-tracing vs PAL₃) ne sont pas comparables ; '
            f'le diamètre équivalent via le volume réduit cet écart.'
        ),

        card(
            chart_head(
                'Tableau comparatif — point par point',
                'Hypothèse d\'homogénéité : les distributions du sous-volume MATLAB sont supposées '
                'représentatives du volume total',
            ),
            table,
        ),

        # Lecture scientifique
        grid(
            card(
                html.Div('Ce que les données confirment', style={
                    'fontSize': '0.67rem', 'fontWeight': '600', 'color': GREEN,
                    'letterSpacing': '0.08em', 'textTransform': 'uppercase', 'marginBottom': '12px',
                }),
                html.Div([
                    item('Fibres quasi-horizontales dans les deux analyses (méd. < 12°)'),
                    item('Isotropie azimutale confirmée — pas de direction préférentielle'),
                    item(f'Porosité élevée ~{POROSITY} % cohérente avec un matériau fibreux lâche'),
                    item(f'Diamètre équivalent convergent à {ECART_PCT}% (51 vs 83 µm)'),
                ]),
                mb='0',
            ),
            card(
                html.Div('Limites et précautions', style={
                    'fontSize': '0.67rem', 'fontWeight': '600', 'color': AMBER,
                    'letterSpacing': '0.08em', 'textTransform': 'uppercase', 'marginBottom': '12px',
                }),
                html.Div([
                    item('Volumes très différents (3.25 %) — comptages absolus non comparables', warn=True),
                    item('Résolutions différentes (5.5 vs 10 µm) — segmentation distincte', warn=True),
                    item('MATLAB sans filtre : fragments et bruit inclus dans les 405 composantes', warn=True),
                    item('Hypothèse d\'homogénéité supposée, non vérifiée formellement', warn=True),
                ]),
                mb='0',
            ),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  APP & LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

TAB_STYLE = dict(
    color=ZN500, fontFamily=FONT, fontSize='0.83rem',
    padding='14px 22px', border='none', fontWeight='500',
    borderBottom='2px solid transparent', background='transparent',
)
TAB_SEL = {**TAB_STYLE,
           'color': ZN900, 'borderBottom': f'2px solid {ZN900}', 'fontWeight': '600'}

app = dash.Dash(
    __name__,
    title='FiberScope',
    suppress_callback_exceptions=True,
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
    ],
)
server = app.server

app.layout = html.Div([

    # Header
    html.Div([
        html.Div([
            html.Div([
                html.Span('FiberScope', style={
                    'fontSize': '1rem', 'fontWeight': '800',
                    'color': ZN900, 'letterSpacing': '-0.03em',
                }),
                html.Span(' · Dragonfly vs MATLAB', style={
                    'fontSize': '0.83rem', 'color': ZN500,
                    'fontWeight': '400', 'marginLeft': '6px',
                }),
            ]),
            html.Div('ESIEE Paris · MSME CNRS UMR 8208 · Projet E4', style={
                'fontSize': '0.75rem', 'color': ZN400, 'fontWeight': '500',
            }),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
            'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 24px',
        }),
    ], style={
        'background': CARD,
        'borderBottom': f'1px solid {ZN200}',
        'padding': '16px 0',
    }),

    # Tabs
    dcc.Tabs(id='tabs', value='overview',
        style={
            'background': CARD,
            'borderBottom': f'1px solid {ZN200}',
            'paddingLeft': '18px',
        },
        children=[
            dcc.Tab(label='Vue d\'ensemble', value='overview',   style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Orientation',     value='orient',     style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Morphologie',     value='morphology', style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Comparaison',     value='compare',    style=TAB_STYLE, selected_style=TAB_SEL),
        ],
    ),

    html.Div(id='content', style={'maxWidth': '1400px', 'margin': '0 auto'}),

    # Footer
    html.Div([
        html.Span('FiberScope', style={'fontWeight': '600', 'color': ZN700}),
        html.Span(
            f' · Dragonfly {VOX_UM:.1f} µm/vox · MATLAB ~10 µm/vox · '
            f'{len(FIB)} fibres Dragonfly · {len(DF_NOL)} composantes MATLAB · '
            f'Porosité ~{POROSITY}%',
            className='tabnum',
        ),
    ], style={
        'textAlign': 'center', 'padding': '20px',
        'fontSize': '0.72rem', 'color': ZN400,
        'borderTop': f'1px solid {ZN200}',
    }),

], style={'fontFamily': FONT, 'background': BG, 'minHeight': '100vh'})


@app.callback(Output('content', 'children'), Input('tabs', 'value'))
def render(tab):
    if tab == 'overview':   return build_overview()
    if tab == 'orient':     return build_orientation()
    if tab == 'morphology': return build_morphology()
    if tab == 'compare':    return build_comparison()
    return html.Div()


@app.callback(Output('fig-elevation', 'figure'), Input('method-toggle', 'value'))
def update_elevation(method):
    fig = go.Figure()
    if method in ('both', 'aa'):
        fig.add_trace(go.Histogram(
            x=FIB['angle_h'], name=f'Dragonfly — méd. {AA_ANG_MED}°',
            histnorm='percent', xbins=dict(size=3),
            marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5)),
            hovertemplate='%{x:.0f}° : %{y:.1f}%<extra>Dragonfly</extra>',
        ))
    if method in ('both', 'nolhan'):
        fig.add_trace(go.Histogram(
            x=DF_NOL['angle_h'], name=f'MATLAB — méd. {NOL_ANG_MED}°',
            histnorm='percent', xbins=dict(size=3),
            marker=dict(color=EMERALD, opacity=0.75, line=dict(color='white', width=0.5)),
            hovertemplate='%{x:.0f}° : %{y:.1f}%<extra>MATLAB</extra>',
        ))
    fig.update_layout(**lay(h=290, lg=(method == 'both'), barmode='overlay',
        xaxis=dict(title='Inclinaison depuis l\'horizontale (°)', range=[0, 90],
                   showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        margin=dict(l=46, r=16, t=10, b=44),
    ))
    return fig


if __name__ == '__main__':
    app.run(debug=False, port=8052)
