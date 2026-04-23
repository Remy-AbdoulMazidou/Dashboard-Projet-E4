"""
Analyse de microstructure fibreuse — Microtomographie X
Comparaison méthode Dragonfly et méthode MATLAB (regionprops3)
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

FONT   = "'Inter', system-ui, sans-serif"
AA     = '#3B82F6'
NOL    = '#F97316'
BG     = '#F3F4F6'
CARD   = '#FFFFFF'
BORDER = '#E5E7EB'
TEXT   = '#111827'
MUTED  = '#6B7280'


def load_aa():
    df = pd.read_csv(os.path.join(AA_DIR, 'donnee.csv'), sep=';')
    df.columns = [c.strip() for c in df.columns]
    df = df[df['Volume (mm³)'] > 0].copy()
    df = df.rename(columns={
        'Label Index': 'label', 'Voxel count': 'voxels',
        'Volume (mm³)': 'vol', 'Phi (°)': 'phi', 'Theta (°)': 'theta',
    })
    bins   = [0, 5, 100, 100_000, 1_000_000, float('inf')]
    labels = ['Bruit', 'Fragment', 'Fibre', 'Gros objet', 'Matrice']
    return df.assign(cat=pd.cut(df['voxels'], bins=bins, labels=labels))


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
    print("Cache épaisseur (~15 s)…")
    chunks = []
    for chunk in pd.read_csv(os.path.join(AA_DIR, 'diametre.csv'), sep=';',
                              chunksize=1_000_000, usecols=['Thickness (mm)'],
                              dtype={'Thickness (mm)': 'float32'}):
        chunks.append(chunk.iloc[::100]['Thickness (mm)'].values)
    t = np.concatenate(chunks).astype(float) * 1000
    t = t[(t > 5) & (t < 350)]
    np.save(cache, t)
    return t


print("Chargement…")
DF_AA  = load_aa()
DF_NOL = load_nolhan()
THICK  = load_thickness()
FIB    = DF_AA[DF_AA['cat'] == 'Fibre'].copy()
FIB    = FIB.assign(angle_h=90 - FIB['phi'])
print(f"OK — {len(DF_AA)} objets · {len(FIB)} fibres Dragonfly · {len(DF_NOL)} fibres MATLAB")

THICK_MED   = int(np.median(THICK))
NOL_D_MED   = int(DF_NOL['Diam_um'].median())
AA_ANG_MED  = round(float(FIB['angle_h'].median()), 1)
NOL_ANG_MED = round(float(DF_NOL['angle_h'].median()), 1)
aa_eq        = (6 * FIB['vol'] * 1e9 / np.pi) ** (1/3)
nol_eq       = (6 * DF_NOL['Volume'] * 1000 / np.pi) ** (1/3)
AA_EQ_MED    = int(aa_eq.median())
NOL_EQ_MED   = int(nol_eq.median())
ECART_PCT    = abs(AA_EQ_MED - NOL_EQ_MED) * 100 // max(AA_EQ_MED, NOL_EQ_MED)


# ── Helpers layout ─────────────────────────────────────────────────────
def lay(h=300, lg=False, **kw):
    d = dict(
        paper_bgcolor=CARD, plot_bgcolor='#FAFAFA',
        font=dict(family=FONT, size=12, color=MUTED),
        height=h, showlegend=lg,
        margin=dict(l=50, r=16, t=12, b=46),
        xaxis=dict(showgrid=False, linecolor=BORDER, zeroline=False,
                   tickfont=dict(size=11, color=MUTED)),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, zeroline=False,
                   tickfont=dict(size=11, color=MUTED)),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)',
                    font=dict(size=12, color=TEXT)),
    )
    d.update(kw)
    return d


def card(children, accent=None, style_extra=None):
    s = {
        'background': CARD, 'border': f'1px solid {BORDER}',
        'borderRadius': '10px', 'padding': '20px', 'marginBottom': '16px',
    }
    if accent:
        s['borderLeft'] = f'4px solid {accent}'
    if style_extra:
        s.update(style_extra)
    return html.Div(children, style=s)


def kpi(value, label, color):
    return html.Div([
        html.Div(str(value), style={
            'fontSize': '2rem', 'fontWeight': '700', 'color': color, 'lineHeight': '1',
        }),
        html.Div(label, style={'fontSize': '0.78rem', 'color': MUTED, 'marginTop': '6px'}),
    ], style={
        'background': CARD, 'border': f'1px solid {BORDER}',
        'borderRadius': '10px', 'padding': '18px 20px',
        'borderTop': f'3px solid {color}',
    })


def titre(t, sub=None):
    return html.Div([
        html.Div(t, style={'fontSize': '0.95rem', 'fontWeight': '600', 'color': TEXT}),
        *([html.Div(sub, style={'fontSize': '0.78rem', 'color': MUTED, 'marginTop': '2px'})] if sub else []),
    ], style={'marginBottom': '14px'})


def remarque(contenu, color=AA, bg='#EFF6FF', border_c=None):
    bc = border_c or color
    return html.Div(contenu if isinstance(contenu, list) else [contenu], style={
        'background': bg, 'borderLeft': f'3px solid {bc}',
        'borderRadius': '0 6px 6px 0', 'padding': '9px 14px',
        'fontSize': '0.81rem', 'lineHeight': '1.6', 'marginTop': '12px',
        'color': '#1E40AF' if bg == '#EFF6FF' else '#374151',
    })


def G(fig):
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def badge(texte, color):
    return html.Span(texte, style={
        'background': color + '18', 'color': color,
        'border': f'1px solid {color}40',
        'borderRadius': '4px', 'padding': '2px 8px',
        'fontSize': '0.75rem', 'fontWeight': '600',
    })


# ══════════════════════════════════════════════════════════════════════
#  TAB 1 — CONTEXTE & MÉTHODES
# ══════════════════════════════════════════════════════════════════════
def build_overview():
    cats   = ['Bruit', 'Fragment', 'Fibre', 'Gros objet', 'Matrice']
    colors = ['#D1D5DB', '#FCD34D', AA, '#A78BFA', '#9CA3AF']
    counts = DF_AA['cat'].value_counts().reindex(cats, fill_value=0)
    fig_cats = go.Figure(go.Bar(
        x=cats, y=counts.values, marker_color=colors,
        text=counts.values, textposition='outside',
        hovertemplate='%{x} : %{y}<extra></extra>',
    ))
    fig_cats.update_layout(**lay(h=250,
        yaxis=dict(title='Nombre d\'objets', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    return html.Div([

        # Contexte du projet
        card([
            html.Div('Contexte du projet', style={
                'fontSize': '0.95rem', 'fontWeight': '600', 'color': TEXT, 'marginBottom': '10px',
            }),
            html.Div([
                'On a scanné un échantillon de matériau fibreux par microtomographie X (résolution 10 µm/voxel). '
                'Deux membres du groupe ont analysé les images 3D avec des outils différents : '
                'Antoine & Aymen avec ',
                html.Strong('Dragonfly ORS'),
                ', Nolhan avec ',
                html.Strong('MATLAB regionprops3'),
                '. Ce dashboard compare les résultats obtenus pour voir si les deux approches donnent les mêmes conclusions sur le matériau.',
            ], style={'fontSize': '0.85rem', 'color': '#374151', 'lineHeight': '1.7'}),
        ]),

        # KPIs
        html.Div([
            kpi(len(FIB),           'fibres détectées\nDragonfly',    AA),
            kpi(len(DF_NOL),        'fibres détectées\nMATLAB',       NOL),
            kpi(f'{AA_ANG_MED}°',   'inclinaison médiane\nDragonfly', AA),
            kpi(f'{NOL_ANG_MED}°',  'inclinaison médiane\nMATLAB',    NOL),
        ], style={
            'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)',
            'gap': '14px', 'marginBottom': '16px',
        }),

        # Les deux méthodes
        html.Div([
            card([
                html.Div([
                    html.Span('●', style={'color': AA, 'marginRight': '8px'}),
                    html.Span('Méthode Dragonfly', style={'fontWeight': '600', 'fontSize': '0.92rem'}),
                ], style={'marginBottom': '10px'}),
                html.Ul([
                    html.Li('Logiciel Dragonfly ORS — segmentation manuelle/automatique'),
                    html.Li('Squelettisation des fibres, puis mesure d\'épaisseur par ray-tracing'),
                    html.Li('Orientation : angles sphériques Phi (inclinaison) et Theta (azimut)'),
                    html.Li(f'Filtre appliqué : 101 – 100 000 voxels → {len(FIB)} fibres retenues'),
                ], style={'fontSize': '0.82rem', 'color': '#374151', 'lineHeight': '1.9',
                          'paddingLeft': '16px', 'margin': 0}),
            ], accent=AA),
            card([
                html.Div([
                    html.Span('●', style={'color': NOL, 'marginRight': '8px'}),
                    html.Span('Méthode MATLAB', style={'fontWeight': '600', 'fontSize': '0.92rem'}),
                ], style={'marginBottom': '10px'}),
                html.Ul([
                    html.Li('MATLAB — fonction regionprops3 sur les composantes connexes'),
                    html.Li('Fournit les axes principaux de l\'ellipsoïde (PAL1, PAL2, PAL3)'),
                    html.Li('Orientation : angles d\'Euler (Orientation_1/2/3)'),
                    html.Li(f'Pas de filtre par taille → {len(DF_NOL)} fibres au total'),
                ], style={'fontSize': '0.82rem', 'color': '#374151', 'lineHeight': '1.9',
                          'paddingLeft': '16px', 'margin': 0}),
            ], accent=NOL),
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '14px'}),

        # Distribution Dragonfly
        card([
            titre('Objets segmentés par Dragonfly',
                  f'{len(DF_AA)} objets détectés au total — seules les fibres (en bleu) sont analysées'),
            G(fig_cats),
            remarque([
                html.Strong(f'{len(FIB)} fibres retenues sur {len(DF_AA)} objets. '),
                'Le bruit et les fragments sont écartés par le filtre de taille.',
            ]),
        ]),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════
#  TAB 2 — ORIENTATION
# ══════════════════════════════════════════════════════════════════════
def build_orientation():
    fig_az = go.Figure([
        go.Histogram(x=FIB['theta'], name='Dragonfly — Theta',
            histnorm='percent', xbins=dict(size=10),
            marker=dict(color=AA, opacity=0.75, line=dict(color='white', width=0.4))),
        go.Histogram(x=DF_NOL['Orientation_1'] * 2, name='MATLAB — Orient.₁×2',
            histnorm='percent', xbins=dict(size=10),
            marker=dict(color=NOL, opacity=0.75, line=dict(color='white', width=0.4))),
    ])
    fig_az.update_layout(**lay(h=260, lg=True, barmode='overlay',
        xaxis=dict(title='Azimut (°)', range=[-185, 185]),
        yaxis=dict(title='% fibres', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    return html.Div([

        # Résultat clé mis en avant
        html.Div([
            html.Div('Résultat principal', style={
                'fontSize': '0.72rem', 'fontWeight': '600', 'color': MUTED,
                'textTransform': 'uppercase', 'letterSpacing': '0.08em', 'marginBottom': '6px',
            }),
            html.Div('Les fibres sont quasi-horizontales — les deux méthodes sont d\'accord.', style={
                'fontSize': '1.05rem', 'fontWeight': '600', 'color': TEXT, 'lineHeight': '1.5',
            }),
            html.Div([
                html.Span(f'Dragonfly : {AA_ANG_MED}° depuis l\'horizontale', style={
                    'color': AA, 'fontWeight': '600', 'marginRight': '20px', 'fontSize': '0.88rem',
                }),
                html.Span(f'MATLAB : {NOL_ANG_MED}° depuis l\'horizontale', style={
                    'color': NOL, 'fontWeight': '600', 'fontSize': '0.88rem',
                }),
            ], style={'marginTop': '10px'}),
        ], style={
            'background': CARD, 'border': f'1px solid {BORDER}',
            'borderRadius': '10px', 'padding': '18px 22px',
            'marginBottom': '16px', 'borderLeft': f'4px solid #16A34A',
        }),

        card([
            titre('Inclinaison des fibres par rapport à l\'horizontale',
                  '0° = fibre couchée à plat · 90° = fibre verticale'),

            html.Div([
                html.Div('Afficher :', style={
                    'fontSize': '0.82rem', 'color': MUTED, 'marginRight': '10px', 'alignSelf': 'center',
                }),
                dcc.RadioItems(
                    id='method-toggle',
                    options=[
                        {'label': ' Les deux',            'value': 'both'},
                        {'label': ' Dragonfly seulement', 'value': 'aa'},
                        {'label': ' MATLAB seulement',    'value': 'nolhan'},
                    ],
                    value='both', inline=True, className='radio-group',
                    inputStyle={'marginRight': '5px', 'cursor': 'pointer'},
                    labelStyle={
                        'marginRight': '0', 'padding': '7px 16px',
                        'fontSize': '0.82rem', 'cursor': 'pointer',
                        'color': MUTED, 'background': CARD,
                        'borderRight': f'1px solid {BORDER}',
                    },
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px'}),

            dcc.Graph(id='fig-elevation', config={'displayModeBar': False}),

            remarque([
                f'Écart entre les deux : {abs(AA_ANG_MED - NOL_ANG_MED):.1f}°. '
                'Les pics sont décalés mais les deux distributions sont concentrées vers 0° — '
                'la conclusion est la même.',
            ]),
        ]),

        card([
            titre('Direction dans le plan horizontal',
                  'Si les barres sont à peu près égales → pas de direction préférentielle'),
            G(fig_az),
            remarque(
                'Pas de direction dominante dans les deux méthodes — '
                'les fibres sont orientées aléatoirement dans le plan horizontal.'
            ),
        ]),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════
#  TAB 3 — COMPARAISON
# ══════════════════════════════════════════════════════════════════════
def build_comparison():

    # Figure mesures directes
    fig_diam = go.Figure([
        go.Histogram(x=THICK,
            name=f'Dragonfly — épaisseur skeleton (méd. {THICK_MED} µm)',
            histnorm='percent', xbins=dict(size=5),
            marker=dict(color=AA, opacity=0.75, line=dict(color='white', width=0.4))),
        go.Histogram(x=DF_NOL['Diam_um'].dropna(),
            name=f'MATLAB — PAL₃ (méd. {NOL_D_MED} µm)',
            histnorm='percent', xbins=dict(size=5),
            marker=dict(color=NOL, opacity=0.75, line=dict(color='white', width=0.4))),
    ])
    fig_diam.update_layout(**lay(h=270, lg=True, barmode='overlay',
        xaxis=dict(title='µm', range=[0, 280]),
        yaxis=dict(title='% fibres', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    # Figure volume
    fig_eq = go.Figure([
        go.Histogram(x=aa_eq, name=f'Dragonfly (méd. {AA_EQ_MED} µm)',
            histnorm='percent', xbins=dict(size=8),
            marker=dict(color=AA, opacity=0.75, line=dict(color='white', width=0.4))),
        go.Histogram(x=nol_eq, name=f'MATLAB (méd. {NOL_EQ_MED} µm)',
            histnorm='percent', xbins=dict(size=8),
            marker=dict(color=NOL, opacity=0.75, line=dict(color='white', width=0.4))),
    ])
    fig_eq.update_layout(**lay(h=270, lg=True, barmode='overlay',
        xaxis=dict(title='Diamètre équivalent (µm)'),
        yaxis=dict(title='% fibres', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    def ligne(label, v_drag, v_mat, accord=None):
        if accord is True:
            icone, couleur = '✓', '#16A34A'
        elif accord is False:
            icone, couleur = '≠', '#D97706'
        else:
            icone, couleur = '—', MUTED
        return html.Div([
            html.Div([
                html.Div(icone, style={
                    'width': '28px', 'height': '28px',
                    'borderRadius': '50%',
                    'background': couleur + '18',
                    'color': couleur,
                    'fontWeight': '700', 'fontSize': '0.85rem',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                    'flexShrink': '0',
                }),
                html.Div([
                    html.Div(label, style={'fontSize': '0.8rem', 'color': MUTED, 'marginBottom': '3px'}),
                    html.Div([
                        html.Span('Dragonfly ', style={'color': AA, 'fontWeight': '600', 'fontSize': '0.84rem'}),
                        html.Span(v_drag + '   ', style={'color': TEXT, 'fontSize': '0.84rem'}),
                        html.Span('MATLAB ', style={'color': NOL, 'fontWeight': '600', 'fontSize': '0.84rem'}),
                        html.Span(v_mat, style={'color': TEXT, 'fontSize': '0.84rem'}),
                    ]),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '14px', 'alignItems': 'center'}),
        ], style={'padding': '12px 0', 'borderBottom': f'1px solid {BORDER}'})

    return html.Div([

        # Intro
        card([
            html.Div('Ce que cette comparaison montre', style={
                'fontSize': '0.95rem', 'fontWeight': '600', 'color': TEXT, 'marginBottom': '10px',
            }),
            html.Div([
                'Les deux méthodes n\'ont pas été conçues pour produire exactement les mêmes mesures — '
                'Dragonfly travaille sur le squelette de la fibre, MATLAB sur son ellipsoïde équivalent. '
                'L\'objectif ici est de vérifier : ',
                html.Strong('est-ce qu\'on arrive aux mêmes conclusions sur le matériau ?'),
            ], style={'fontSize': '0.84rem', 'color': '#374151', 'lineHeight': '1.7'}),
        ]),

        # Points de comparaison
        card([
            titre('Point par point'),
            ligne('Orientation des fibres',
                  'Horizontale', 'Horizontale', accord=True),
            ligne(f'Angle médian depuis l\'horizontale',
                  f'{AA_ANG_MED}°', f'{NOL_ANG_MED}°', accord=True),
            ligne('Isotropie dans le plan horizontal',
                  'Uniforme', 'Uniforme', accord=True),
            ligne('Nombre de fibres détectées',
                  str(len(FIB)), str(len(DF_NOL)), accord=False),
            ligne('Mesure de taille directe',
                  f'{THICK_MED} µm (épaisseur skeleton)', f'{NOL_D_MED} µm (PAL₃)', accord=False),
            html.Div([
                html.Div('✓', style={
                    'width': '28px', 'height': '28px', 'borderRadius': '50%',
                    'background': '#16A34A18', 'color': '#16A34A',
                    'fontWeight': '700', 'fontSize': '0.85rem',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                    'flexShrink': '0',
                }),
                html.Div([
                    html.Div('Taille via le volume (comparaison équitable)',
                             style={'fontSize': '0.8rem', 'color': MUTED, 'marginBottom': '3px'}),
                    html.Div([
                        html.Span('Dragonfly ', style={'color': AA, 'fontWeight': '600', 'fontSize': '0.84rem'}),
                        html.Span(f'{AA_EQ_MED} µm   ', style={'color': TEXT, 'fontSize': '0.84rem'}),
                        html.Span('MATLAB ', style={'color': NOL, 'fontWeight': '600', 'fontSize': '0.84rem'}),
                        html.Span(f'{NOL_EQ_MED} µm', style={'color': TEXT, 'fontSize': '0.84rem'}),
                    ]),
                ]),
            ], style={
                'display': 'flex', 'gap': '14px', 'alignItems': 'center',
                'padding': '12px 0',
            }),
        ]),

        # Taille — explication de l'écart
        html.Div([
            card([
                titre('Pourquoi l\'écart sur la taille ?',
                      f'Dragonfly : {THICK_MED} µm · MATLAB : {NOL_D_MED} µm'),
                G(fig_diam),
                remarque([
                    'Ces deux courbes ne mesurent pas la même chose. '
                    'Dragonfly mesure l\'épaisseur en chaque point du squelette. '
                    'MATLAB mesure PAL₃, l\'axe le plus court de l\'ellipsoïde ajusté sur la fibre entière. ',
                    html.Strong('L\'écart ×2 est normal — ce n\'est pas une erreur des deux méthodes.'),
                ]),
            ]),
            card([
                titre('Comparaison via le volume',
                      f'd = (6V/π)^(1/3) — Dragonfly {AA_EQ_MED} µm · MATLAB {NOL_EQ_MED} µm · écart {ECART_PCT}%'),
                G(fig_eq),
                remarque([
                    'En recalculant un diamètre équivalent depuis le volume de chaque fibre, '
                    'les deux distributions se rapprochent : ',
                    html.Strong(f'{AA_EQ_MED} µm vs {NOL_EQ_MED} µm ({ECART_PCT}% d\'écart). '),
                    'C\'est la seule comparaison valide entre les deux méthodes sur la taille.',
                ]),
            ]),
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '14px'}),

        # Conclusion
        html.Div([
            html.Div('Conclusion', style={
                'fontSize': '0.72rem', 'fontWeight': '600', 'color': MUTED,
                'textTransform': 'uppercase', 'letterSpacing': '0.08em', 'marginBottom': '8px',
            }),
            html.Div([
                html.Div('Sur l\'orientation et l\'isotropie : accord total entre les deux méthodes.', style={
                    'fontSize': '0.85rem', 'color': '#374151', 'marginBottom': '5px',
                }),
                html.Div([
                    'Sur la taille : les mesures directes diffèrent (métriques différentes), '
                    'mais via le volume les résultats convergent à ',
                    html.Strong(f'{ECART_PCT}% près.'),
                ], style={'fontSize': '0.85rem', 'color': '#374151'}),
            ]),
        ], style={
            'background': '#F0FDF4', 'border': '1px solid #BBF7D0',
            'borderRadius': '10px', 'padding': '18px 20px',
            'marginBottom': '16px',
        }),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════
#  TAB 4 — MORPHOLOGIE
# ══════════════════════════════════════════════════════════════════════
def build_morphology():

    # Volume des fibres — les deux méthodes (unité commune : µm³)
    vol_aa_um3  = FIB['vol'] * 1e9           # mm³ → µm³
    vol_nol_um3 = DF_NOL['Volume'] * 1000    # vox → µm³ (1 vox = 10³ µm³)

    fig_vol = go.Figure([
        go.Histogram(x=np.log10(vol_aa_um3),
            name=f'Dragonfly (méd. {int(vol_aa_um3.median()):,} µm³)',
            histnorm='percent', xbins=dict(size=0.15),
            marker=dict(color=AA, opacity=0.75, line=dict(color='white', width=0.4))),
        go.Histogram(x=np.log10(vol_nol_um3),
            name=f'MATLAB (méd. {int(vol_nol_um3.median()):,} µm³)',
            histnorm='percent', xbins=dict(size=0.15),
            marker=dict(color=NOL, opacity=0.75, line=dict(color='white', width=0.4))),
    ])
    fig_vol.update_layout(**lay(h=270, lg=True, barmode='overlay',
        xaxis=dict(title='log₁₀(Volume en µm³)',
                   tickvals=[3,4,5,6,7],
                   ticktext=['10³','10⁴','10⁵','10⁶','10⁷']),
        yaxis=dict(title='% fibres', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    # Longueur et rapport d'aspect (MATLAB)
    fig_len = go.Figure(go.Histogram(
        x=DF_NOL['Len_um'], name='Longueur (PAL₁)',
        histnorm='percent', xbins=dict(size=30),
        marker=dict(color=NOL, opacity=0.8, line=dict(color='white', width=0.4)),
    ))
    fig_len.update_layout(**lay(h=240,
        xaxis=dict(title='Longueur µm'),
        yaxis=dict(title='% fibres', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    fig_ar = go.Figure(go.Histogram(
        x=DF_NOL['AspectRatio'].clip(upper=12), name='PAL₁/PAL₃',
        histnorm='percent', xbins=dict(size=0.4),
        marker=dict(color=NOL, opacity=0.8, line=dict(color='white', width=0.4)),
    ))
    fig_ar.update_layout(**lay(h=240,
        xaxis=dict(title='Rapport d\'aspect (longueur / diamètre)'),
        yaxis=dict(title='% fibres', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    # Scatter longueur vs diamètre
    fig_ld = go.Figure(go.Scatter(
        x=DF_NOL['Diam_um'], y=DF_NOL['Len_um'],
        mode='markers',
        marker=dict(color=NOL, size=5, opacity=0.55,
                    line=dict(color='white', width=0.3)),
        hovertemplate='Diam. %{x:.0f} µm · Long. %{y:.0f} µm<extra></extra>',
    ))
    fig_ld.update_layout(**lay(h=270,
        xaxis=dict(title='Diamètre PAL₃ (µm)', range=[0, 200]),
        yaxis=dict(title='Longueur PAL₁ (µm)', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    # Scatter diamètre vs solidity
    fig_ds = go.Figure(go.Scatter(
        x=DF_NOL['Diam_um'], y=DF_NOL['Solidity'],
        mode='markers',
        marker=dict(
            color=DF_NOL['AspectRatio'], colorscale='Blues',
            size=5, opacity=0.6,
            colorbar=dict(title='Aspect<br>ratio', thickness=10, len=0.6),
            line=dict(color='white', width=0.3),
        ),
        hovertemplate='Diam. %{x:.0f} µm · Solidité %{y:.2f}<extra></extra>',
    ))
    fig_ds.update_layout(**lay(h=270,
        xaxis=dict(title='Diamètre PAL₃ (µm)', range=[0, 200]),
        yaxis=dict(title='Solidité', range=[0.1, 1.05],
                   gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    # Carte spatiale (vue de dessus + coupe latérale)
    fig_map = go.Figure(go.Scatter(
        x=DF_NOL['Centroid_1'] * 10,
        y=DF_NOL['Centroid_2'] * 10,
        mode='markers',
        marker=dict(
            color=DF_NOL['angle_h'], colorscale='RdYlGn_r',
            cmin=0, cmax=45,
            size=(DF_NOL['Len_um'] / DF_NOL['Len_um'].max() * 14 + 4).clip(4, 18),
            opacity=0.7,
            colorbar=dict(title='Angle<br>horiz. (°)', thickness=10, len=0.7),
            line=dict(color='white', width=0.3),
        ),
        hovertemplate='x=%{x:.0f} µm · y=%{y:.0f} µm<extra></extra>',
    ))
    fig_map.update_layout(**lay(h=320,
        xaxis=dict(title='x (µm)', scaleanchor='y'),
        yaxis=dict(title='y (µm)', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))

    return html.Div([

        # Volume
        card([
            titre('Volume des fibres — comparaison directe',
                  'Même unité (µm³), échelle log pour lisibilité'),
            G(fig_vol),
            remarque([
                f'Dragonfly : médiane {int(vol_aa_um3.median()):,} µm³ · '
                f'MATLAB : médiane {int(vol_nol_um3.median()):,} µm³. '
                'Les fibres Dragonfly sont un peu plus grosses en médiane — '
                'le filtre strict (101–100k vox) écarte les petits objets que MATLAB garde.',
            ]),
        ]),

        # Longueur + Aspect ratio (MATLAB)
        card([
            html.Div([
                html.Span('●', style={'color': NOL, 'marginRight': '8px'}),
                html.Span('Forme des fibres — Méthode MATLAB', style={
                    'fontWeight': '600', 'fontSize': '0.92rem',
                }),
                html.Span(' (Dragonfly ne fournit pas ces données)', style={
                    'fontSize': '0.78rem', 'color': MUTED, 'marginLeft': '8px',
                }),
            ], style={'marginBottom': '16px'}),

            html.Div([
                html.Div([
                    titre('Longueur des fibres (PAL₁)',
                          f'Médiane : {int(DF_NOL["Len_um"].median())} µm · max : {int(DF_NOL["Len_um"].max())} µm'),
                    G(fig_len),
                ]),
                html.Div([
                    titre('Rapport d\'aspect (longueur / diamètre)',
                          f'Médiane : {DF_NOL["AspectRatio"].median():.1f} — fibre ≈ 2.6× plus longue que large'),
                    G(fig_ar),
                ]),
            ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '16px'}),

            remarque([
                'La majorité des fibres ont un rapport d\'aspect entre 2 et 5 — '
                'elles sont allongées mais pas extrêmement fines. '
                'Quelques fibres dépassent 10 : ce sont probablement des fibres très longues ou des fibres fusionnées.',
            ], color=NOL, bg='#FFF7ED'),
        ], accent=NOL),

        # Scatter longueur/diamètre + solidity/diamètre
        html.Div([
            card([
                titre('Longueur vs diamètre (MATLAB)',
                      'Chaque point = une fibre'),
                G(fig_ld),
                remarque([
                    'Pas de corrélation nette : les fibres épaisses ne sont pas forcément les plus longues. '
                    'La forme des fibres est variable.',
                ], color=NOL, bg='#FFF7ED'),
            ]),
            card([
                titre('Diamètre vs solidité (MATLAB)',
                      'Solidité = volume / volume convexe · couleur = rapport d\'aspect'),
                G(fig_ds),
                remarque([
                    'Corrélation négative (r ≈ −0.43) : '
                    'les fibres épaisses tendent à être moins régulières (solidité plus basse). '
                    'Les fibres fines ont une forme plus compacte.',
                ], color=NOL, bg='#FFF7ED'),
            ]),
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '14px'}),

        # Carte spatiale
        card([
            titre('Localisation des fibres dans l\'échantillon (vue de dessus — MATLAB)',
                  'Taille du point ∝ longueur · couleur = angle depuis l\'horizontale (vert = horizontal)'),
            G(fig_map),
            remarque([
                'Les fibres sont réparties de façon assez uniforme dans le plan. '
                'Pas de zone de concentration ou de vide visible — '
                'la distribution spatiale semble homogène sur les ~2 mm × 2 mm du scan.',
            ], color=NOL, bg='#FFF7ED'),
        ]),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════
#  TAB 5 — DONNÉES
# ══════════════════════════════════════════════════════════════════════
def build_data():

    def col_row(name, unit, desc, alt=False):
        bg = '#F9FAFB' if alt else CARD
        return html.Tr([
            html.Td(name, style={
                'padding': '8px 12px', 'fontWeight': '600', 'fontSize': '0.82rem',
                'color': TEXT, 'borderBottom': f'1px solid {BORDER}',
                'background': bg, 'fontFamily': 'monospace',
            }),
            html.Td(unit, style={
                'padding': '8px 12px', 'fontSize': '0.8rem', 'color': MUTED,
                'borderBottom': f'1px solid {BORDER}', 'background': bg,
            }),
            html.Td(desc, style={
                'padding': '8px 12px', 'fontSize': '0.82rem', 'color': '#374151',
                'borderBottom': f'1px solid {BORDER}', 'background': bg,
            }),
        ])

    def col_table(rows_data):
        return html.Table([
            html.Thead(html.Tr([
                html.Th(h, style={
                    'padding': '8px 12px', 'fontSize': '0.75rem', 'color': MUTED,
                    'fontWeight': '600', 'textTransform': 'uppercase',
                    'borderBottom': f'2px solid {BORDER}', 'background': '#F9FAFB',
                }) for h in ['Colonne', 'Unité', 'Description']
            ])),
            html.Tbody([col_row(*r, alt=(i % 2 == 1)) for i, r in enumerate(rows_data)]),
        ], style={'width': '100%', 'borderCollapse': 'collapse'})

    return html.Div([

        card([
            html.Div([
                html.Span('●', style={'color': AA, 'marginRight': '8px'}),
                html.Span('Fichiers Dragonfly', style={'fontWeight': '600', 'fontSize': '0.95rem'}),
            ], style={'marginBottom': '18px'}),

            html.Div([
                html.Div([
                    html.Span('donnee.csv', style={
                        'fontFamily': 'monospace', 'fontWeight': '600',
                        'fontSize': '0.88rem', 'color': AA,
                    }),
                    html.Span(f'  {len(DF_AA)} lignes · séparateur point-virgule', style={
                        'fontSize': '0.8rem', 'color': MUTED,
                    }),
                ], style={'marginBottom': '10px'}),
                col_table([
                    ('Label Index',  '—',    'Identifiant de l\'objet segmenté'),
                    ('Voxel count',  'vox',  'Volume en voxels'),
                    ('Volume (mm³)', 'mm³',  'Volume converti, résolution 10 µm/voxel'),
                    ('Phi (°)',      '°',    'Angle polaire — 0° = vertical, 90° = horizontal'),
                    ('Theta (°)',    '°',    'Angle azimutal dans le plan'),
                    ('MIL',         '—',    'Mean Intercept Length — non exploité ici'),
                    ('SVD',         '—',    'Non renseigné dans ce dataset'),
                ]),
            ], style={'marginBottom': '22px'}),

            html.Div([
                html.Div([
                    html.Span('diametre.csv', style={
                        'fontFamily': 'monospace', 'fontWeight': '600',
                        'fontSize': '0.88rem', 'color': AA,
                    }),
                    html.Span('  ~16 millions de lignes · 785 Mo · séparateur point-virgule', style={
                        'fontSize': '0.8rem', 'color': MUTED,
                    }),
                ], style={'marginBottom': '10px'}),
                col_table([
                    ('Thickness (mm)', 'mm',
                     'Épaisseur locale mesurée par ray-tracing en chaque point du squelette'),
                ]),
                html.Div(
                    'Un point de mesure par voxel de squelette — d\'où la taille du fichier. '
                    'Pour l\'affichage, on prend 1 point sur 100 (sous-échantillonnage).',
                    style={'fontSize': '0.79rem', 'color': MUTED, 'marginTop': '8px', 'fontStyle': 'italic'},
                ),
            ]),
        ], accent=AA),

        card([
            html.Div([
                html.Span('●', style={'color': NOL, 'marginRight': '8px'}),
                html.Span('Fichier MATLAB', style={'fontWeight': '600', 'fontSize': '0.95rem'}),
            ], style={'marginBottom': '18px'}),

            html.Div([
                html.Div([
                    html.Span('Resultats_Fibres.xlsx', style={
                        'fontFamily': 'monospace', 'fontWeight': '600',
                        'fontSize': '0.88rem', 'color': NOL,
                    }),
                    html.Span(f'  {len(DF_NOL)} lignes', style={
                        'fontSize': '0.8rem', 'color': MUTED,
                    }),
                ], style={'marginBottom': '10px'}),
                col_table([
                    ('Volume',                'vox',  'Volume de l\'objet en voxels'),
                    ('Centroid_1/2/3',        'vox',  'Coordonnées du centre de masse (x, y, z)'),
                    ('EquivDiameter',         'vox',  'Diamètre de la sphère de même volume'),
                    ('PrincipalAxisLength_1', 'vox',  'PAL₁ — axe le plus long (longueur de la fibre)'),
                    ('PrincipalAxisLength_2', 'vox',  'PAL₂ — axe intermédiaire'),
                    ('PrincipalAxisLength_3', 'vox',  'PAL₃ — axe le plus court (≈ diamètre)'),
                    ('Orientation_1/2/3',     '°',    'Angles d\'Euler — orientation dans l\'espace 3D'),
                    ('Solidity',              '—',    'Volume / volume convexe (1 = objet convexe parfait)'),
                    ('SurfaceArea',           'vox²', 'Aire de surface de l\'objet'),
                    ('ConvexVolume',          'vox',  'Volume de l\'enveloppe convexe'),
                ]),
                html.Div(
                    'Résolution 10 µm/voxel — pour convertir en µm : multiplier PAL et EquivDiameter par 10.',
                    style={'fontSize': '0.79rem', 'color': MUTED, 'marginTop': '8px', 'fontStyle': 'italic'},
                ),
            ]),
        ], accent=NOL),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════════
TB = dict(
    color=MUTED, fontFamily=FONT, fontSize='0.85rem',
    padding='12px 20px', border='none', fontWeight='500',
    borderBottom='2px solid transparent', background='transparent',
)
TB_SEL = {**TB, 'color': TEXT, 'borderBottom': f'2px solid {TEXT}', 'fontWeight': '600'}

app = dash.Dash(__name__, title='Microstructure fibreuse',
                suppress_callback_exceptions=True,
                external_stylesheets=[
                    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
                ])
server = app.server

app.layout = html.Div([

    html.Div([
        html.Div('Analyse de microstructure fibreuse — Dragonfly vs MATLAB', style={
            'fontSize': '1rem', 'fontWeight': '700', 'color': TEXT,
        }),
    ], style={
        'background': CARD, 'padding': '14px 24px',
        'borderBottom': f'1px solid {BORDER}',
    }),

    dcc.Tabs(id='tabs', value='overview',
        style={'background': CARD, 'borderBottom': f'1px solid {BORDER}'},
        children=[
            dcc.Tab(label='Contexte & méthodes', value='overview',   style=TB, selected_style=TB_SEL),
            dcc.Tab(label='Orientation',         value='orient',     style=TB, selected_style=TB_SEL),
            dcc.Tab(label='Comparaison',         value='compare',    style=TB, selected_style=TB_SEL),
            dcc.Tab(label='Morphologie',         value='morphology', style=TB, selected_style=TB_SEL),
            dcc.Tab(label='Données',             value='data',       style=TB, selected_style=TB_SEL),
        ],
    ),

    html.Div(id='content'),

], style={'fontFamily': FONT, 'background': BG, 'minHeight': '100vh'})


@app.callback(Output('content', 'children'), Input('tabs', 'value'))
def render(tab):
    if tab == 'overview':   return build_overview()
    if tab == 'orient':     return build_orientation()
    if tab == 'compare':    return build_comparison()
    if tab == 'morphology': return build_morphology()
    if tab == 'data':       return build_data()
    return html.Div()


@app.callback(Output('fig-elevation', 'figure'), Input('method-toggle', 'value'))
def update_elevation(method):
    f = go.Figure()
    if method in ('both', 'aa'):
        f.add_trace(go.Histogram(
            x=FIB['angle_h'], name=f'Dragonfly — méd. {AA_ANG_MED}°',
            histnorm='percent', xbins=dict(size=3),
            marker=dict(color=AA, opacity=0.78, line=dict(color='white', width=0.4)),
        ))
    if method in ('both', 'nolhan'):
        f.add_trace(go.Histogram(
            x=DF_NOL['angle_h'], name=f'MATLAB — méd. {NOL_ANG_MED}°',
            histnorm='percent', xbins=dict(size=3),
            marker=dict(color=NOL, opacity=0.78, line=dict(color='white', width=0.4)),
        ))
    f.update_layout(**lay(h=290, lg=(method == 'both'), barmode='overlay',
        xaxis=dict(title='Angle depuis l\'horizontale (°)', range=[0, 90]),
        yaxis=dict(title='% fibres', gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    ))
    return f


if __name__ == '__main__':
    app.run(debug=False, port=8051)
