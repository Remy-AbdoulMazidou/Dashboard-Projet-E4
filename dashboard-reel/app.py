"""
FiberScope · Post-traitement comparatif Dragonfly vs MATLAB
Projet E4 ESIEE Paris · MSME UMR 8208 CNRS
"""
import os
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import lognorm as sp_lognorm
from scipy.stats import skew as sp_skew

BASE    = os.path.dirname(os.path.abspath(__file__))
AA_DIR  = os.path.join(BASE, '..', 'vrai-data', 'antoine-aymen')
NOL_DIR = os.path.join(BASE, '..', 'vrai-data', 'nolhan')

# ── Palette ────────────────────────────────────────────────────────────────────
FONT     = "'Inter', system-ui, -apple-system, sans-serif"
INDIGO   = '#6366F1'
EMERALD  = '#10B981'
BG       = '#F8FAFC'
CARD     = '#FFFFFF'
ZN100    = '#F4F4F5'
ZN200    = '#E4E4E7'
ZN300    = '#D4D4D8'
ZN400    = '#A1A1AA'
ZN500    = '#71717A'
ZN700    = '#3F3F46'
ZN800    = '#27272A'
ZN900    = '#18181B'
AMBER    = '#D97706'
GREEN    = '#059669'
RED      = '#E11D48'

GEN_COLORS = ['#60A5FA', '#6366F1', '#7C3AED', '#A855F7']
GEN_LABELS = ['F1 — Généré', 'F2 — Généré', 'F3 — Généré', 'F4 — Généré']
GEN_KEYS   = ['F1_genere', 'F2_genere', 'F3_genere', 'F4_genere']


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
    df['lambda_v_um'] = df['lambda_v'] * 1000
    df['lambda_t_um'] = df['lambda_t'] * 1000
    return df


print("Chargement des données…")
DF_AA    = _load_dragonfly('donnees_F1_recycle.csv')
DF_NOL   = load_nolhan()
THICK    = load_thickness()
DF_ACOUS = load_acoustique()

VOX_UM = 5.50
FIB    = DF_AA[DF_AA['cat'] == 'Fibre'].assign(angle_h=lambda d: 90 - d['phi'])

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

VOL_TOTAL    = 122.96
VOL_NOL_MM3  = 4.00
VOL_RATIO_PC = round(VOL_NOL_MM3 / VOL_TOTAL * 100, 1)
POROSITY     = 94.5

ACOUS_GEN = DF_ACOUS[DF_ACOUS['nom'].str.contains('genere')]
ACOUS_REF = DF_ACOUS[DF_ACOUS['nom'] == 'F1_originel']

# ── Tests de Kolmogorov-Smirnov ───────────────────────────────────────────────
KS_ORIENT = stats.ks_2samp(FIB['angle_h'].dropna().values,
                            DF_NOL['angle_h'].dropna().values)
KS_DIAM   = stats.ks_2samp(aa_eq.dropna().values,
                            nol_eq.dropna().values)

# ── Fits log-normaux sur le diamètre équivalent ────────────────────────────────
try:
    _eq_aa_clean  = aa_eq[aa_eq > 0].values
    _eq_nol_clean = nol_eq[nol_eq > 0].values
    LN_AA  = sp_lognorm.fit(_eq_aa_clean,  floc=0)
    LN_NOL = sp_lognorm.fit(_eq_nol_clean, floc=0)
    LN_OK  = True
except Exception:
    LN_OK  = False

print(f"OK · {len(FIB)} fibres Dragonfly · {len(DF_NOL)} composantes MATLAB · "
      f"{len(ACOUS_GEN)} échantillons générés")
print(f"   KS orient p={KS_ORIENT.pvalue:.4f}  ·  KS diam p={KS_DIAM.pvalue:.4f}")


# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def lay(h=300, lg=False, **kw):
    d = dict(
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=dict(family=FONT, size=11, color=ZN500),
        height=h, showlegend=lg,
        margin=dict(l=54, r=18, t=20, b=48),
        xaxis=dict(showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500, family=FONT)),
        yaxis=dict(gridcolor='#F4F4F5', linecolor='transparent', zeroline=False,
                   tickfont=dict(size=10, color=ZN500, family=FONT)),
        legend=dict(orientation='h', yanchor='bottom', y=1.04, xanchor='left', x=0,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=10, color=ZN700, family=FONT)),
        hoverlabel=dict(bgcolor=ZN900, bordercolor=ZN900,
                        font=dict(color='white', size=11, family=FONT), namelength=-1),
    )
    d.update(kw)
    return d


def card(*children, p='20px 24px', mb='14px', hover=True):
    base = {
        'background': CARD, 'borderRadius': '10px',
        'border': f'1px solid {ZN200}',
        'padding': p, 'marginBottom': mb,
    }
    return html.Div(list(children), style=base, className='hover-card' if hover else '')


def grid(*children, cols=2, gap='14px', mb='14px'):
    return html.Div(list(children), style={
        'display': 'grid',
        'gridTemplateColumns': ' '.join(['1fr'] * cols),
        'gap': gap, 'marginBottom': mb,
    })


def G(fig):
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def chart_head(title, subtitle=None, question=None):
    els = [html.Div(title, style={
        'fontSize': '0.84rem', 'fontWeight': '700', 'color': ZN800, 'marginBottom': '3px',
    })]
    if subtitle:
        els.append(html.Div(subtitle, style={
            'fontSize': '0.73rem', 'color': ZN400, 'marginBottom': '4px',
        }))
    if question:
        els.append(html.Div(question, style={
            'fontStyle': 'italic', 'fontSize': '0.75rem', 'color': INDIGO,
            'borderLeft': f'2px solid {INDIGO}', 'paddingLeft': '9px',
            'marginTop': '6px', 'marginBottom': '14px',
            'background': 'rgba(99,102,241,0.04)', 'borderRadius': '0 6px 6px 0',
            'padding': '5px 9px',
        }))
    else:
        els.append(html.Div(style={'marginBottom': '14px'}))
    return html.Div(els)


def insight(text, color=GREEN, bg='#F0FDF4', border='#D1FAE5'):
    return html.Div(text, style={
        'borderLeft': f'3px solid {border}',
        'borderRadius': '0 6px 6px 0',
        'padding': '10px 14px', 'marginBottom': '16px',
        'fontSize': '0.82rem', 'fontWeight': '500', 'color': color, 'lineHeight': '1.6',
    })


def item(text, warn=False):
    return html.Div([
        html.Span('›', style={'color': ZN300, 'marginRight': '8px', 'fontWeight': '700'}),
        html.Span(text, style={
            'fontSize': '0.81rem',
            'color': AMBER if warn else ZN700,
            'fontWeight': '500' if warn else '400',
        }),
    ], style={'marginBottom': '7px', 'display': 'flex', 'alignItems': 'baseline'})


# ── Nouvelles fonctions helpers ────────────────────────────────────────────────

def delta_chip(pct, label=''):
    if pct < 15:
        bg, fg = '#DCFCE7', '#166534'
        sym = '✓'
    elif pct < 40:
        bg, fg = '#FEF3C7', '#92400E'
        sym = '⚠'
    else:
        bg, fg = '#FEE2E2', '#991B1B'
        sym = '!'
    txt = f'{sym} Δ {pct:.0f}%' + (f' {label}' if label else '')
    return html.Span(txt, style={
        'display': 'inline-block', 'padding': '3px 10px', 'borderRadius': '20px',
        'fontSize': '0.71rem', 'fontWeight': '700', 'background': bg, 'color': fg,
        'letterSpacing': '0.01em',
    })


