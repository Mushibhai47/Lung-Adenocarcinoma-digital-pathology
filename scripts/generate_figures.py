"""
generate_figures.py
Generates all figures for the GitHub repository:
  1. Pipeline overview diagram
  2. Kaplan-Meier curves (Chapter 2 — STAS and pN)
  3. Kaplan-Meier curves (Chapter 4 — digital metrics)
  4. Distribution plots for lymphocyte and tumour cell density
  5. Inter-ROI reproducibility scatter plots
"""
import sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from scipy import stats
import pyreadstat
from lifelines import KaplanMeierFitter

# Output folder
import os
fig_dir = r'C:\Users\musha\Desktop\QuPath\docs\images'
os.makedirs(fig_dir, exist_ok=True)

BLUE   = '#2E75B6'
DKBLUE = '#1F3864'
GREEN  = '#548235'
ORANGE = '#C55A11'
RED    = '#C00000'
GREY   = '#595959'
LGREY  = '#D9D9D9'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 11,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 150,
})

# ── Load data ────────────────────────────────────────────────────────────
df_spss, meta = pyreadstat.read_sav(r'C:\Users\musha\Desktop\QuPath\Lung_june2025.sav')
vl = meta.variable_value_labels
df = df_spss.copy()
df['Surgery_date'] = pd.to_datetime(df['Surgery_date'])
df['dateofdeathorlastcontact'] = pd.to_datetime(df['dateofdeathorlastcontact'])
df['surv_months'] = (df['dateofdeathorlastcontact'] - df['Surgery_date']).dt.days / 30.44
df['event'] = df['Status'].astype(int)
df = df[df['surv_months'] > 0].copy()

df_dig = pd.read_csv(r'C:\Users\musha\Desktop\QuPath\analysis_results.csv')

# ════════════════════════════════════════════════════════════════════════
# FIGURE 1: PIPELINE OVERVIEW DIAGRAM
# ════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 9))
ax.set_xlim(0, 14); ax.set_ylim(0, 9)
ax.axis('off')
ax.set_facecolor('#F8F9FA')
fig.patch.set_facecolor('#F8F9FA')

def box(ax, x, y, w, h, text, sub='', color=BLUE, fontsize=11):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle="round,pad=0.15",
                           linewidth=1.5, edgecolor=color,
                           facecolor=color + '22')
    ax.add_patch(rect)
    ax.text(x, y + (0.15 if sub else 0), text, ha='center', va='center',
            fontsize=fontsize, fontweight='bold', color=color, wrap=True)
    if sub:
        ax.text(x, y - 0.28, sub, ha='center', va='center',
                fontsize=8.5, color=GREY)

def arrow(ax, x1, y1, x2, y2, color=GREY):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8))

# Title
ax.text(7, 8.5, 'Digital Pathology Analysis Pipeline', ha='center', va='center',
        fontsize=16, fontweight='bold', color=DKBLUE)
ax.text(7, 8.1, 'Lung Adenocarcinoma — QuPath H&E Workflow', ha='center', va='center',
        fontsize=12, color=GREY)

# Row 1: Input
box(ax, 2, 7.0, 3.2, 0.9, '173 Resected Cases',       'CHUC 2015–2019', DKBLUE)
box(ax, 7, 7.0, 3.2, 0.9, 'Whole Slide Imaging',       '171 digitised H&E slides', BLUE)
box(ax, 12, 7.0, 3.2, 0.9, 'Clinical Database',        'SPSS + Excel (172 pts)', GREEN)

# Arrows row 1 → row 2
arrow(ax, 3.6, 7.0, 5.4, 7.0)
arrow(ax, 8.6, 7.0, 10.4, 7.0)
arrow(ax, 7, 6.55, 7, 6.05)

# Row 2: Processing
box(ax, 3.5, 5.6, 3.2, 0.9, 'ROI Annotation',          '2 × 4 mm² per case', BLUE)
box(ax, 7,   5.6, 3.2, 0.9, 'Cell Detection (QuPath)',  'WatershedCellDetection', BLUE)
box(ax, 10.5,5.6, 3.2, 0.9, 'Cell Classification',      'Lymphocytes vs Tumour', BLUE)

