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

# Couleurs échantillons générés
GEN_COLORS  = ['#60A5FA', '#6366F1', '#7C3AED', '#A855F7']
GEN_LABELS  = ['F1 — Généré', 'F2 — Généré', 'F3 — Généré', 'F4 — Généré']
GEN_KEYS    = ['F1_genere', 'F2_genere', 'F3_genere', 'F4_genere']


# ══════════════════════════════════════════════════════════════════════════════
#  CHARGEMENT DES DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

def _load_dragonfly(filename):
    df = pd.read_csv(os.path.join(AA_DIR, filename), sep=';', encoding='utf-8-sig')
    df.columns = [c.strip() for c in df.columns]
    vol_col   = next(c for c in df.columns if 'Volume' in c and 'Surface' not in c)
    phi_col   = next(c for c in df.columns if 'Phi'    in c)
    theta_col = next(c for c in df.columns if 'Theta'  in c)
    sa_col    = next((c for c in df.columns if 'Surface' in c), None)
    rename    = {'Label Index': 'label', 'Voxel count': 'voxels',
                 vol_col: 'vol', phi_col: 'phi', theta_col: 'theta'}
    if sa_col:
        rename[sa_col] = 'surface_area'
    df = df[df[vol_col] > 0].rename(columns=rename)
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


def load_acoustique():
    df = pd.read_csv(os.path.join(AA_DIR, 'analyse_grandeurs_dossier.csv'),
                     sep=';', encoding='utf-8-sig')
    df.columns = ['nom', 'porosite', 'tortuosite', 'sv', 'lambda_v', 'lambda_t', 'sigma']
    df['lambda_v_um'] = df['lambda_v'] * 1000   # mm → µm
    df['lambda_t_um'] = df['lambda_t'] * 1000   # mm → µm
    return df


print("Chargement des données…")
DF_AA  = _load_dragonfly('donnees_F1_recycle.csv')
DF_NOL = load_nolhan()
THICK  = load_thickness()
DF_ACOUS = load_acoustique()

VOX_UM = 5.50
FIB    = DF_AA[DF_AA['cat'] == 'Fibre'].assign(angle_h=lambda d: 90 - d['phi'])

# Métriques comparatives
THICK_MED   = int(np.median(THICK))
NOL_D_MED   = int(DF_NOL['Diam_um'].median())
AA_ANG_MED  = round(float(FIB['angle_h'].median()), 1)
NOL_ANG_MED = round(float(DF_NOL['angle_h'].median()), 1)
aa_eq       = (6 * FIB['vol'] * 1e9 / np.pi) ** (1 / 3)
nol_eq      = (6 * DF_NOL['Volume'] * 1000 / np.pi) ** (1 / 3)
AA_EQ_MED   = int(aa_eq.median())
NOL_EQ_MED  = int(nol_eq.median())
ECART_PCT   = abs(AA_EQ_MED - NOL_EQ_MED) * 100 // max(AA_EQ_MED, NOL_EQ_MED)
NOL_LEN_MED = int(DF_NOL['Len_um'].median())
NOL_AR_MED  = round(float(DF_NOL['AspectRatio'].median()), 1)

# Contexte volumique
VOL_TOTAL    = 122.96
VOL_NOL_MM3  = 4.00
VOL_RATIO_PC = round(VOL_NOL_MM3 / VOL_TOTAL * 100, 1)
POROSITY     = 94.5

# Sous-datasets acoustiques
ACOUS_GEN = DF_ACOUS[DF_ACOUS['nom'].str.contains('genere')]
ACOUS_REF = DF_ACOUS[DF_ACOUS['nom'] == 'F1_originel']

print(f"OK · {len(FIB)} fibres Dragonfly · {len(DF_NOL)} composantes MATLAB · "
      f"{len(ACOUS_GEN)} échantillons générés")


# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def lay(h=300, lg=False, **kw):
    d = dict(
        paper_bgcolor=CARD, plot_bgcolor=BG,
        font=dict(family=FONT, size=11, color=ZN500),
        height=h, showlegend=lg,
        margin=dict(l=52, r=16, t=18, b=46),
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
                    'fontSize': '1.9rem', 'fontWeight': '700',
                    'color': INDIGO, 'lineHeight': '1', 'letterSpacing': '-0.03em',
                }),
                html.Div([
                    html.Span('●', style={'color': INDIGO, 'fontSize': '0.55rem', 'marginRight': '5px'}),
                    html.Span('Dragonfly', style={'color': ZN500, 'fontSize': '0.74rem'}),
                ], style={'marginTop': '7px', 'display': 'flex', 'alignItems': 'center'}),
            ]),
            html.Div(style={'width': '1px', 'background': ZN200, 'margin': '0 18px', 'alignSelf': 'stretch'}),
            html.Div([
                html.Div(str(v_nol), className='tabnum', style={
                    'fontSize': '1.9rem', 'fontWeight': '700',
                    'color': EMERALD, 'lineHeight': '1', 'letterSpacing': '-0.03em',
                }),
                html.Div([
                    html.Span('●', style={'color': EMERALD, 'fontSize': '0.55rem', 'marginRight': '5px'}),
                    html.Span('MATLAB', style={'color': ZN500, 'fontSize': '0.74rem'}),
                ], style={'marginTop': '7px', 'display': 'flex', 'alignItems': 'center'}),
            ]),
        ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '14px'}),
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
            'fontSize': '1.9rem', 'fontWeight': '700',
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