def ks_banner(ks_result, label=''):
    pval = ks_result.pvalue
    similar = pval > 0.05
    icon  = '✓' if similar else '⚠'
    verdict = 'distributions statistiquement similaires' if similar else 'distributions significativement différentes'
    bg, fg, bd = ('#F0FDF4', '#166534', '#86EFAC') if similar else ('#FFFBEB', '#92400E', '#FCD34D')
    return html.Div([
        html.Span('Test de Kolmogorov-Smirnov', style={
            'fontSize': '0.68rem', 'fontWeight': '700', 'textTransform': 'uppercase',
            'letterSpacing': '0.08em', 'color': ZN400, 'marginRight': '10px',
        }),
        html.Span(f'{icon}  {verdict}', style={
            'fontSize': '0.75rem', 'fontWeight': '600', 'color': fg,
            'background': bg, 'border': f'1px solid {bd}', 'borderRadius': '20px',
            'padding': '3px 10px',
        }),
        html.Span(f'  D = {ks_result.statistic:.3f}  ·  p = {pval:.4f}', style={
            'fontSize': '0.73rem', 'color': ZN400, 'marginLeft': '10px',
        }),
    ], style={'display': 'flex', 'alignItems': 'center', 'marginTop': '10px',
              'paddingTop': '10px', 'borderTop': f'1px solid {ZN200}'})


def moments_table_cmp(arr_aa, arr_nol, unit='', fmt='.1f'):
    def r(arr):
        a = arr[~np.isnan(arr)]
        return {
            'n': len(a), 'mean': float(np.mean(a)),
            'median': float(np.median(a)), 'std': float(np.std(a, ddof=1)),
            'p25': float(np.percentile(a, 25)), 'p75': float(np.percentile(a, 75)),
            'skew': float(sp_skew(a, bias=False)),
        }

    s_aa  = r(arr_aa)
    s_nol = r(arr_nol)

    th_s = {
        'fontSize': '0.65rem', 'fontWeight': '600', 'textTransform': 'uppercase',
        'letterSpacing': '0.07em', 'color': ZN500, 'padding': '8px 12px',
        'background': ZN100, 'textAlign': 'left', 'whiteSpace': 'nowrap',
        'borderBottom': f'2px solid {ZN200}',
    }
    td_s  = {'padding': '7px 12px', 'fontSize': '0.79rem', 'borderBottom': f'1px solid {ZN200}',
             'fontVariantNumeric': 'tabular-nums', 'color': ZN700}
    td_aa = {**td_s, 'background': '#EEF2FF', 'fontWeight': '600', 'color': INDIGO}
    td_nol= {**td_s, 'background': '#ECFDF5', 'fontWeight': '600', 'color': EMERALD}

    def td(val, style, d=1):
        return html.Td(f'{val:{fmt}}{unit}', style=style)

    rows_data = [
        ('Nb mesures',  s_aa['n'],      s_nol['n'],      True),
        ('Moyenne',     s_aa['mean'],   s_nol['mean'],   False),
        ('Médiane',     s_aa['median'], s_nol['median'], False),
        ('Écart-type',  s_aa['std'],    s_nol['std'],    False),
        ('P25',         s_aa['p25'],    s_nol['p25'],    False),
        ('P75',         s_aa['p75'],    s_nol['p75'],    False),
        ('Asymétrie',   s_aa['skew'],   s_nol['skew'],   False),
    ]

    body_rows = []
    for label, v_aa, v_nol, is_int in rows_data:
        fmt_val = 'd' if is_int else fmt.lstrip('.')
        fmt_str = f'{{:.0f}}' if is_int else f'{{:{fmt}}}'
        body_rows.append(html.Tr([
            html.Td(label, style={**td_s, 'background': ZN100, 'fontWeight': '500', 'color': ZN700}),
            html.Td(fmt_str.format(v_aa) + ('' if is_int else unit), style=td_aa),
            html.Td(fmt_str.format(v_nol) + ('' if is_int else unit), style=td_nol),
        ]))

    return html.Table([
        html.Thead(html.Tr([
            html.Th('Statistique', style=th_s),
            html.Th([html.Span('● ', style={'color': INDIGO}), 'Dragonfly'], style=th_s),
            html.Th([html.Span('● ', style={'color': EMERALD}), 'MATLAB'], style=th_s),
        ])),
        html.Tbody(body_rows),
    ], style={'width': '100%', 'borderCollapse': 'collapse', 'borderRadius': '10px',
              'overflow': 'hidden'})