arrow(ax, 3.5, 6.55, 3.5, 6.05)
arrow(ax, 5.1, 5.6, 5.4, 5.6)
arrow(ax, 8.6, 5.6, 8.9, 5.6)

# Row 3: Outputs
box(ax, 2,   4.1, 2.8, 0.9, 'Lymphocyte Density',   'cells/mm²  per ROI', ORANGE)
box(ax, 5,   4.1, 2.8, 0.9, 'Tumour Cell Density',  'cells/mm²  per ROI', ORANGE)
box(ax, 8,   4.1, 2.8, 0.9, 'T:L Ratio',            'Tumour / Lymphocyte', ORANGE)
box(ax, 11,  4.1, 2.8, 0.9, 'Slide–Patient Linkage','141/173 mapped (81.5%)', GREEN)

arrow(ax, 3.5, 5.15, 3, 4.55)
arrow(ax, 7,   5.15, 6, 4.55)
arrow(ax, 7,   5.15, 8, 4.55)
arrow(ax, 10.5,5.15, 11, 4.55)

# Row 4: Analysis
box(ax, 3.5, 2.7, 3.2, 0.9, 'Descriptive Statistics','Distributions & variability', DKBLUE)
box(ax, 7,   2.7, 3.2, 0.9, 'Clinicopathologic\nAssociations','Mann–Whitney U', DKBLUE)
box(ax, 10.5,2.7, 3.2, 0.9, 'Survival Analysis',     'Kaplan–Meier + Cox', DKBLUE)

for xs, xe in [(2,3.5),(5,5),(8,7),(11,10.5)]:
    arrow(ax, xs, 3.65, xe, 3.15)

# Row 5: Result
box(ax, 7, 1.35, 8, 0.85,
    'Key Result: Workflow validated (r=0.907). No significant prognostic associations.',
    'Foundation for future DL-based classification', RED)

arrow(ax, 3.5, 2.25, 5.5, 1.7)
arrow(ax, 7,   2.25, 7,   1.8)
arrow(ax, 10.5,2.25, 8.5, 1.7)

# Legend
for i, (label, color) in enumerate([('Input/Data', DKBLUE),('Processing', BLUE),
                                      ('Output metrics', ORANGE),('Linkage/Clinical', GREEN),
                                      ('Final finding', RED)], 0):
    rect = mpatches.Patch(color=color+'33', label=label,
                          linewidth=1.5, edgecolor=color)
    ax.text(0.5 + i*2.7, 0.35, '■ ' + label, color=color, fontsize=9, ha='left')

plt.tight_layout()
plt.savefig(f'{fig_dir}/fig1_pipeline_overview.png', dpi=150, bbox_inches='tight',
            facecolor='#F8F9FA')
plt.close()
print("Saved fig1_pipeline_overview.png")

# ════════════════════════════════════════════════════════════════════════
# FIGURE 2: KM CURVES — Chapter 2 (STAS and pN)
# ════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
fig.suptitle('Overall Survival — Conventional Clinicopathologic Factors\n'
             'Surgically Resected Lung Adenocarcinoma (n = 172)',
             fontsize=13, fontweight='bold', color=DKBLUE, y=1.01)

df_stas = df[df['STAS'].isin([0,1])].copy()