def insight(text, color=GREEN, bg='#F0FDF4', border='#D1FAE5'):
    return html.Div(text, style={
        'background': bg, 'border': f'1px solid {border}', 'borderRadius': '10px',
        'padding': '14px 18px', 'marginBottom': '14px',
        'fontSize': '0.85rem', 'fontWeight': '500', 'color': color, 'lineHeight': '1.5',
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
        textfont=dict(size=11, color=ZN700, family=FONT), cliponaxis=False,
        hovertemplate='<b>%{x}</b> — %{y} objets<extra></extra>',
    ))
    fig_seg.update_layout(**lay(h=230,
        margin=dict(l=16, r=16, t=28, b=36),
        yaxis=dict(visible=False),
        xaxis=dict(showgrid=False, linecolor='transparent', zeroline=False,
                   tickfont=dict(size=11, color=ZN700)),
    ))

    return html.Div([

        html.Div([
            kpi_single('Porosité', f'{POROSITY} %',
                       sub='Volume de fibres ≈ 4.3 % · mesure Dragonfly (plage 88–95 %)',
                       color=ZN800),
            kpi_dual('Inclinaison médiane', f'{AA_ANG_MED}°', f'{NOL_ANG_MED}°',
                     '✓ Convergence', 'badge-ok'),
            kpi_dual('Diamètre équivalent', f'{AA_EQ_MED} µm', f'{NOL_EQ_MED} µm',
                     f'≈ {ECART_PCT}% d\'écart', 'badge-warn'),
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr',
                  'gap': '14px', 'marginBottom': '14px'}),

        grid(
            card(
                html.Div('Contexte volumique', style={
                    'fontSize': '0.67rem', 'fontWeight': '600',
                    'color': ZN400, 'letterSpacing': '0.09em', 'marginBottom': '16px',
                }),
                html.Div([
                    html.Div('Volume total — Dragonfly (F1 Recyclé)', style={
                        'fontSize': '0.75rem', 'fontWeight': '600', 'color': ZN700, 'marginBottom': '5px',
                    }),
                    html.Div(style={'height': '8px', 'background': INDIGO, 'borderRadius': '4px',
                                    'width': '100%', 'marginBottom': '4px'}),
                    html.Span(f'122.96 mm³ — 100%', className='tabnum',
                              style={'fontWeight': '700', 'color': INDIGO, 'fontSize': '0.88rem'}),
                ], style={'marginBottom': '14px'}),
                html.Div([
                    html.Div('Sous-volume — MATLAB (Nolhan)', style={
                        'fontSize': '0.75rem', 'fontWeight': '600', 'color': ZN700, 'marginBottom': '5px',
                    }),
                    html.Div([html.Div(style={
                        'height': '8px', 'background': EMERALD, 'borderRadius': '4px',
                        'width': f'{VOL_RATIO_PC}%',
                    })], style={'background': ZN100, 'borderRadius': '4px', 'marginBottom': '4px'}),
                    html.Span(f'4.00 mm³ — {VOL_RATIO_PC}% du total', className='tabnum',
                              style={'fontWeight': '700', 'color': EMERALD, 'fontSize': '0.88rem'}),
                ]),
                html.Div(
                    'Hypothèse d\'homogénéité : distributions du sous-volume supposées '
                    'représentatives du volume total.',
                    style={'fontSize': '0.74rem', 'color': ZN500, 'marginTop': '14px',
                           'paddingTop': '12px', 'borderTop': f'1px solid {ZN200}'},
                ),
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
                            'fontSize': '2.2rem', 'fontWeight': '700', 'color': INDIGO,
                            'letterSpacing': '-0.03em',
                        }),
                        html.Div('fibres Dragonfly', style={'fontSize': '0.75rem', 'color': ZN500, 'marginTop': '4px'}),
                        html.Div('Filtre : 101 – 100 000 voxels · 5.5 µm/vox',
                                 style={'fontSize': '0.71rem', 'color': ZN400}),
                    ]),
                    html.Div(style={'width': '1px', 'background': ZN200, 'margin': '0 20px', 'alignSelf': 'stretch'}),
                    html.Div([
                        html.Div(str(len(DF_NOL)), className='tabnum', style={
                            'fontSize': '2.2rem', 'fontWeight': '700', 'color': EMERALD,
                            'letterSpacing': '-0.03em',
                        }),
                        html.Div('composantes MATLAB', style={'fontSize': '0.75rem', 'color': ZN500, 'marginTop': '4px'}),
                        html.Div('Aucun filtre · fragments inclus · ~10 µm/vox',
                                 style={'fontSize': '0.71rem', 'color': ZN400}),
                    ]),
                ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '14px'}),
                html.Div(
                    '⚠ Comptages non comparables — volumes et filtres différents. '
                    'Seules les distributions normalisées (%) sont valides.',
                    style={'fontSize': '0.75rem', 'color': AMBER, 'lineHeight': '1.5',
                           'paddingTop': '12px', 'borderTop': f'1px solid {ZN200}'},
                ),
                p='20px 22px',
            ),
        ),

        grid(
            html.Div([
                html.Div([
                    html.Span('●', style={'color': INDIGO, 'fontSize': '0.65rem', 'marginRight': '8px'}),
                    html.Span('Dragonfly ORS — F1 Recyclé', style={'fontWeight': '700', 'fontSize': '0.88rem', 'color': ZN900}),
                    html.Span('5.5 µm/voxel', style={'fontSize': '0.72rem', 'color': ZN400, 'marginLeft': '10px'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px'}),
                html.Div([
                    item('Segmentation volumique → squelettisation'),
                    item('Épaisseur locale par ray-tracing'),
                    item(f'Filtre : 101–100 000 voxels → {len(FIB)} fibres'),
                    item('Volume total : 122.96 mm³', warn=True),
                ]),
            ], style={'background': CARD, 'borderRadius': '12px', 'padding': '20px 22px',
                      'boxShadow': '0 0 0 1px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)'}),
            html.Div([
                html.Div([
                    html.Span('●', style={'color': EMERALD, 'fontSize': '0.65rem', 'marginRight': '8px'}),
                    html.Span('MATLAB regionprops3 — Nolhan', style={'fontWeight': '700', 'fontSize': '0.88rem', 'color': ZN900}),
                    html.Span('~10 µm/voxel', style={'fontSize': '0.72rem', 'color': ZN400, 'marginLeft': '10px'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px'}),
                html.Div([
                    item('Composantes connexes → ellipsoïde équivalent'),
                    item('Axes principaux PAL1/2/3, angles d\'Euler'),
                    item(f'Aucun filtre → {len(DF_NOL)} composantes'),
                    item('Sous-volume : 200×200×100 vox = 4.00 mm³', warn=True),
                ]),
            ], style={'background': CARD, 'borderRadius': '12px', 'padding': '20px 22px',
                      'boxShadow': '0 0 0 1px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)'}),
        ),

        card(
            chart_head('Classification Dragonfly — tous les objets détectés',
                       f'{len(DF_AA)} objets · seules les fibres (indigo) entrent dans la comparaison'),
            G(fig_seg),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — ORIENTATION
# ══════════════════════════════════════════════════════════════════════════════

def _polar_rose():
    n_bins  = 18
    bins_p  = np.linspace(0, 360, n_bins + 1)
    theta_aa  = FIB['theta'].values % 360
    theta_nol = (DF_NOL['Orientation_1'].values * 2) % 360
    h_aa,  _ = np.histogram(theta_aa,  bins=bins_p)
    h_nol, _ = np.histogram(theta_nol, bins=bins_p)
    h_aa  = h_aa  / h_aa.sum()  * 100
    h_nol = h_nol / h_nol.sum() * 100
    centers = (bins_p[:-1] + bins_p[1:]) / 2
    fig = go.Figure([
        go.Barpolar(r=h_aa,  theta=centers, name='Dragonfly', width=20,
                    marker=dict(color=INDIGO,  opacity=0.75, line=dict(color='white', width=0.5)),
                    hovertemplate='%{theta:.0f}° : %{r:.1f}%<extra>Dragonfly</extra>'),
        go.Barpolar(r=h_nol, theta=centers, name='MATLAB',    width=20,
                    marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
                    hovertemplate='%{theta:.0f}° : %{r:.1f}%<extra>MATLAB</extra>'),
    ])
    fig.update_layout(
        paper_bgcolor=CARD, height=360, showlegend=True,
        margin=dict(l=20, r=20, t=20, b=10),
        legend=dict(orientation='h', y=-0.04, x=0.5, xanchor='center',
                    bgcolor='rgba(0,0,0,0)', font=dict(size=11, color=ZN700, family=FONT)),
        hoverlabel=dict(bgcolor=ZN900, bordercolor=ZN900,
                        font=dict(color='white', size=11, family=FONT)),
        polar=dict(bgcolor=BG,
                   radialaxis=dict(visible=True, showticklabels=False, gridcolor=ZN200, linecolor=ZN200),
                   angularaxis=dict(direction='clockwise', rotation=90,
                                    tickfont=dict(size=10, color=ZN500, family=FONT),
                                    linecolor=ZN200, gridcolor=ZN200)),
    )
    return fig


def _fig_azimut():
    fig = go.Figure([
        go.Histogram(x=FIB['theta'], name=f'Dragonfly — Theta',
                     histnorm='percent', xbins=dict(size=10),
                     marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f}° : %{y:.1f}%<extra>Dragonfly</extra>'),
        go.Histogram(x=DF_NOL['Orientation_1'] * 2, name='MATLAB — Orient₁×2',
                     histnorm='percent', xbins=dict(size=10),
                     marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f}° : %{y:.1f}%<extra>MATLAB</extra>'),
    ])
    fig.update_layout(**lay(h=250, lg=True, barmode='overlay',
        xaxis=dict(title='Azimut (°)', range=[-185, 185], showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))
    return fig


def build_orientation():
    ecart = abs(AA_ANG_MED - NOL_ANG_MED)
    return html.Div([

        insight(f'✓  Convergence : fibres quasi-horizontales dans les deux méthodes '
                f'(Dragonfly {AA_ANG_MED}°, MATLAB {NOL_ANG_MED}°, écart {ecart:.1f}°). '
                f'Distribution azimutale uniforme → pas de direction préférentielle.'),

        grid(
            card(
                chart_head('Distribution azimutale — Diagramme rose polaire',
                           'Un cercle régulier confirme l\'isotropie dans le plan horizontal'),
                G(_polar_rose()),
                mb='0',
            ),
            card(
                html.Div([
                    chart_head('Inclinaison depuis l\'horizontale',
                               '0° = fibre à plat · 90° = fibre verticale'),
                    dcc.RadioItems(id='method-toggle',
                        options=[{'label': 'Les deux', 'value': 'both'},
                                 {'label': 'Dragonfly', 'value': 'aa'},
                                 {'label': 'MATLAB', 'value': 'nolhan'}],
                        value='both', className='method-toggle',
                        inputStyle={'display': 'none'}, labelStyle={'cursor': 'pointer'},
                        style={'marginBottom': '12px'}),
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
                ], style={'display': 'flex', 'gap': '24px', 'marginTop': '10px',
                          'paddingTop': '10px', 'borderTop': f'1px solid {ZN200}'}),
                mb='0',
            ),
        ),

        card(
            chart_head('Distribution azimutale — Histogramme',
                       'Confirmation de l\'isotropie : distribution plate sur -180° à +180°'),
            G(_fig_azimut()),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — MORPHOLOGIE (maximum de comparaisons)
# ══════════════════════════════════════════════════════════════════════════════

def build_morphologie():
    vol_aa_um3  = FIB['vol'] * 1e9
    vol_nol_um3 = DF_NOL['Volume'] * 1000

    # 1. Diamètre direct (métriques différentes)
    fig_d_direct = go.Figure([
        go.Histogram(x=THICK, name=f'Dragonfly · ray-tracing (méd. {THICK_MED} µm)',
                     histnorm='percent', xbins=dict(size=5),
                     marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>Dragonfly</extra>'),
        go.Histogram(x=DF_NOL['Diam_um'].dropna(), name=f'MATLAB · PAL₃×10 (méd. {NOL_D_MED} µm)',
                     histnorm='percent', xbins=dict(size=5),
                     marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>MATLAB</extra>'),
    ])
    fig_d_direct.update_layout(**lay(h=270, lg=True, barmode='overlay',
        xaxis=dict(title='µm', range=[0, 280], showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 2. Diamètre équivalent ∛(6V/π)
    fig_d_eq = go.Figure([
        go.Histogram(x=aa_eq, name=f'Dragonfly (méd. {AA_EQ_MED} µm)',
                     histnorm='percent', xbins=dict(size=8),
                     marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>Dragonfly</extra>'),
        go.Histogram(x=nol_eq, name=f'MATLAB (méd. {NOL_EQ_MED} µm)',
                     histnorm='percent', xbins=dict(size=8),
                     marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>MATLAB</extra>'),
    ])
    fig_d_eq.update_layout(**lay(h=270, lg=True, barmode='overlay',
        xaxis=dict(title='Diamètre équivalent (µm)', showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 3. CDF diamètre équivalent
    x_aa_s  = np.sort(aa_eq.values)
    y_aa_s  = np.arange(1, len(x_aa_s)  + 1) / len(x_aa_s)  * 100
    x_nol_s = np.sort(nol_eq.values)
    y_nol_s = np.arange(1, len(x_nol_s) + 1) / len(x_nol_s) * 100

    fig_cdf = go.Figure([
        go.Scatter(x=x_aa_s,  y=y_aa_s,
                   name=f'Dragonfly (méd. {AA_EQ_MED} µm)',
                   line=dict(color=INDIGO, width=2.5), mode='lines',
                   hovertemplate='%{x:.0f} µm → %{y:.1f}%<extra>Dragonfly</extra>'),
        go.Scatter(x=x_nol_s, y=y_nol_s,
                   name=f'MATLAB (méd. {NOL_EQ_MED} µm)',
                   line=dict(color=EMERALD, width=2.5), mode='lines',
                   hovertemplate='%{x:.0f} µm → %{y:.1f}%<extra>MATLAB</extra>'),
        go.Scatter(x=[AA_EQ_MED,  AA_EQ_MED],  y=[0, 50],
                   line=dict(color=INDIGO,  width=1, dash='dot'), mode='lines', showlegend=False),
        go.Scatter(x=[NOL_EQ_MED, NOL_EQ_MED], y=[0, 50],
                   line=dict(color=EMERALD, width=1, dash='dot'), mode='lines', showlegend=False),
        go.Scatter(x=[0, AA_EQ_MED],  y=[50, 50],
                   line=dict(color=ZN400, width=1, dash='dot'), mode='lines', showlegend=False),
    ])
    fig_cdf.update_layout(**lay(h=270, lg=True,
        xaxis=dict(title='Diamètre équivalent (µm)', showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='Fibres ≤ x (%)', range=[0, 100], gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 4. Distribution de volumes (log)
    fig_vol = go.Figure([
        go.Histogram(x=np.log10(vol_aa_um3),
                     name=f'Dragonfly (méd. {int(vol_aa_um3.median()):,} µm³)',
                     histnorm='percent', xbins=dict(size=0.15),
                     marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5))),
        go.Histogram(x=np.log10(vol_nol_um3),
                     name=f'MATLAB (méd. {int(vol_nol_um3.median()):,} µm³)',
                     histnorm='percent', xbins=dict(size=0.15),
                     marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5))),
    ])
    fig_vol.update_layout(**lay(h=270, lg=True, barmode='overlay',
        xaxis=dict(title='Volume (µm³)', tickvals=[3,4,5,6,7],
                   ticktext=['10³','10⁴','10⁵','10⁶','10⁷'],
                   showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 5. Box plots — inclinaison
    fig_box_ang = go.Figure([
        go.Box(y=FIB['angle_h'], name='Dragonfly', marker_color=INDIGO,
               line=dict(color=INDIGO), fillcolor='rgba(99,102,241,0.12)',
               hovertemplate='%{y:.1f}°<extra>Dragonfly</extra>'),
        go.Box(y=DF_NOL['angle_h'], name='MATLAB', marker_color=EMERALD,
               line=dict(color=EMERALD), fillcolor='rgba(16,185,129,0.12)',
               hovertemplate='%{y:.1f}°<extra>MATLAB</extra>'),
    ])
    fig_box_ang.update_layout(**lay(h=270,
        yaxis=dict(title='Inclinaison (°)', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        xaxis=dict(showgrid=False, linecolor='transparent', tickfont=dict(size=11, color=ZN700)),
    ))

    # 6. Box plots — diamètre équivalent
    fig_box_diam = go.Figure([
        go.Box(y=aa_eq,  name=f'Dragonfly', marker_color=INDIGO,
               line=dict(color=INDIGO),  fillcolor='rgba(99,102,241,0.12)',
               hovertemplate='%{y:.0f} µm<extra>Dragonfly</extra>'),
        go.Box(y=nol_eq, name=f'MATLAB',    marker_color=EMERALD,
               line=dict(color=EMERALD), fillcolor='rgba(16,185,129,0.12)',
               hovertemplate='%{y:.0f} µm<extra>MATLAB</extra>'),
    ])
    fig_box_diam.update_layout(**lay(h=270,
        yaxis=dict(title='Diamètre équivalent (µm)', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        xaxis=dict(showgrid=False, linecolor='transparent', tickfont=dict(size=11, color=ZN700)),
    ))

    # 7. Scatter : volume vs inclinaison
    fig_scatter = go.Figure([
        go.Scatter(x=vol_aa_um3, y=FIB['angle_h'],
                   mode='markers', name='Dragonfly',
                   marker=dict(color=INDIGO, size=7, opacity=0.65,
                               line=dict(color='white', width=0.5)),
                   hovertemplate='Vol. %{x:.0f} µm³ · %{y:.1f}°<extra>Dragonfly</extra>'),
        go.Scatter(x=vol_nol_um3, y=DF_NOL['angle_h'],
                   mode='markers', name='MATLAB',
                   marker=dict(color=EMERALD, size=7, opacity=0.65,
                               line=dict(color='white', width=0.5)),
                   hovertemplate='Vol. %{x:.0f} µm³ · %{y:.1f}°<extra>MATLAB</extra>'),
    ])
    fig_scatter.update_layout(**lay(h=270, lg=True,
        xaxis=dict(title='Volume (µm³)', type='log', showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='Inclinaison (°)', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 8. Longueur MATLAB
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

    # 9. Rapport d'aspect MATLAB
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

    # 10. Carte spatiale MATLAB
    fig_map = go.Figure(go.Scatter(
        x=DF_NOL['Centroid_1'] * 10, y=DF_NOL['Centroid_2'] * 10,
        mode='markers',
        marker=dict(color=DF_NOL['angle_h'],
                    colorscale=[[0, EMERALD], [0.5, '#FBBF24'], [1, RED]],
                    cmin=0, cmax=45,
                    size=(DF_NOL['Len_um'] / DF_NOL['Len_um'].max() * 14 + 4).clip(4, 18),
                    opacity=0.85,
                    colorbar=dict(title=dict(text='Incl. (°)', side='right'),
                                  thickness=10, len=0.75,
                                  tickfont=dict(size=10, color=ZN500, family=FONT)),
                    line=dict(color='white', width=0.5)),
        hovertemplate='x=%{x:.0f} µm · y=%{y:.0f} µm<extra></extra>',
    ))
    fig_map.update_layout(**lay(h=340,
        xaxis=dict(title='x (µm)', scaleanchor='y', showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='y (µm)', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        margin=dict(l=50, r=60, t=18, b=50),
    ))

    return html.Div([

        # Diamètres
        grid(
            card(chart_head('Diamètre — mesure directe',
                            'Ray-tracing local (Dragonfly) vs petit axe PAL₃ (MATLAB) — métriques différentes'),
                 G(fig_d_direct),
                 html.Div('⚠ Ces deux courbes ne mesurent pas la même grandeur — '
                          'l\'écart ×2 est attendu et n\'indique pas de désaccord.',
                          style={'fontSize': '0.75rem', 'color': AMBER, 'marginTop': '8px'}),
                 mb='0'),
            card(chart_head(f'Diamètre équivalent sphérique — d = ∛(6V/π)',
                            f'Même formule pour les deux méthodes · écart résiduel {ECART_PCT}%'),
                 G(fig_d_eq),
                 html.Div(f'Comparaison la plus équitable : {ECART_PCT}% d\'écart entre les médianes '
                          f'({AA_EQ_MED} µm vs {NOL_EQ_MED} µm).',
                          style={'fontSize': '0.75rem', 'color': ZN500, 'marginTop': '8px'}),
                 mb='0'),
        ),

        # CDF + Volume
        grid(
            card(chart_head('Distribution cumulée — Diamètre équivalent',
                            'La courbe la plus à gauche = fibres plus fines en médiane · pointillés = médianes'),
                 G(fig_cdf), mb='0'),
            card(chart_head('Distribution des volumes — Échelle logarithmique',
                            'Même unité µm³ pour les deux méthodes'),
                 G(fig_vol), mb='0'),
        ),

        # Box plots
        grid(
            card(chart_head('Box plot — Inclinaison depuis l\'horizontale',
                            'Médiane, quartiles et valeurs extrêmes'),
                 G(fig_box_ang), mb='0'),
            card(chart_head('Box plot — Diamètre équivalent',
                            'Dispersion des tailles de fibres par méthode'),
                 G(fig_box_diam), mb='0'),
        ),

        # Scatter + longueur
        grid(
            card(chart_head('Volume vs Inclinaison',
                            'Chaque point = une fibre · les fibres volumineuses sont-elles plus inclinées ?'),
                 G(fig_scatter), mb='0'),
            card(chart_head(f'Longueur des fibres — MATLAB uniquement',
                            f'PAL₁ de l\'ellipsoïde × 10 µm · médiane {NOL_LEN_MED} µm'),
                 G(fig_len),
                 html.Div('Dragonfly ne fournit pas de longueur directement (squelette non exporté).',
                          style={'fontSize': '0.75rem', 'color': ZN500, 'marginTop': '8px'}),
                 mb='0'),
        ),

        # Rapport d'aspect
        card(chart_head(f'Rapport d\'aspect — MATLAB uniquement',
                        f'Longueur / Diamètre (PAL₁/PAL₃) · médiane {NOL_AR_MED}'),
             G(fig_ar)),

        # Carte spatiale
        card(chart_head('Localisation spatiale des fibres dans le sous-volume — MATLAB',
                        'Taille ∝ longueur · couleur = inclinaison (vert=horizontal, rouge=vertical)'),
             G(fig_map)),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — COMPARAISON (synthèse)
# ══════════════════════════════════════════════════════════════════════════════

def build_comparaison():
    def row(metric, v_aa, v_nol, bdg, bdg_cls, note='', alt=False):
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
            html.Th([html.Span('●', style={'color': INDIGO,  'marginRight': '6px'}), 'Dragonfly'], style={'background': ZN100}),
            html.Th([html.Span('●', style={'color': EMERALD, 'marginRight': '6px'}), 'MATLAB'],    style={'background': ZN100}),
            html.Th('Accord', style={'background': ZN100}),
        ])),
        html.Tbody([
            row('Volume analysé',          '122.96 mm³', '4.00 mm³',          f'⚠ {VOL_RATIO_PC}% commun', 'badge-warn',
                'Volumes et filtres différents — distributions % valides (hypothèse homogénéité)', False),
            row('Résolution',              f'{VOX_UM} µm/vox', '~10 µm/vox',  '— Résolutions ≠',        'badge-info', '', True),
            row('Porosité',                f'~{POROSITY} %',   '— (n/a)',      '— Dragonfly seulement',   'badge-info', 'Plage mesurée 88–95 %', False),
            row('Orientation générale',    'Quasi-horizontale','Quasi-horizontale','✓ Accord',            'badge-ok',   '', True),
            row('Inclinaison médiane',      f'{AA_ANG_MED}°',   f'{NOL_ANG_MED}°','✓ Écart {abs(AA_ANG_MED-NOL_ANG_MED):.1f}°','badge-ok','Depuis l\'horizontale', False),
            row('Isotropie azimutale',     'Uniforme',         'Uniforme',     '✓ Accord',                'badge-ok',   'Pas de direction préférentielle', True),
            row('Diamètre mesure directe', f'{THICK_MED} µm',  f'{NOL_D_MED} µm', '≠ Métriques ≠',      'badge-diff', 'Ray-tracing vs PAL₃ — non comparables en valeur absolue', False),
            row('Diamètre équivalent ∛6V/π',f'{AA_EQ_MED} µm', f'{NOL_EQ_MED} µm',f'≈ {ECART_PCT}% écart','badge-warn','Même formule — comparaison la plus équitable', True),
            row('Longueur médiane',         '— (n/a)',          f'{NOL_LEN_MED} µm','— MATLAB uniquement', 'badge-info', 'PAL₁ × 10 µm', False),
            row('Rapport d\'aspect médian', '— (n/a)',          str(NOL_AR_MED),    '— MATLAB uniquement', 'badge-info', 'Longueur / Diamètre', True),
        ]),
    ], className='cmp-table', style={'width': '100%'})

    return html.Div([

        insight(f'Résultat clé : convergence sur l\'orientation (fibres horizontales, isotropes). '
                f'Écart sur le diamètre ({ECART_PCT}%) expliqué par des métriques différentes — '
                f'le diamètre équivalent via volume est la comparaison la plus rigoureuse.'),

        card(chart_head('Tableau comparatif — point par point'), table),

        grid(
            card(
                html.Div('✓  Ce que les données confirment', style={
                    'fontSize': '0.67rem', 'fontWeight': '600', 'color': GREEN,
                    'letterSpacing': '0.08em', 'textTransform': 'uppercase', 'marginBottom': '12px',
                }),
                html.Div([
                    item('Fibres quasi-horizontales : médianes < 12° pour les deux méthodes'),
                    item('Isotropie azimutale confirmée — pas de direction préférentielle'),
                    item(f'Porosité ~{POROSITY}% — cohérente avec un matériau fibreux lâche'),
                    item(f'Diamètre équivalent convergent à {ECART_PCT}% ({AA_EQ_MED} µm vs {NOL_EQ_MED} µm)'),
                ]),
                mb='0',
            ),
            card(
                html.Div('⚠  Limites et précautions', style={
                    'fontSize': '0.67rem', 'fontWeight': '600', 'color': AMBER,
                    'letterSpacing': '0.08em', 'textTransform': 'uppercase', 'marginBottom': '12px',
                }),
                html.Div([
                    item('Volumes très différents (3.25 %) — comptages absolus non comparables', warn=True),
                    item('Résolutions différentes : 5.5 µm (Dragonfly) vs 10 µm (MATLAB)', warn=True),
                    item('MATLAB sans filtre : fragments et bruit inclus dans les 405 comp.', warn=True),
                    item('Hypothèse d\'homogénéité supposée, non vérifiée formellement', warn=True),
                ]),
                mb='0',
            ),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 5 — PROPRIÉTÉS ACOUSTIQUES (F1–F4 générés vs porosité)
# ══════════════════════════════════════════════════════════════════════════════

def _acous_scatter(y_col, y_label, y_log=False, y_unit=''):
    gen  = ACOUS_GEN.copy()
    ref  = ACOUS_REF.copy()

    # Traces générés (F1→F4 avec progression de couleur)
    traces = []
    for i, (_, r) in enumerate(gen.iterrows()):
        label = GEN_LABELS[i] if i < len(GEN_LABELS) else r['nom']
        traces.append(go.Scatter(
            x=[r['porosite'] * 100], y=[r[y_col]],
            mode='markers', name=label,
            marker=dict(color=GEN_COLORS[i], size=11, symbol='circle',
                        line=dict(color='white', width=1.5)),
            hovertemplate=f'Porosité: %{{x:.2f}}%<br>{y_label}: %{{y:.4g}}{y_unit}<extra>{label}</extra>',
        ))

    # Ligne de tendance sur les générés
    if len(gen) >= 2:
        xi = gen['porosite'].values * 100
        yi = gen[y_col].values
        idx = np.argsort(xi)
        if y_log:
            lyi = np.log10(yi)
            coeffs = np.polyfit(xi[idx], lyi[idx], 1)
            x_fit = np.linspace(xi.min() - 0.5, xi.max() + 0.5, 100)
            y_fit = 10 ** np.polyval(coeffs, x_fit)
        else:
            coeffs = np.polyfit(xi[idx], yi[idx], 1)
            x_fit = np.linspace(xi.min() - 0.5, xi.max() + 0.5, 100)
            y_fit = np.polyval(coeffs, x_fit)
        traces.append(go.Scatter(
            x=x_fit, y=y_fit, mode='lines', name='Tendance',
            line=dict(color=ZN400, width=1.5, dash='dot'),
            showlegend=False,
            hoverinfo='skip',
        ))

    # Référence F1_originel
    if not ref.empty:
        r = ref.iloc[0]
        traces.append(go.Scatter(
            x=[r['porosite'] * 100], y=[r[y_col]],
            mode='markers', name='F1 — Référence (scan réel)',
            marker=dict(color=ZN400, size=13, symbol='star',
                        line=dict(color='white', width=1.5)),
            hovertemplate=f'Porosité: %{{x:.2f}}%<br>{y_label}: %{{y:.4g}}{y_unit}<extra>F1 Référence</extra>',
        ))

    fig = go.Figure(traces)
    fig.update_layout(**lay(h=280, lg=True,
        xaxis=dict(title='Porosité (%)', showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title=y_label + (f' ({y_unit})' if y_unit else ''),
                   type='log' if y_log else 'linear',
                   gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        margin=dict(l=60, r=16, t=18, b=46),
        legend=dict(orientation='h', yanchor='bottom', y=1.04, xanchor='left', x=0,
                    font=dict(size=10, color=ZN700)),
    ))
    return fig


def build_acoustique():
    gen_rows = []
    for _, r in DF_ACOUS.iterrows():
        is_ref = r['nom'] == 'F1_originel'
        gen_rows.append(html.Tr([
            html.Td(r['nom'].replace('_', ' '),
                    style={'fontWeight': '600' if is_ref else '400',
                           'color': ZN400 if is_ref else ZN700,
                           'fontSize': '0.82rem', 'padding': '11px 14px'}),
            html.Td(f"{r['porosite']*100:.1f} %", className='tabnum',
                    style={'padding': '11px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['tortuosite']:.4f}", className='tabnum',
                    style={'padding': '11px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['sv']:.2f}", className='tabnum',
                    style={'padding': '11px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['lambda_v_um']:.1f}", className='tabnum',
                    style={'padding': '11px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['lambda_t_um']:.1f}", className='tabnum',
                    style={'padding': '11px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['sigma']:,.0f}", className='tabnum',
                    style={'padding': '11px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
        ], style={'background': '#FAFAFA' if is_ref else CARD}))

    th_style = {'fontSize': '0.68rem', 'fontWeight': '600', 'textTransform': 'uppercase',
                'letterSpacing': '0.07em', 'color': ZN400, 'padding': '0 14px 12px 14px',
                'borderBottom': f'1px solid {ZN200}', 'textAlign': 'left'}

    acous_table = html.Table([
        html.Thead(html.Tr([
            html.Th('Échantillon', style=th_style),
            html.Th('Porosité φ', style=th_style),
            html.Th('Tortuosité τ', style=th_style),
            html.Th('Sv (mm⁻¹)', style=th_style),
            html.Th('Λ visc. (µm)', style=th_style),
            html.Th('Λ\' therm. (µm)', style=th_style),
            html.Th('σ (N·s·m⁻⁴)', style=th_style),
        ])),
        html.Tbody(gen_rows),
    ], style={'width': '100%', 'borderCollapse': 'collapse'})

    return html.Div([

        insight(
            'Ces 4 échantillons générés numériquement permettent d\'étudier comment la microstructure '
            'fibreuse influence les propriétés acoustiques macroscopiques (modèle JCAL). '
            'La porosité varie de 87.7 % à 95 % — on observe des tendances claires sur chaque paramètre.',
            color=ZN800, bg=ZN100, border=ZN200,
        ),

        card(chart_head('Paramètres JCAL — Tableau récapitulatif',
                        '★ F1 Référence = scan réel · F1–F4 Génér. = structures numériques'),
             acous_table),

        # Sv et Tortuosité
        grid(
            card(chart_head('Surface spécifique Sv en fonction de la porosité',
                            'Sv augmente quand la porosité diminue → fibres plus serrées'),
                 G(_acous_scatter('sv', 'Sv', y_unit='mm⁻¹')), mb='0'),
            card(chart_head('Tortuosité en fonction de la porosité',
                            'Tortuosité ↑ quand porosité ↓ → chemin plus tortueux pour l\'air'),
                 G(_acous_scatter('tortuosite', 'Tortuosité')), mb='0'),
        ),

        # Longueurs caractéristiques
        grid(
            card(chart_head('Longueur visqueuse Λ en fonction de la porosité',
                            'Λ ↓ quand Sv ↑ → pores plus petits, dissipation visqueuse plus forte'),
                 G(_acous_scatter('lambda_v_um', 'Λ visqueuse', y_unit='µm')), mb='0'),
            card(chart_head('Longueur thermique Λ\' en fonction de la porosité',
                            'Λ\' > Λ : l\'échange thermique agit à une plus grande échelle que la viscosité'),
                 G(_acous_scatter('lambda_t_um', 'Λ\' thermique', y_unit='µm')), mb='0'),
        ),

        # Résistivité (log scale car ×100 entre F1 et F4)
        card(chart_head('Résistivité au flux σ en fonction de la porosité',
                        'Échelle logarithmique — σ varie sur 2 ordres de grandeur entre F1 et F4'),
             G(_acous_scatter('sigma', 'σ', y_log=True, y_unit='N·s·m⁻⁴'))),

        # Explication JCAL
        card(
            html.Div('Modèle JCAL — Paramètres clés', style={
                'fontSize': '0.67rem', 'fontWeight': '600', 'color': ZN400,
                'letterSpacing': '0.08em', 'textTransform': 'uppercase', 'marginBottom': '14px',
            }),
            html.Div([
                html.Div([
                    html.Div('Sv — Surface spécifique volumique', style={'fontWeight': '600', 'fontSize': '0.81rem', 'color': ZN800, 'marginBottom': '3px'}),
                    html.Div('Rapport surface/volume du réseau poreux. Lié au diamètre des fibres : d ≈ 4(1−φ)/Sv. Plus Sv est élevé, plus les fibres sont fines.', style={'fontSize': '0.77rem', 'color': ZN500, 'lineHeight': '1.5'}),
                ], style={'marginBottom': '12px'}),
                html.Div([
                    html.Div('Λ — Longueur visqueuse', style={'fontWeight': '600', 'fontSize': '0.81rem', 'color': ZN800, 'marginBottom': '3px'}),
                    html.Div('Caractérise la dissipation d\'énergie par viscosité dans les constrictions. Λ ≈ 2V_pore / S_pore pour les sections les plus étroites.', style={'fontSize': '0.77rem', 'color': ZN500, 'lineHeight': '1.5'}),
                ], style={'marginBottom': '12px'}),
                html.Div([
                    html.Div('σ — Résistivité au flux d\'air', style={'fontWeight': '600', 'fontSize': '0.81rem', 'color': ZN800, 'marginBottom': '3px'}),
                    html.Div('Résistance globale à l\'écoulement de l\'air à travers le matériau. Paramètre clé pour l\'absorption acoustique basse fréquence.', style={'fontSize': '0.77rem', 'color': ZN500, 'lineHeight': '1.5'}),
                ]),
            ]),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  APP & LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

TAB_STYLE = dict(
    color=ZN500, fontFamily=FONT, fontSize='0.83rem',
    padding='14px 20px', border='none', fontWeight='500',
    borderBottom='2px solid transparent', background='transparent',
)
TAB_SEL = {**TAB_STYLE, 'color': ZN900, 'borderBottom': f'2px solid {ZN900}', 'fontWeight': '600'}

app = dash.Dash(__name__, title='FiberScope', suppress_callback_exceptions=True,
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
    ],
)
server = app.server

app.layout = html.Div([

    html.Div([
        html.Div([
            html.Div([
                html.Span('FiberScope', style={'fontSize': '1rem', 'fontWeight': '800',
                                               'color': ZN900, 'letterSpacing': '-0.03em'}),
                html.Span(' · Dragonfly vs MATLAB', style={'fontSize': '0.83rem', 'color': ZN500,
                                                            'fontWeight': '400', 'marginLeft': '6px'}),
            ]),
            html.Div('ESIEE Paris · MSME CNRS UMR 8208 · Projet E4',
                     style={'fontSize': '0.75rem', 'color': ZN400, 'fontWeight': '500'}),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                  'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 24px'}),
    ], style={'background': CARD, 'borderBottom': f'1px solid {ZN200}', 'padding': '16px 0'}),

    dcc.Tabs(id='tabs', value='overview',
        style={'background': CARD, 'borderBottom': f'1px solid {ZN200}', 'paddingLeft': '18px'},
        children=[
            dcc.Tab(label='Vue d\'ensemble',        value='overview',    style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Orientation',            value='orient',      style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Morphologie',            value='morphologie', style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Comparaison',            value='compare',     style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Propriétés acoustiques', value='acoustique',  style=TAB_STYLE, selected_style=TAB_SEL),
        ],
    ),

    html.Div(id='content', style={'maxWidth': '1400px', 'margin': '0 auto'}),

    html.Div([
        html.Span('FiberScope', style={'fontWeight': '600', 'color': ZN700}),
        html.Span(f' · Dragonfly {VOX_UM} µm/vox (F1 Recyclé) · MATLAB ~10 µm/vox · '
                  f'{len(FIB)} fibres · {len(DF_NOL)} composantes · Porosité ~{POROSITY}%',
                  className='tabnum'),
    ], style={'textAlign': 'center', 'padding': '20px', 'fontSize': '0.72rem',
              'color': ZN400, 'borderTop': f'1px solid {ZN200}'}),

], style={'fontFamily': FONT, 'background': BG, 'minHeight': '100vh'})


@app.callback(Output('content', 'children'), Input('tabs', 'value'))
def render(tab):
    if tab == 'overview':    return build_overview()
    if tab == 'orient':      return build_orientation()
    if tab == 'morphologie': return build_morphologie()
    if tab == 'compare':     return build_comparaison()
    if tab == 'acoustique':  return build_acoustique()
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
    fig.update_layout(**lay(h=285, lg=(method == 'both'), barmode='overlay',
        xaxis=dict(title='Inclinaison depuis l\'horizontale (°)', range=[0, 90],
                   showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        margin=dict(l=52, r=16, t=10, b=46),
    ))
    return fig


if __name__ == '__main__':
    app.run(debug=False, port=8052)