def verdict_card(icon, title, detail, status='ok'):
    colors = {
        'ok':   {'bg': '#F0FDF4', 'border': '#10B981', 'title': '#065F46'},
        'warn': {'bg': '#FFFBEB', 'border': '#F59E0B', 'title': '#92400E'},
        'diff': {'bg': '#FFF1F2', 'border': '#E11D48', 'title': '#9F1239'},
    }
    c = colors.get(status, colors['ok'])
    return html.Div([
        html.Div([
            html.Span(icon, style={'marginRight': '7px', 'fontSize': '0.9rem'}),
            html.Span(title, style={'fontSize': '0.81rem', 'fontWeight': '700', 'color': c['title']}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '7px'}),
        html.Div(detail, style={'fontSize': '0.74rem', 'color': ZN500, 'lineHeight': '1.55'}),
    ], style={
        'background': c['bg'], 'borderRadius': '8px', 'padding': '14px 16px',
        'borderTop': f'1px solid {ZN200}',
        'borderRight': f'1px solid {ZN200}',
        'borderBottom': f'1px solid {ZN200}',
        'borderLeft': f'3px solid {c["border"]}',
    }, className='hover-card')


def kpi_dual(label, v_aa, v_nol, badge_text, badge_cls='badge-info', delta_pct=None):
    return html.Div([
        html.Div(label.upper(), style={
            'fontSize': '0.66rem', 'fontWeight': '600',
            'color': ZN400, 'letterSpacing': '0.08em', 'marginBottom': '12px',
        }),
        html.Div([
            html.Div([
                html.Div(str(v_aa), className='tabnum', style={
                    'fontSize': '1.8rem', 'fontWeight': '700',
                    'color': INDIGO, 'lineHeight': '1', 'letterSpacing': '-0.025em',
                }),
                html.Div([
                    html.Span('●', style={'color': INDIGO, 'fontSize': '0.5rem', 'marginRight': '5px'}),
                    html.Span('Dragonfly', style={'color': ZN400, 'fontSize': '0.72rem'}),
                ], style={'marginTop': '6px', 'display': 'flex', 'alignItems': 'center'}),
            ]),
            html.Div(style={'width': '1px', 'background': ZN200, 'margin': '0 14px', 'alignSelf': 'stretch'}),
            html.Div([
                html.Div(str(v_nol), className='tabnum', style={
                    'fontSize': '1.8rem', 'fontWeight': '700',
                    'color': EMERALD, 'lineHeight': '1', 'letterSpacing': '-0.025em',
                }),
                html.Div([
                    html.Span('●', style={'color': EMERALD, 'fontSize': '0.5rem', 'marginRight': '5px'}),
                    html.Span('MATLAB', style={'color': ZN400, 'fontSize': '0.72rem'}),
                ], style={'marginTop': '6px', 'display': 'flex', 'alignItems': 'center'}),
            ]),
        ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '12px'}),
        html.Div([
            html.Span(badge_text, className=f'badge {badge_cls}'),
            *([html.Span(style={'marginLeft': '8px'}), delta_chip(delta_pct)] if delta_pct is not None else []),
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '6px'}),
    ], style={
        'background': CARD, 'borderRadius': '10px',
        'border': f'1px solid {ZN200}',
        'padding': '18px 20px',
    }, className='hover-card')


def kpi_single(label, value, sub=None, color=ZN900):
    return html.Div([
        html.Div(label.upper(), style={
            'fontSize': '0.66rem', 'fontWeight': '600',
            'color': ZN400, 'letterSpacing': '0.08em', 'marginBottom': '12px',
        }),
        html.Div(value, className='tabnum', style={
            'fontSize': '1.8rem', 'fontWeight': '700',
            'color': color, 'lineHeight': '1', 'letterSpacing': '-0.025em', 'marginBottom': '8px',
        }),
        *([html.Div(sub, style={'fontSize': '0.75rem', 'color': ZN400})] if sub else []),
    ], style={
        'background': CARD, 'borderRadius': '10px',
        'border': f'1px solid {ZN200}',
        'padding': '18px 20px',
    }, className='hover-card')


def lognorm_trace(params, arr, color, name, bw=8):
    """Overlay de fit log-normal sur un histogram histnorm='percent'."""
    if not LN_OK or params is None:
        return None
    try:
        shape, loc, scale = params
        x_fit = np.linspace(max(arr.min() * 0.5, 1), arr.max() * 1.15, 300)
        pdf   = sp_lognorm.pdf(x_fit, shape, loc, scale)
        y_pct = pdf * bw * 100
        return go.Scatter(
            x=x_fit, y=y_pct, mode='lines',
            name=f'Fit log-normale — {name}',
            line=dict(color=color, width=2.5, dash='dot'),
            hovertemplate=f'%{{x:.0f}} µm → %{{y:.2f}}%<extra>Fit {name}</extra>',
        )
    except Exception:
        return None


def method_pills():
    return html.Div([
        html.Span([html.Span('●', style={'color': INDIGO, 'marginRight': '5px'}), 'Dragonfly ORS'], style={
            'display': 'inline-flex', 'alignItems': 'center',
            'background': '#EEF2FF', 'color': '#4338CA', 'border': '1px solid #C7D2FE',
            'borderRadius': '20px', 'padding': '3px 10px',
            'fontSize': '0.72rem', 'fontWeight': '600', 'marginRight': '8px',
        }),
        html.Span([html.Span('●', style={'color': EMERALD, 'marginRight': '5px'}), 'MATLAB regionprops3'], style={
            'display': 'inline-flex', 'alignItems': 'center',
            'background': '#ECFDF5', 'color': '#065F46', 'border': '1px solid #6EE7B7',
            'borderRadius': '20px', 'padding': '3px 10px',
            'fontSize': '0.72rem', 'fontWeight': '600',
        }),
    ], style={'marginBottom': '16px'})


# ══════════════════════════════════════════════════════════════════════════════
#  ONGLET 1 — CONTEXTE & DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

def build_overview():
    cats   = ['Bruit', 'Fragment', 'Fibre', 'Gros objet', 'Matrice']
    colors = [ZN300, '#FCD34D', INDIGO, '#A78BFA', ZN400]
    counts = DF_AA['cat'].value_counts().reindex(cats, fill_value=0)

    fig_seg = go.Figure(go.Bar(
        x=cats, y=counts.values, marker_color=colors,
        text=counts.values, textposition='outside', cliponaxis=False,
        textfont=dict(size=11, color=ZN700, family=FONT),
        hovertemplate='<b>%{x}</b> — %{y} objets<extra></extra>',
    ))
    fig_seg.update_layout(**lay(h=210,
        margin=dict(l=10, r=10, t=28, b=36),
        yaxis=dict(visible=False),
        xaxis=dict(showgrid=False, linecolor='transparent', zeroline=False,
                   tickfont=dict(size=11, color=ZN700)),
    ))

    return html.Div([

        insight(
            '📊  Ce dashboard post-traite et compare les résultats de deux méthodes d\'analyse '
            'de microstructure fibreuse par microtomographie X : Dragonfly ORS (scan complet, '
            '122.96 mm³) et MATLAB regionprops3 (sous-volume, 4.00 mm³). Naviguez dans les '
            'onglets pour explorer l\'orientation, la morphologie et les propriétés acoustiques.',
            color=ZN800, bg=ZN100, border=ZN200,
        ),

        html.Div([
            kpi_single('Porosité mesurée', f'{POROSITY} %',
                       sub='Dragonfly · plage 88–95 % · fibres ≈ 4.3 % du volume',
                       color=ZN800),
            kpi_dual('Inclinaison médiane', f'{AA_ANG_MED}°', f'{NOL_ANG_MED}°',
                     '✓ Convergence des deux méthodes', 'badge-ok',
                     delta_pct=abs(AA_ANG_MED - NOL_ANG_MED) / max(AA_ANG_MED, NOL_ANG_MED) * 100),
            kpi_dual('Diamètre équivalent', f'{AA_EQ_MED} µm', f'{NOL_EQ_MED} µm',
                     '∛(6V/π) — même formule', 'badge-warn',
                     delta_pct=ECART_PCT),
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr',
                  'gap': '14px', 'marginBottom': '14px'}),

        grid(
            card(
                html.Div('Volumes analysés', style={
                    'fontSize': '0.66rem', 'fontWeight': '700',
                    'color': ZN400, 'letterSpacing': '0.09em', 'textTransform': 'uppercase',
                    'marginBottom': '18px',
                }),
                html.Div([
                    html.Div('Dragonfly ORS — Scan complet F1', style={
                        'fontSize': '0.75rem', 'fontWeight': '600', 'color': ZN700, 'marginBottom': '6px',
                    }),
                    html.Div(style={'height': '8px', 'background': INDIGO, 'borderRadius': '4px',
                                    'width': '100%', 'marginBottom': '5px'}),
                    html.Span('122.96 mm³ — 100 %', className='tabnum',
                              style={'fontWeight': '800', 'color': INDIGO, 'fontSize': '0.9rem'}),
                ], style={'marginBottom': '16px'}),
                html.Div([
                    html.Div('MATLAB regionprops3 — Sous-volume Nolhan', style={
                        'fontSize': '0.75rem', 'fontWeight': '600', 'color': ZN700, 'marginBottom': '6px',
                    }),
                    html.Div([html.Div(style={
                        'height': '8px', 'background': EMERALD, 'borderRadius': '4px',
                        'width': f'{VOL_RATIO_PC}%',
                    })], style={'background': ZN100, 'borderRadius': '4px', 'marginBottom': '5px'}),
                    html.Span(f'4.00 mm³ — {VOL_RATIO_PC} % du scan', className='tabnum',
                              style={'fontWeight': '800', 'color': EMERALD, 'fontSize': '0.9rem'}),
                ]),
                html.Div(
                    '⚠  Hypothèse d\'homogénéité : les distributions du sous-volume MATLAB '
                    'sont supposées représentatives du volume total.',
                    style={'fontSize': '0.73rem', 'color': AMBER, 'marginTop': '14px',
                           'paddingTop': '12px', 'borderTop': f'1px solid {ZN200}'},
                ),
                p='20px 22px',
            ),
            card(
                html.Div('Objets détectés', style={
                    'fontSize': '0.66rem', 'fontWeight': '700',
                    'color': ZN400, 'letterSpacing': '0.09em', 'textTransform': 'uppercase',
                    'marginBottom': '18px',
                }),
                html.Div([
                    html.Div([
                        html.Div(str(len(FIB)), className='tabnum', style={
                            'fontSize': '2.4rem', 'fontWeight': '800', 'color': INDIGO,
                            'letterSpacing': '-0.04em',
                        }),
                        html.Div('fibres Dragonfly', style={'fontSize': '0.75rem', 'color': ZN500}),
                        html.Div('Filtre · 101–100 000 voxels · 5.5 µm/vox',
                                 style={'fontSize': '0.7rem', 'color': ZN400, 'marginTop': '3px'}),
                    ]),
                    html.Div(style={'width': '1px', 'background': ZN200, 'margin': '0 22px', 'alignSelf': 'stretch'}),
                    html.Div([
                        html.Div(str(len(DF_NOL)), className='tabnum', style={
                            'fontSize': '2.4rem', 'fontWeight': '800', 'color': EMERALD,
                            'letterSpacing': '-0.04em',
                        }),
                        html.Div('composantes MATLAB', style={'fontSize': '0.75rem', 'color': ZN500}),
                        html.Div('Aucun filtre · fragments inclus · ~10 µm/vox',
                                 style={'fontSize': '0.7rem', 'color': ZN400, 'marginTop': '3px'}),
                    ]),
                ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '14px'}),
                html.Div(
                    '⚠  Comptages absolus non comparables — volumes et filtres très différents. '
                    'Seules les distributions normalisées (%) ont valeur comparative.',
                    style={'fontSize': '0.73rem', 'color': AMBER,
                           'paddingTop': '12px', 'borderTop': f'1px solid {ZN200}'},
                ),
                p='20px 22px',
            ),
        ),

        grid(
            html.Div([
                html.Div([
                    html.Span('●', style={'color': INDIGO, 'fontSize': '0.65rem', 'marginRight': '8px'}),
                    html.Span('Dragonfly ORS', style={'fontWeight': '700', 'fontSize': '0.86rem', 'color': ZN900}),
                    html.Span(' · 5.5 µm/vox', style={'fontSize': '0.7rem', 'color': ZN400, 'marginLeft': '6px'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                item('Segmentation volumique → squelettisation'),
                item('Épaisseur locale par ray-tracing (16.5 M mesures)'),
                item(f'Filtre taille → {len(FIB)} fibres retenues'),
                item('Volume analysé : scan complet 122.96 mm³', warn=False),
            ], style={'background': '#EEF2FF', 'borderRadius': '12px', 'padding': '18px 20px',
                      'border': f'1px solid #C7D2FE'}),
            html.Div([
                html.Div([
                    html.Span('●', style={'color': EMERALD, 'fontSize': '0.65rem', 'marginRight': '8px'}),
                    html.Span('MATLAB regionprops3', style={'fontWeight': '700', 'fontSize': '0.86rem', 'color': ZN900}),
                    html.Span(' · ~10 µm/vox', style={'fontSize': '0.7rem', 'color': ZN400, 'marginLeft': '6px'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                item('Composantes connexes → ellipsoïde équivalent'),
                item('Axes principaux PAL1/2/3, angles d\'Euler'),
                item(f'Aucun filtre → {len(DF_NOL)} composantes'),
                item('Sous-volume : 200×200×100 vox = 4.00 mm³', warn=False),
            ], style={'background': '#ECFDF5', 'borderRadius': '12px', 'padding': '18px 20px',
                      'border': f'1px solid #6EE7B7'}),
        ),

        card(
            chart_head(
                'Classification des objets détectés — Dragonfly',
                f'{len(DF_AA)} objets analysés · seules les fibres (indigo) entrent dans la comparaison',
                question='Comment Dragonfly distingue-t-il fibres, bruit, et matrice dans le scan ?',
            ),
            G(fig_seg),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  ONGLET 2 — ORIENTATION
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
                    marker=dict(color=INDIGO,  opacity=0.78, line=dict(color='white', width=0.8)),
                    hovertemplate='%{theta:.0f}° : %{r:.1f}%<extra>Dragonfly</extra>'),
        go.Barpolar(r=h_nol, theta=centers, name='MATLAB',    width=20,
                    marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.8)),
                    hovertemplate='%{theta:.0f}° : %{r:.1f}%<extra>MATLAB</extra>'),
    ])
    fig.update_layout(
        paper_bgcolor=CARD, height=360, showlegend=True,
        margin=dict(l=20, r=20, t=30, b=10),
        legend=dict(orientation='h', y=-0.04, x=0.5, xanchor='center',
                    bgcolor='rgba(0,0,0,0)', font=dict(size=11, color=ZN700, family=FONT)),
        hoverlabel=dict(bgcolor=ZN900, bordercolor=ZN900,
                        font=dict(color='white', size=11, family=FONT)),
        polar=dict(bgcolor='#FAFBFC',
                   radialaxis=dict(visible=True, showticklabels=True, ticksuffix='%',
                                   tickfont=dict(size=9, color=ZN400),
                                   gridcolor=ZN200, linecolor=ZN200),
                   angularaxis=dict(direction='clockwise', rotation=90,
                                    tickfont=dict(size=10, color=ZN500, family=FONT),
                                    linecolor=ZN200, gridcolor=ZN200)),
    )
    return fig


def _fig_azimut():
    fig = go.Figure([
        go.Histogram(x=FIB['theta'], name='Dragonfly — Theta',
                     histnorm='percent', xbins=dict(size=10),
                     marker=dict(color=INDIGO, opacity=0.75, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f}° : %{y:.1f}%<extra>Dragonfly</extra>'),
        go.Histogram(x=DF_NOL['Orientation_1'] * 2, name='MATLAB — Orient₁×2',
                     histnorm='percent', xbins=dict(size=10),
                     marker=dict(color=EMERALD, opacity=0.65, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f}° : %{y:.1f}%<extra>MATLAB</extra>'),
    ])
    fig.update_layout(**lay(h=240, lg=True, barmode='overlay',
        xaxis=dict(title='Azimut (°)', range=[-185, 185], showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))
    return fig


def build_orientation():
    ecart = abs(AA_ANG_MED - NOL_ANG_MED)
    return html.Div([

        insight(
            f'✓  Les deux méthodes convergent : fibres quasi-horizontales '
            f'(Dragonfly {AA_ANG_MED}°, MATLAB {NOL_ANG_MED}°, écart {ecart:.1f}°). '
            f'La distribution azimutale est uniforme dans les deux cas → pas de direction préférentielle dans le plan horizontal.',
        ),

        grid(
            card(
                chart_head('Diagramme de rose — Distribution azimutale',
                           '18 secteurs de 20° · normalisé en % · sens horaire depuis le Nord',
                           question='Les fibres ont-elles une direction préférentielle dans le plan horizontal ?'),
                G(_polar_rose()),
                mb='0',
            ),
            card(
                html.Div([
                    chart_head('Inclinaison depuis l\'horizontale',
                               '0° = fibre à plat · 90° = fibre verticale',
                               question='Les fibres sont-elles proches de l\'horizontale ?'),
                    dcc.RadioItems(id='method-toggle',
                        options=[{'label': 'Les deux', 'value': 'both'},
                                 {'label': 'Dragonfly', 'value': 'aa'},
                                 {'label': 'MATLAB', 'value': 'nolhan'}],
                        value='both', className='method-toggle',
                        inputStyle={'display': 'none'}, labelStyle={'cursor': 'pointer'},
                        style={'marginBottom': '10px', 'marginTop': '-8px'}),
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start'}),
                dcc.Graph(id='fig-elevation', config={'displayModeBar': False}),
                html.Div([
                    html.Div([
                        html.Span(f'{AA_ANG_MED}°', className='tabnum', style={
                            'color': INDIGO, 'fontWeight': '800', 'fontSize': '1.1rem', 'marginRight': '6px',
                        }),
                        html.Span('Dragonfly · médiane', style={'color': ZN500, 'fontSize': '0.77rem'}),
                    ], style={'display': 'flex', 'alignItems': 'baseline', 'marginBottom': '4px'}),
                    html.Div([
                        html.Span(f'{NOL_ANG_MED}°', className='tabnum', style={
                            'color': EMERALD, 'fontWeight': '800', 'fontSize': '1.1rem', 'marginRight': '6px',
                        }),
                        html.Span('MATLAB · médiane', style={'color': ZN500, 'fontSize': '0.77rem'}),
                    ], style={'display': 'flex', 'alignItems': 'baseline'}),
                ], style={'display': 'flex', 'gap': '24px', 'marginTop': '8px',
                          'paddingTop': '10px', 'borderTop': f'1px solid {ZN200}'}),
                mb='0',
            ),
        ),

        card(
            chart_head('Statistiques descriptives — Inclinaison (°)'),
            moments_table_cmp(FIB['angle_h'].dropna().values,
                              DF_NOL['angle_h'].dropna().values, unit='°'),
            ks_banner(KS_ORIENT, 'inclinaison'),
        ),

        card(
            chart_head('Distribution azimutale — Histogramme de confirmation',
                       'Une distribution plate confirme l\'isotropie dans le plan horizontal',
                       question='La répartition des fibres est-elle uniforme selon toutes les directions ?'),
            G(_fig_azimut()),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  ONGLET 3 — MORPHOLOGIE
# ══════════════════════════════════════════════════════════════════════════════

def build_morphologie():
    vol_aa_um3  = FIB['vol'] * 1e9
    vol_nol_um3 = DF_NOL['Volume'] * 1000

    # 1. Diamètre direct
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
    fig_d_direct.update_layout(**lay(h=260, lg=True, barmode='overlay',
        xaxis=dict(title='µm', range=[0, 280], showgrid=False, linecolor=ZN200,
                   zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 2. Diamètre équivalent + fit log-normal
    fig_d_eq = go.Figure([
        go.Histogram(x=aa_eq, name=f'Dragonfly (méd. {AA_EQ_MED} µm)',
                     histnorm='percent', xbins=dict(size=8),
                     marker=dict(color=INDIGO, opacity=0.70, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>Dragonfly</extra>'),
        go.Histogram(x=nol_eq, name=f'MATLAB (méd. {NOL_EQ_MED} µm)',
                     histnorm='percent', xbins=dict(size=8),
                     marker=dict(color=EMERALD, opacity=0.60, line=dict(color='white', width=0.5)),
                     hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra>MATLAB</extra>'),
    ])
    t_aa  = lognorm_trace(LN_AA,  aa_eq.values,  INDIGO,   'Dragonfly', bw=8)
    t_nol = lognorm_trace(LN_NOL, nol_eq.values, EMERALD,  'MATLAB',    bw=8)
    if t_aa:  fig_d_eq.add_trace(t_aa)
    if t_nol: fig_d_eq.add_trace(t_nol)
    fig_d_eq.update_layout(**lay(h=260, lg=True, barmode='overlay',
        xaxis=dict(title='Diamètre équivalent (µm)', showgrid=False, linecolor=ZN200,
                   zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 3. CDF
    x_aa_s  = np.sort(aa_eq.values)
    y_aa_s  = np.arange(1, len(x_aa_s)  + 1) / len(x_aa_s)  * 100
    x_nol_s = np.sort(nol_eq.values)
    y_nol_s = np.arange(1, len(x_nol_s) + 1) / len(x_nol_s) * 100
    fig_cdf = go.Figure([
        go.Scatter(x=x_aa_s,  y=y_aa_s,  name=f'Dragonfly (méd. {AA_EQ_MED} µm)',
                   line=dict(color=INDIGO, width=2.5), mode='lines',
                   hovertemplate='%{x:.0f} µm → %{y:.1f}%<extra>Dragonfly</extra>'),
        go.Scatter(x=x_nol_s, y=y_nol_s, name=f'MATLAB (méd. {NOL_EQ_MED} µm)',
                   line=dict(color=EMERALD, width=2.5), mode='lines',
                   hovertemplate='%{x:.0f} µm → %{y:.1f}%<extra>MATLAB</extra>'),
        go.Scatter(x=[AA_EQ_MED,  AA_EQ_MED],  y=[0, 50],
                   line=dict(color=INDIGO,  width=1.5, dash='dot'), mode='lines', showlegend=False),
        go.Scatter(x=[NOL_EQ_MED, NOL_EQ_MED], y=[0, 50],
                   line=dict(color=EMERALD, width=1.5, dash='dot'), mode='lines', showlegend=False),
        go.Scatter(x=[0, max(AA_EQ_MED, NOL_EQ_MED)], y=[50, 50],
                   line=dict(color=ZN300, width=1, dash='dot'), mode='lines', showlegend=False),
    ])
    fig_cdf.update_layout(**lay(h=260, lg=True,
        xaxis=dict(title='Diamètre équivalent (µm)', showgrid=False, linecolor=ZN200,
                   zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='Fibres ≤ x (%)', range=[0, 100], gridcolor=ZN100, linecolor=ZN200,
                   zeroline=False, tickfont=dict(size=10, color=ZN500)),
    ))

    # 4. Volumes log
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
    fig_vol.update_layout(**lay(h=260, lg=True, barmode='overlay',
        xaxis=dict(title='Volume (µm³)', tickvals=[3, 4, 5, 6, 7],
                   ticktext=['10³', '10⁴', '10⁵', '10⁶', '10⁷'],
                   showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 5 & 6. Box plots
    fig_box_ang = go.Figure([
        go.Box(y=FIB['angle_h'], name='Dragonfly', marker_color=INDIGO,
               line=dict(color=INDIGO), fillcolor='rgba(99,102,241,0.10)',
               hovertemplate='%{y:.1f}°<extra>Dragonfly</extra>'),
        go.Box(y=DF_NOL['angle_h'], name='MATLAB', marker_color=EMERALD,
               line=dict(color=EMERALD), fillcolor='rgba(16,185,129,0.10)',
               hovertemplate='%{y:.1f}°<extra>MATLAB</extra>'),
    ])
    fig_box_ang.update_layout(**lay(h=260,
        yaxis=dict(title='Inclinaison (°)', gridcolor=ZN100, linecolor=ZN200,
                   zeroline=False, tickfont=dict(size=10, color=ZN500)),
        xaxis=dict(showgrid=False, linecolor='transparent', tickfont=dict(size=11, color=ZN700)),
    ))

    fig_box_diam = go.Figure([
        go.Box(y=aa_eq,  name='Dragonfly', marker_color=INDIGO,
               line=dict(color=INDIGO),  fillcolor='rgba(99,102,241,0.10)',
               hovertemplate='%{y:.0f} µm<extra>Dragonfly</extra>'),
        go.Box(y=nol_eq, name='MATLAB',   marker_color=EMERALD,
               line=dict(color=EMERALD), fillcolor='rgba(16,185,129,0.10)',
               hovertemplate='%{y:.0f} µm<extra>MATLAB</extra>'),
    ])
    fig_box_diam.update_layout(**lay(h=260,
        yaxis=dict(title='Diamètre équivalent (µm)', gridcolor=ZN100, linecolor=ZN200,
                   zeroline=False, tickfont=dict(size=10, color=ZN500)),
        xaxis=dict(showgrid=False, linecolor='transparent', tickfont=dict(size=11, color=ZN700)),
    ))

    # 7. Scatter volume vs inclinaison
    fig_scatter = go.Figure([
        go.Scatter(x=vol_aa_um3, y=FIB['angle_h'], mode='markers', name='Dragonfly',
                   marker=dict(color=INDIGO, size=7, opacity=0.65,
                               line=dict(color='white', width=0.5)),
                   hovertemplate='Vol. %{x:,.0f} µm³ · %{y:.1f}°<extra>Dragonfly</extra>'),
        go.Scatter(x=vol_nol_um3, y=DF_NOL['angle_h'], mode='markers', name='MATLAB',
                   marker=dict(color=EMERALD, size=7, opacity=0.65,
                               line=dict(color='white', width=0.5)),
                   hovertemplate='Vol. %{x:,.0f} µm³ · %{y:.1f}°<extra>MATLAB</extra>'),
    ])
    fig_scatter.update_layout(**lay(h=260, lg=True,
        xaxis=dict(title='Volume (µm³)', type='log', showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='Inclinaison (°)', gridcolor=ZN100, linecolor=ZN200,
                   zeroline=False, tickfont=dict(size=10, color=ZN500)),
    ))

    # 8. Longueur MATLAB
    fig_len = go.Figure(go.Histogram(
        x=DF_NOL['Len_um'], histnorm='percent', xbins=dict(size=30),
        marker=dict(color=EMERALD, opacity=0.85, line=dict(color='white', width=0.5)),
        hovertemplate='%{x:.0f} µm : %{y:.1f}%<extra></extra>',
    ))
    fig_len.update_layout(**lay(h=240,
        xaxis=dict(title=f'Longueur PAL₁ (µm) · méd. {NOL_LEN_MED} µm',
                   showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 9. Rapport d'aspect MATLAB
    fig_ar = go.Figure(go.Histogram(
        x=DF_NOL['AspectRatio'].clip(upper=12), histnorm='percent', xbins=dict(size=0.5),
        marker=dict(color=EMERALD, opacity=0.85, line=dict(color='white', width=0.5)),
        hovertemplate='L/D = %{x:.1f} : %{y:.1f}%<extra></extra>',
    ))
    fig_ar.update_layout(**lay(h=240,
        xaxis=dict(title=f'Rapport d\'aspect L/D · méd. {NOL_AR_MED}',
                   showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='% fibres', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
    ))

    # 10. Carte spatiale MATLAB
    len_norm = DF_NOL['Len_um'] / DF_NOL['Len_um'].max()
    fig_map = go.Figure(go.Scatter(
        x=DF_NOL['Centroid_1'] * 10, y=DF_NOL['Centroid_2'] * 10,
        mode='markers',
        marker=dict(
            color=DF_NOL['angle_h'],
            colorscale=[[0, EMERALD], [0.4, '#FBBF24'], [1, RED]],
            cmin=0, cmax=45,
            size=(len_norm * 14 + 4).clip(4, 18),
            opacity=0.85,
            colorbar=dict(title=dict(text='Incl.°', side='right'),
                          thickness=10, len=0.75,
                          tickfont=dict(size=9, color=ZN500, family=FONT)),
            line=dict(color='white', width=0.5)),
        hovertemplate='x=%{x:.0f} µm · y=%{y:.0f} µm<extra></extra>',
    ))
    fig_map.update_layout(**lay(h=320,
        xaxis=dict(title='x (µm)', scaleanchor='y', showgrid=False,
                   linecolor=ZN200, zeroline=False, tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title='y (µm)', gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        margin=dict(l=52, r=60, t=18, b=52),
    ))

    return html.Div([

        card(
            chart_head('Statistiques descriptives — Diamètre équivalent ∛(6V/π)',
                       'Même formule appliquée aux deux méthodes pour une comparaison équitable'),
            moments_table_cmp(aa_eq.dropna().values, nol_eq.dropna().values, unit=' µm'),
        ),

        grid(
            card(chart_head('Diamètre — mesure directe',
                            'Ray-tracing local (Dragonfly) vs petit axe PAL₃ (MATLAB)',
                            question='Les deux méthodes mesurent-elles le même diamètre ?'),
                 G(fig_d_direct),
                 html.Div('⚠ Métriques différentes — cet écart est attendu et ne constitue pas un désaccord.',
                          style={'fontSize': '0.73rem', 'color': AMBER, 'marginTop': '8px'}),
                 mb='0'),
            card(chart_head(f'Diamètre équivalent sphérique — d = ∛(6V/π)',
                            f'Même formule pour les deux méthodes · courbes en pointillés = fit log-normal',
                            question='Sous une métrique commune, les fibres ont-elles la même taille ?'),
                 G(fig_d_eq),
                 ks_banner(KS_DIAM, 'diamètre équivalent'),
                 mb='0'),
        ),

        grid(
            card(chart_head('Fonction de répartition cumulée (CDF)',
                            'La courbe la plus à gauche = fibres plus fines · pointillés = médianes',
                            question='Quelle proportion de fibres est inférieure à un diamètre donné ?'),
                 G(fig_cdf), mb='0'),
            card(chart_head('Distribution des volumes — Échelle logarithmique',
                            'Même unité µm³ pour une comparaison directe',
                            question='Les fibres ont-elles des volumes similaires selon les deux méthodes ?'),
                 G(fig_vol), mb='0'),
        ),

        grid(
            card(chart_head('Box plot — Inclinaison depuis l\'horizontale',
                            'Médiane (trait), quartiles (boîte), extrêmes (moustaches)'),
                 G(fig_box_ang), mb='0'),
            card(chart_head('Box plot — Diamètre équivalent',
                            'Dispersion des tailles de fibres par méthode'),
                 G(fig_box_diam), mb='0'),
        ),

        grid(
            card(chart_head('Volume vs Inclinaison',
                            'Chaque point = une fibre · y a-t-il une corrélation taille/orientation ?',
                            question='Les fibres volumineuses sont-elles plus inclinées que les petites ?'),
                 G(fig_scatter), mb='0'),
            card(chart_head(f'Longueur des fibres — MATLAB uniquement',
                            f'PAL₁ × 10 µm · médiane {NOL_LEN_MED} µm'),
                 G(fig_len),
                 html.Div('Dragonfly ne fournit pas de longueur (squelette non exporté dans ce format).',
                          style={'fontSize': '0.73rem', 'color': ZN400, 'marginTop': '8px'}),
                 mb='0'),
        ),

        grid(
            card(chart_head(f'Rapport d\'aspect L/D — MATLAB uniquement',
                            f'PAL₁/PAL₃ · médiane {NOL_AR_MED} · tronqué à 12'),
                 G(fig_ar), mb='0'),
            card(chart_head('Localisation spatiale dans le sous-volume — MATLAB',
                            'Taille ∝ longueur · couleur = inclinaison (vert=horizontal, rouge=incliné)'),
                 G(fig_map), mb='0'),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  ONGLET 4 — BILAN COMPARATIF
# ══════════════════════════════════════════════════════════════════════════════

def build_comparaison():

    def row(metric, v_aa, v_nol, bdg, bdg_cls, note='', d_pct=None, alt=False):
        bg = ZN100 if alt else CARD
        return html.Tr([
            html.Td([
                html.Div(metric, style={'fontWeight': '500', 'color': ZN700, 'fontSize': '0.83rem'}),
                *([html.Div(note, style={'fontSize': '0.71rem', 'color': ZN400, 'marginTop': '2px'})] if note else []),
            ], style={'background': bg, 'padding': '11px 14px', 'verticalAlign': 'middle'}),
            html.Td(html.Span(v_aa, className='tabnum'),
                    style={'background': bg, 'padding': '11px 14px',
                           'color': INDIGO, 'fontWeight': '700', 'fontSize': '0.85rem',
                           'verticalAlign': 'middle'}),
            html.Td(html.Span(v_nol, className='tabnum'),
                    style={'background': bg, 'padding': '11px 14px',
                           'color': EMERALD, 'fontWeight': '700', 'fontSize': '0.85rem',
                           'verticalAlign': 'middle'}),
            html.Td([
                html.Span(bdg, className=f'badge {bdg_cls}'),
                *([html.Span(style={'marginLeft': '6px'}), delta_chip(d_pct)] if d_pct is not None else []),
            ], style={'background': bg, 'padding': '11px 14px', 'verticalAlign': 'middle',
                      'whiteSpace': 'nowrap'}),
        ])

    th_s = {'background': ZN100, 'color': ZN500, 'padding': '10px 14px',
            'fontSize': '0.68rem', 'fontWeight': '600', 'textTransform': 'uppercase',
            'letterSpacing': '0.07em', 'textAlign': 'left',
            'borderBottom': f'2px solid {ZN200}'}

    table = html.Table([
        html.Thead(html.Tr([
            html.Th('Propriété', style=th_s),
            html.Th([html.Span('● ', style={'color': INDIGO}), 'Dragonfly'], style=th_s),
            html.Th([html.Span('● ', style={'color': EMERALD}), 'MATLAB'], style=th_s),
            html.Th('Analyse', style=th_s),
        ])),
        html.Tbody([
            row('Volume analysé',             '122.96 mm³',        '4.00 mm³',
                f'⚠ {VOL_RATIO_PC}% commun',  'badge-warn',
                'Volumes différents — distributions % valides sous hypothèse homogénéité',
                d_pct=None, alt=False),
            row('Résolution voxel',           f'{VOX_UM} µm/vox',  '~10 µm/vox',
                '— Résolutions ≠',             'badge-info', '', alt=True),
            row('Porosité',                   f'~{POROSITY} %',    '— (n/a)',
                '— Dragonfly seulement',       'badge-info',
                'Plage mesurée 88–95 %', alt=False),
            row('Orientation générale',       'Quasi-horizontale', 'Quasi-horizontale',
                '✓ Accord',                    'badge-ok',   '', alt=True),
            row('Inclinaison médiane',         f'{AA_ANG_MED}°',    f'{NOL_ANG_MED}°',
                '✓ Convergence',               'badge-ok',
                'Depuis l\'horizontale · écart ' + f'{abs(AA_ANG_MED-NOL_ANG_MED):.1f}°',
                d_pct=abs(AA_ANG_MED-NOL_ANG_MED)/max(AA_ANG_MED, NOL_ANG_MED)*100, alt=False),
            row('Isotropie azimutale',        'Uniforme',          'Uniforme',
                '✓ Accord',                    'badge-ok',
                'Distribution plate sur 360°', alt=True),
            row('Diamètre mesure directe',    f'{THICK_MED} µm',   f'{NOL_D_MED} µm',
                '≠ Métriques ≠',               'badge-diff',
                'Ray-tracing ≠ PAL₃ — non comparables en valeur absolue', alt=False),
            row('Diamètre équivalent ∛6V/π',  f'{AA_EQ_MED} µm',   f'{NOL_EQ_MED} µm',
                f'⚠ Écart résiduel',           'badge-warn',
                'Même formule · comparaison la plus équitable',
                d_pct=ECART_PCT, alt=True),
            row('Longueur médiane',            '— (n/a)',            f'{NOL_LEN_MED} µm',
                '— MATLAB seulement',          'badge-info',
                'PAL₁ × 10 µm', alt=False),
            row('Rapport d\'aspect médian',    '— (n/a)',            str(NOL_AR_MED),
                '— MATLAB seulement',          'badge-info',
                'Longueur / Diamètre', alt=True),
        ]),
    ], style={'width': '100%', 'borderCollapse': 'collapse'})

    return html.Div([

        html.Div('Verdict rapide', style={
            'fontSize': '0.67rem', 'fontWeight': '700', 'color': ZN400,
            'letterSpacing': '0.09em', 'textTransform': 'uppercase',
            'marginBottom': '12px',
        }),
        html.Div([
            verdict_card('✓', 'Orientation convergente',
                         f'Les deux méthodes situent les fibres quasi-horizontalement '
                         f'(Drag. {AA_ANG_MED}° · MATLAB {NOL_ANG_MED}°).', 'ok'),
            verdict_card('✓', 'Isotropie azimutale confirmée',
                         'Aucune direction préférentielle dans le plan horizontal '
                         'pour les deux méthodes.', 'ok'),
            verdict_card('⚠', f'Écart diamètre {ECART_PCT}%',
                         f'Sous la même formule ∛(6V/π) : {AA_EQ_MED} µm (Drag.) vs '
                         f'{NOL_EQ_MED} µm (MATLAB). Dû aux résolutions et filtres différents.', 'warn'),
            verdict_card('⚠', 'Volumes non comparables',
                         f'Dragonfly = scan complet (122.96 mm³), MATLAB = sous-volume '
                         f'({VOL_RATIO_PC}%). Comparaison via distributions normalisées.', 'warn'),
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)',
                  'gap': '12px', 'marginBottom': '16px'}),

        card(
            chart_head('Tableau comparatif complet', 'Point par point · Δ = écart relatif entre médianes'),
            table,
        ),

        grid(
            card(
                html.Div('✓  Ce que les données confirment', style={
                    'fontSize': '0.67rem', 'fontWeight': '700', 'color': GREEN,
                    'letterSpacing': '0.08em', 'textTransform': 'uppercase', 'marginBottom': '12px',
                }),
                html.Div([
                    item('Fibres quasi-horizontales : médianes < 12° pour les deux méthodes'),
                    item('Isotropie azimutale — pas de direction préférentielle'),
                    item(f'Porosité ~{POROSITY}% cohérente avec un matériau fibreux lâche'),
                    item(f'Diamètre équivalent : convergence partielle ({ECART_PCT}% d\'écart)'),
                    item('Test KS inclinaison : ' + ('similaires ✓' if KS_ORIENT.pvalue > 0.05
                         else f'différentes (p={KS_ORIENT.pvalue:.3f})')),
                ]),
                mb='0',
            ),
            card(
                html.Div('⚠  Limites et précautions d\'interprétation', style={
                    'fontSize': '0.67rem', 'fontWeight': '700', 'color': AMBER,
                    'letterSpacing': '0.08em', 'textTransform': 'uppercase', 'marginBottom': '12px',
                }),
                html.Div([
                    item(f'Volumes très différents ({VOL_RATIO_PC}%) — comptages absolus non comparables', warn=True),
                    item('Résolutions différentes : 5.5 µm (Drag.) vs 10 µm (MATLAB)', warn=True),
                    item('MATLAB sans filtre : fragments et bruit inclus dans les 405', warn=True),
                    item('Hypothèse d\'homogénéité du sous-volume non vérifiée formellement', warn=True),
                    item('Test KS diamètre : ' + ('similaires' if KS_DIAM.pvalue > 0.05
                         else f'différentes (p={KS_DIAM.pvalue:.3f})'), warn=KS_DIAM.pvalue <= 0.05),
                ]),
                mb='0',
            ),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  ONGLET 5 — PROPRIÉTÉS ACOUSTIQUES
# ══════════════════════════════════════════════════════════════════════════════

def _acous_scatter(y_col, y_label, y_log=False, y_unit=''):
    gen = ACOUS_GEN.copy()
    ref = ACOUS_REF.copy()
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
    if len(gen) >= 2:
        xi  = gen['porosite'].values * 100
        yi  = gen[y_col].values
        idx = np.argsort(xi)
        if y_log:
            coeffs = np.polyfit(xi[idx], np.log10(yi[idx]), 1)
            x_fit  = np.linspace(xi.min() - 0.5, xi.max() + 0.5, 100)
            y_fit  = 10 ** np.polyval(coeffs, x_fit)
        else:
            coeffs = np.polyfit(xi[idx], yi[idx], 1)
            x_fit  = np.linspace(xi.min() - 0.5, xi.max() + 0.5, 100)
            y_fit  = np.polyval(coeffs, x_fit)
        traces.append(go.Scatter(
            x=x_fit, y=y_fit, mode='lines', name='Tendance',
            line=dict(color=ZN400, width=1.5, dash='dot'),
            showlegend=False, hoverinfo='skip',
        ))
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
    fig.update_layout(**lay(h=268, lg=True,
        xaxis=dict(title='Porosité (%)', showgrid=False, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        yaxis=dict(title=y_label + (f' ({y_unit})' if y_unit else ''),
                   type='log' if y_log else 'linear',
                   gridcolor=ZN100, linecolor=ZN200, zeroline=False,
                   tickfont=dict(size=10, color=ZN500)),
        margin=dict(l=62, r=16, t=18, b=46),
        legend=dict(orientation='h', yanchor='bottom', y=1.04, xanchor='left', x=0,
                    font=dict(size=10, color=ZN700)),
    ))
    return fig


def build_acoustique():
    th_s = {'fontSize': '0.68rem', 'fontWeight': '700', 'textTransform': 'uppercase',
            'letterSpacing': '0.07em', 'color': ZN400, 'padding': '0 14px 11px 14px',
            'borderBottom': f'1px solid {ZN200}', 'textAlign': 'left'}

    gen_rows = []
    for _, r in DF_ACOUS.iterrows():
        is_ref = r['nom'] == 'F1_originel'
        gen_rows.append(html.Tr([
            html.Td(r['nom'].replace('_', ' '),
                    style={'fontWeight': '700' if is_ref else '400',
                           'color': ZN700, 'fontSize': '0.82rem',
                           'padding': '10px 14px'}),
            html.Td(f"{r['porosite']*100:.1f} %", className='tabnum',
                    style={'padding': '10px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['tortuosite']:.4f}", className='tabnum',
                    style={'padding': '10px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['sv']:.2f}", className='tabnum',
                    style={'padding': '10px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['lambda_v_um']:.1f}", className='tabnum',
                    style={'padding': '10px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['lambda_t_um']:.1f}", className='tabnum',
                    style={'padding': '10px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
            html.Td(f"{r['sigma']:,.0f}", className='tabnum',
                    style={'padding': '10px 14px', 'fontSize': '0.82rem', 'color': ZN700}),
        ], style={'background': ZN100 if is_ref else CARD,
                  'borderBottom': f'1px solid {ZN200}'}))

    acous_table = html.Table([
        html.Thead(html.Tr([
            html.Th('Échantillon', style=th_s),
            html.Th('Porosité φ', style=th_s),
            html.Th('Tortuosité τ', style=th_s),
            html.Th('Sv (mm⁻¹)', style=th_s),
            html.Th('Λ visc. (µm)', style=th_s),
            html.Th('Λ\' therm. (µm)', style=th_s),
            html.Th('σ (N·s·m⁻⁴)', style=th_s),
        ])),
        html.Tbody(gen_rows),
    ], style={'width': '100%', 'borderCollapse': 'collapse'})

    return html.Div([

        insight(
            'Ces 4 structures générées numériquement permettent d\'étudier comment la microstructure '
            'fibreuse influence les propriétés acoustiques macroscopiques via le modèle JCAL. '
            'La porosité varie de 87.7 % à 95 % — des tendances claires émergent sur chaque paramètre. '
            'L\'étoile (★) représente le scan réel F1 comme référence.',
            color=ZN800, bg=ZN100, border=ZN200,
        ),

        card(chart_head('Paramètres JCAL — Tableau récapitulatif',
                        '★ F1 Référence = scan réel F1_originel · F1–F4 = structures numériques'),
             acous_table),

        grid(
            card(chart_head('Surface spécifique Sv vs porosité',
                            'Sv ↑ quand porosité ↓ → fibres plus denses, surfaces plus grandes',
                            question='Comment la densité fibreuse affecte-t-elle la surface spécifique ?'),
                 G(_acous_scatter('sv', 'Sv', y_unit='mm⁻¹')), mb='0'),
            card(chart_head('Tortuosité vs porosité',
                            'Tortuosité ↑ quand porosité ↓ → chemin plus sinueux pour l\'onde',
                            question='Les fibres plus denses créent-elles des chemins acoustiques plus tortueux ?'),
                 G(_acous_scatter('tortuosite', 'Tortuosité')), mb='0'),
        ),

        grid(
            card(chart_head('Longueur visqueuse Λ vs porosité',
                            'Λ ↓ quand Sv ↑ → constrictions plus petites, dissipation visqueuse plus forte',
                            question='Comment la microstructure contrôle-t-elle la dissipation visqueuse ?'),
                 G(_acous_scatter('lambda_v_um', 'Λ visqueuse', y_unit='µm')), mb='0'),
            card(chart_head('Longueur thermique Λ\' vs porosité',
                            'Λ\' > Λ : l\'échange thermique agit à une échelle plus grande que la viscosité',
                            question='Pourquoi la longueur thermique est-elle toujours supérieure à la longueur visqueuse ?'),
                 G(_acous_scatter('lambda_t_um', 'Λ\' thermique', y_unit='µm')), mb='0'),
        ),

        card(chart_head('Résistivité au flux σ vs porosité',
                        'Échelle logarithmique — σ varie sur 2 ordres de grandeur entre F1 (poreux) et F4 (dense)',
                        question='Quel paramètre de microstructure domine la résistivité au flux d\'air ?'),
             G(_acous_scatter('sigma', 'σ', y_log=True, y_unit='N·s·m⁻⁴'))),

        card(
            html.Div('Modèle JCAL — Guide des paramètres', style={
                'fontSize': '0.67rem', 'fontWeight': '700', 'color': ZN400,
                'letterSpacing': '0.08em', 'textTransform': 'uppercase', 'marginBottom': '16px',
            }),
            html.Div([
                html.Div([
                    html.Div('Sv — Surface spécifique volumique (mm⁻¹)',
                             style={'fontWeight': '700', 'fontSize': '0.82rem', 'color': ZN800, 'marginBottom': '3px'}),
                    html.Div('Rapport surface / volume du réseau poreux. Lié au diamètre des fibres : d ≈ 4(1−φ)/Sv. '
                             'Plus Sv est élevé, plus les fibres sont fines et serrées.',
                             style={'fontSize': '0.77rem', 'color': ZN500, 'lineHeight': '1.55'}),
                ], style={'marginBottom': '14px'}),
                html.Div([
                    html.Div('Λ — Longueur visqueuse (µm)',
                             style={'fontWeight': '700', 'fontSize': '0.82rem', 'color': ZN800, 'marginBottom': '3px'}),
                    html.Div('Caractérise la dissipation d\'énergie par viscosité dans les constrictions. '
                             'Λ ≈ 2V_pore / S_pore pour les sections les plus étroites du réseau.',
                             style={'fontSize': '0.77rem', 'color': ZN500, 'lineHeight': '1.55'}),
                ], style={'marginBottom': '14px'}),
                html.Div([
                    html.Div('σ — Résistivité au flux d\'air (N·s·m⁻⁴)',
                             style={'fontWeight': '700', 'fontSize': '0.82rem', 'color': ZN800, 'marginBottom': '3px'}),
                    html.Div('Résistance globale à l\'écoulement de l\'air. Paramètre dominant pour '
                             'l\'absorption acoustique basse fréquence. Varie de 12 k à 1.4 M entre F1 et F4.',
                             style={'fontSize': '0.77rem', 'color': ZN500, 'lineHeight': '1.55'}),
                ]),
            ]),
        ),

    ], style={'padding': '24px'})


# ══════════════════════════════════════════════════════════════════════════════
#  APP & LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

TAB_STYLE = dict(
    color=ZN400, fontFamily=FONT, fontSize='0.82rem',
    padding='13px 20px', border='none', fontWeight='500',
    borderBottom='3px solid transparent', background='transparent',
    letterSpacing='-0.01em',
)
TAB_SEL = {**TAB_STYLE, 'borderBottom': f'3px solid {INDIGO}',
           'fontWeight': '700', 'color': ZN900}

app = dash.Dash(__name__, title='FiberScope', suppress_callback_exceptions=True,
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
    ],
)
server = app.server

app.layout = html.Div([

    # Barre d'accent gradient (rendue via CSS ::before sur body)
    html.Div(style={'height': '3px',
                    'background': f'linear-gradient(90deg, {INDIGO} 0%, {EMERALD} 100%)'}),

    # En-tête
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Span('FiberScope', style={
                        'fontSize': '1.05rem', 'fontWeight': '800',
                        'color': ZN900, 'letterSpacing': '-0.04em',
                    }),
                    html.Span(' · Analyse microstructure fibreuse', style={
                        'fontSize': '0.82rem', 'color': ZN500,
                        'fontWeight': '400', 'marginLeft': '6px',
                    }),
                ], style={'marginBottom': '4px'}),
                html.Div('ESIEE Paris · MSME CNRS UMR 8208 · Projet E4',
                         style={'fontSize': '0.73rem', 'color': ZN400, 'fontWeight': '500'}),
            ]),
            method_pills(),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                  'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 24px'}),
    ], style={'background': CARD, 'borderBottom': f'1px solid {ZN200}', 'padding': '15px 0'}),

    # Navigation
    dcc.Tabs(id='tabs', value='overview',
        style={'background': CARD, 'borderBottom': f'1px solid {ZN200}',
               'paddingLeft': '18px', 'paddingTop': '4px'},
        children=[
            dcc.Tab(label='Contexte & Données',   value='overview',    style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Orientation',           value='orient',      style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Morphologie',           value='morphologie', style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Bilan comparatif',      value='compare',     style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label='Acoustique',            value='acoustique',  style=TAB_STYLE, selected_style=TAB_SEL),
        ],
    ),

    html.Div(id='content', style={'maxWidth': '1400px', 'margin': '0 auto'}),

    html.Div([
        html.Span([
            html.Span('●', style={'color': INDIGO, 'marginRight': '4px'}),
            html.Span('Dragonfly', style={'fontWeight': '600', 'marginRight': '16px', 'color': ZN700}),
            html.Span('●', style={'color': EMERALD, 'marginRight': '4px'}),
            html.Span('MATLAB', style={'fontWeight': '600', 'marginRight': '20px', 'color': ZN700}),
        ]),
        html.Span(
            f'{VOX_UM} µm/vox (Drag.) · ~10 µm/vox (MATLAB) · '
            f'{len(FIB)} fibres · {len(DF_NOL)} composantes · '
            f'Porosité ~{POROSITY}% · F1 Recyclé',
            className='tabnum',
        ),
    ], style={'textAlign': 'center', 'padding': '18px', 'fontSize': '0.71rem',
              'color': ZN400, 'borderTop': f'1px solid {ZN200}',
              'background': CARD, 'display': 'flex', 'justifyContent': 'center',
              'alignItems': 'center', 'gap': '4px'}),

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
            marker=dict(color=INDIGO, opacity=0.78, line=dict(color='white', width=0.5)),
            hovertemplate='%{x:.0f}° : %{y:.1f}%<extra>Dragonfly</extra>',
        ))
    if method in ('both', 'nolhan'):
        fig.add_trace(go.Histogram(
            x=DF_NOL['angle_h'], name=f'MATLAB — méd. {NOL_ANG_MED}°',
            histnorm='percent', xbins=dict(size=3),
            marker=dict(color=EMERALD, opacity=0.75, line=dict(color='white', width=0.5)),
            hovertemplate='%{x:.0f}° : %{y:.1f}%<extra>MATLAB</extra>',
        ))
    fig.update_layout(**lay(h=280, lg=(method == 'both'), barmode='overlay',
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