for ax, (col, g0val, g1val, g0lab, g1lab, c0, c1, title, foot) in zip(axes, [
    ('STAS', 0, 1, 'STAS-negative (n=130)', 'STAS-positive (n=41)',
     BLUE, RED, 'Spread Through Air Spaces (STAS)', 'Log-rank p = 0.028;  HR = 1.73 (1.05–2.84)'),
    ('Nplus', 0, 1, 'N0 (n=134)', 'N+ (n=38)',
     BLUE, RED, 'Nodal Status', 'Log-rank p < 0.001;  HR = 2.60 (1.58–4.26)')
]):
    dfw = df_stas if col=='STAS' else df.copy()
    if col == 'Nplus':
        dfw['Nplus'] = (dfw['pN'] > 0).astype(int)

    g0 = dfw[dfw[col] == g0val]
    g1 = dfw[dfw[col] == g1val]

    kmf0 = KaplanMeierFitter(); kmf0.fit(g0['surv_months'], g0['event'], label=g0lab)
    kmf1 = KaplanMeierFitter(); kmf1.fit(g1['surv_months'], g1['event'], label=g1lab)

    kmf0.plot_survival_function(ax=ax, color=BLUE, linewidth=2.2, ci_show=True, ci_alpha=0.12)
    kmf1.plot_survival_function(ax=ax, color=RED, linewidth=2.2, ci_show=True, ci_alpha=0.12)

    ax.set_title(title, fontsize=12, fontweight='bold', color=DKBLUE, pad=8)
    ax.set_xlabel('Time from Surgery (months)', fontsize=10)
    ax.set_ylabel('Overall Survival Probability', fontsize=10)
    ax.set_ylim(0, 1.05); ax.set_xlim(0)
    ax.text(0.97, 0.97, foot, transform=ax.transAxes, ha='right', va='top',
            fontsize=9, style='italic', color=GREY,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=LGREY, alpha=0.8))
    ax.legend(frameon=False, fontsize=9, loc='lower left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_facecolor('#FAFAFA')

plt.tight_layout()
plt.savefig(f'{fig_dir}/fig2_km_chapter2.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_km_chapter2.png")

# ════════════════════════════════════════════════════════════════════════
# FIGURE 3: KM CURVES — Chapter 4 digital metrics (null results)
# ════════════════════════════════════════════════════════════════════════
df_s = df_dig.merge(
    df[['FICHA','surv_months','event']].rename(columns={'FICHA':'FICHA'}),
    on='FICHA', how='inner'
).dropna(subset=['surv_months','event','lymp_mean','tumor_mean'])

fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
fig.suptitle('Overall Survival by Digital Pathology Metrics (n = 141, 63 events)\n'
             'Kaplan–Meier with Median Dichotomisation',
             fontsize=13, fontweight='bold', color=DKBLUE, y=1.01)

for ax, (col, split, label, p_val) in zip(axes, [
    ('lymp_mean',   109.2, 'Lymphocyte Density\n(split at 109.2 cells/mm²)',  'Log-rank p = 0.855'),
    ('tumor_mean', 1122.4, 'Tumour Cell Density\n(split at 1122.4 cells/mm²)','Log-rank p = 0.530'),
    ('ratio_mean',    6.2, 'Tumour:Lymphocyte Ratio\n(split at 6.2)',          'Log-rank p = 0.596'),
]):
    g_lo = df_s[df_s[col] <= split]
    g_hi = df_s[df_s[col] >  split]
    kmf0 = KaplanMeierFitter(); kmf0.fit(g_lo['surv_months'], g_lo['event'], label=f'Low (n={len(g_lo)})')
    kmf1 = KaplanMeierFitter(); kmf1.fit(g_hi['surv_months'], g_hi['event'], label=f'High (n={len(g_hi)})')
    kmf0.plot_survival_function(ax=ax, color=BLUE,  linewidth=2.2, ci_show=True, ci_alpha=0.12)
    kmf1.plot_survival_function(ax=ax, color=GREEN, linewidth=2.2, ci_show=True, ci_alpha=0.12)
    ax.set_title(label, fontsize=11, fontweight='bold', color=DKBLUE, pad=8)
    ax.set_xlabel('Time from Surgery (months)', fontsize=10)
    ax.set_ylabel('Overall Survival Probability', fontsize=10)
    ax.set_ylim(0, 1.05); ax.set_xlim(0)
    ax.text(0.97, 0.97, p_val + '\n(not significant)', transform=ax.transAxes,
            ha='right', va='top', fontsize=9, style='italic', color=GREY,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=LGREY, alpha=0.8))
    ax.legend(frameon=False, fontsize=9, loc='lower left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_facecolor('#FAFAFA')

plt.tight_layout()
plt.savefig(f'{fig_dir}/fig3_km_chapter4.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_km_chapter4.png")

# ════════════════════════════════════════════════════════════════════════
# FIGURE 4: DENSITY DISTRIBUTIONS
# ════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('Distribution of Digital Pathology Metrics Across 141 Cases',
             fontsize=13, fontweight='bold', color=DKBLUE)

lymp_all = pd.concat([df_dig['lymp_ROI1'], df_dig['lymp_ROI2']]).dropna()
tumo_all = pd.concat([df_dig['tumor_ROI1'], df_dig['tumor_ROI2']]).dropna()

for ax, data, label, color, mean_v, med_v in [
    (axes[0], lymp_all, 'Lymphocyte Density (cells/mm²)', BLUE,
     data.mean() if False else lymp_all.mean(), lymp_all.median()),
    (axes[1], tumo_all, 'Tumour Cell Density (cells/mm²)', GREEN,
     tumo_all.mean(), tumo_all.median()),
]:
    ax.hist(data, bins=35, color=color, alpha=0.75, edgecolor='white', linewidth=0.5)
    ax.axvline(mean_v, color=RED, linestyle='--', linewidth=1.8, label=f'Mean = {mean_v:.0f}')
    ax.axvline(med_v,  color=ORANGE, linestyle='-',  linewidth=1.8, label=f'Median = {med_v:.0f}')
    ax.set_xlabel(label, fontsize=11)
    ax.set_ylabel('Number of ROIs (n = 282)', fontsize=11)
    ax.legend(frameon=False, fontsize=10)
    ax.set_facecolor('#FAFAFA')
    ax.grid(axis='y', alpha=0.25, linestyle='--')
    ax.text(0.97, 0.97, f'n = {len(data)} ROIs\nCV = {100*data.std()/data.mean():.1f}%',
            transform=ax.transAxes, ha='right', va='top', fontsize=9, color=GREY,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=LGREY, alpha=0.8))

plt.tight_layout()
plt.savefig(f'{fig_dir}/fig4_density_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_density_distributions.png")

# ════════════════════════════════════════════════════════════════════════
# FIGURE 5: INTER-ROI REPRODUCIBILITY SCATTER
# ════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
fig.suptitle('Intra-tumoral Reproducibility: ROI 1 vs ROI 2\n(n = 141 case pairs)',
             fontsize=13, fontweight='bold', color=DKBLUE)

for ax, (col1, col2, label, color, r_val) in zip(axes, [
    ('lymp_ROI1',  'lymp_ROI2',  'Lymphocyte Density (cells/mm²)',  BLUE,  0.882),
    ('tumor_ROI1', 'tumor_ROI2', 'Tumour Cell Density (cells/mm²)', GREEN, 0.907),
]):
    x = df_dig[col1].dropna()
    y = df_dig[col2].dropna()
    idx = x.index.intersection(y.index)
    x, y = x[idx], y[idx]

    ax.scatter(x, y, alpha=0.55, s=28, color=color, edgecolors='white', linewidth=0.3)
    # Line of identity
    lim = max(x.max(), y.max()) * 1.05
    ax.plot([0, lim], [0, lim], 'k--', linewidth=1, alpha=0.4, label='Line of identity')
    # Regression line
    m, b, *_ = stats.linregress(x, y)
    xr = np.linspace(0, lim, 200)
    ax.plot(xr, m*xr + b, color=RED, linewidth=1.8, label=f'Regression line')

    ax.set_xlabel(f'ROI 1 — {label}', fontsize=10)
    ax.set_ylabel(f'ROI 2 — {label}', fontsize=10)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.text(0.05, 0.93, f'Pearson r = {r_val:.3f}\np < 0.001',
            transform=ax.transAxes, fontsize=11, color=DKBLUE, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.35', facecolor=color+'22', edgecolor=color))
    ax.legend(frameon=False, fontsize=9, loc='lower right')
    ax.set_facecolor('#FAFAFA')
    ax.grid(alpha=0.25, linestyle='--')

plt.tight_layout()
plt.savefig(f'{fig_dir}/fig5_reproducibility.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig5_reproducibility.png")

print("\nAll 5 figures saved to:", fig_dir)
