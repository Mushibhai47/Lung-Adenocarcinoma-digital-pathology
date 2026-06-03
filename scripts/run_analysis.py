#!/usr/bin/env python3
"""
Complete statistical analysis for lung adenocarcinoma thesis.
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ─── 1. LOAD DATA ────────────────────────────────────────────────────────────
print("=" * 70)
print("STEP 1: LOADING AND MERGING DATA")
print("=" * 70)

clinical = pd.read_excel('Lung_june2025_slidenumber.xlsx')
lymp_raw  = pd.read_csv('lymphocyte_results_clean.csv')
tumor_raw = pd.read_csv('tumor_cell_results_clean.csv')

# Extract slide_id from Coluna1 (e.g. slide-...-R2-S9.qpdata → R2-S9)
def extract_slide_id(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    # Handle typo: 'lide-...' (missing leading 's')
    import re
    m = re.search(r'(R\d+-S\d+)\.qpdata', val)
    if m:
        return m.group(1)
    return None

clinical['slide_id'] = clinical['Coluna1'].apply(extract_slide_id)
clinical_mapped = clinical[clinical['slide_id'].notna()].copy()
print(f"Clinical rows with slide mapping: {len(clinical_mapped)}")

# ─── 2. AGGREGATE DENSITIES PER SLIDE ────────────────────────────────────────
# For slides with >2 regions, use only Region_Index 1 and 2 (the canonical ROIs)
# (Extra regions appear to be repeated/extra annotations)

lymp_r1 = lymp_raw[lymp_raw['Region_Index'] == 1][['slide_id', 'Lymphocyte_Density_per_mm2']].rename(
    columns={'Lymphocyte_Density_per_mm2': 'lymp_ROI1'})
lymp_r2 = lymp_raw[lymp_raw['Region_Index'] == 2][['slide_id', 'Lymphocyte_Density_per_mm2']].rename(
    columns={'Lymphocyte_Density_per_mm2': 'lymp_ROI2'})

tumor_r1 = tumor_raw[tumor_raw['Region_Index'] == 1][['slide_id', 'Tumor_Cell_Density_per_mm2']].rename(
    columns={'Tumor_Cell_Density_per_mm2': 'tumor_ROI1'})
tumor_r2 = tumor_raw[tumor_raw['Region_Index'] == 2][['slide_id', 'Tumor_Cell_Density_per_mm2']].rename(
    columns={'Tumor_Cell_Density_per_mm2': 'tumor_ROI2'})

# Merge density data
density = lymp_r1.merge(lymp_r2, on='slide_id', how='outer') \
                 .merge(tumor_r1, on='slide_id', how='outer') \
                 .merge(tumor_r2, on='slide_id', how='outer')

# Per-case means and ratio
density['lymp_mean']  = (density['lymp_ROI1'] + density['lymp_ROI2']) / 2
density['tumor_mean'] = (density['tumor_ROI1'] + density['tumor_ROI2']) / 2
density['ratio_mean'] = np.where(
    density['lymp_mean'] > 0,
    density['tumor_mean'] / density['lymp_mean'],
    np.nan
)

print(f"Density records (slides with >=1 ROI): {len(density)}")

# ─── 3. MERGE WITH CLINICAL DATA ─────────────────────────────────────────────
# Map clinical columns
clinical_cols = ['slide_id', 'FICHA', 'Survival_months', 'Status',
                 'Stage_group', 'STAS', 'pN',
                 'Lymphovascular_Invasion', 'Visceral_Pleural_Invasion',
                 'Patient_age', 'Patient_sex', 'Tumor_size']
clin = clinical_mapped[clinical_cols].copy()

merged = clin.merge(density, on='slide_id', how='inner')
print(f"Merged cases (clinical + density): {len(merged)}")

# Exclude STAS=99 (unknown/missing)
merged = merged[merged['STAS'] != 99]
print(f"After excluding STAS=99: {len(merged)}")

# Stage_group encoding: values 1-8 observed
# Based on clinical context for lung adenocarcinoma and AJCC staging:
# We'll create a binary: Stage_early (I) vs Stage_advanced (II/III)
# Stage_group values: need to interpret — let's check distribution
print("\nStage_group value counts:")
print(merged['Stage_group'].value_counts().sort_index())

# Based on typical AJCC encoding in SPSS exports for lung:
# 1=IA1, 2=IA2, 3=IA3, 4=IB, 5=IIA, 6=IIB, 7=IIIA, 8=IIIB
# Stage I = values 1,2,3,4; Stage II/III = 5,6,7,8
merged['Stage_I_vs_higher'] = (merged['Stage_group'] <= 4).astype(int)
merged['Stage_label'] = merged['Stage_group'].map({
    1:'IA1', 2:'IA2', 3:'IA3', 4:'IB', 5:'IIA', 6:'IIB', 7:'IIIA', 8:'IIIB'
})

# pN binary: N0 vs N+
merged['pN_binary'] = (merged['pN'] >= 1).astype(int)

# Complete cases for density
complete = merged.dropna(subset=['lymp_mean', 'tumor_mean', 'lymp_ROI1', 'lymp_ROI2',
                                  'tumor_ROI1', 'tumor_ROI2']).copy()
print(f"\nComplete cases for density analysis: {len(complete)}")
print(f"Deaths (Status=1): {complete['Status'].sum()}")
print(f"Alive (Status=0): {(complete['Status']==0).sum()}")

# Save merged dataset
merged.to_csv('analysis_results.csv', index=False)
print("\nSaved analysis_results.csv")


# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────
def fmt_p(p):
    """Format p-value for reporting."""
    if p < 0.001:
        return "p<0.001"
    return f"p={p:.3f}"

def iqr_str(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    return f"{series.median():.1f} ({q1:.1f}–{q3:.1f})"

def mwu_test(g1, g2):
    """Mann-Whitney U, two-sided."""
    g1 = g1.dropna()
    g2 = g2.dropna()
    if len(g1) < 2 or len(g2) < 2:
        return np.nan, np.nan
    u, p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
    return u, p

def significance_label(p):
    if p < 0.05:
        return "significant"
    elif p < 0.10:
        return "trend toward significance"
    else:
        return "not significant"


# ─── A. DESCRIPTIVE STATISTICS ────────────────────────────────────────────────
print("\n" + "=" * 70)
print("A. DESCRIPTIVE STATISTICS")
print("=" * 70)

desc_results = {}
for col, label in [('lymp_mean', 'Lymphocyte density (cells/mm²)'),
                    ('tumor_mean', 'Tumour cell density (cells/mm²)'),
                    ('ratio_mean', 'Tumour:lymphocyte ratio')]:
    s = complete[col].dropna()
    desc = {
        'n': len(s),
        'mean': s.mean(),
        'sd': s.std(),
        'median': s.median(),
        'q1': s.quantile(0.25),
        'q3': s.quantile(0.75),
        'min': s.min(),
        'max': s.max(),
    }
    desc_results[col] = desc
    print(f"\n{label} (n={desc['n']}):")
    print(f"  Mean ± SD:   {desc['mean']:.1f} ± {desc['sd']:.1f}")
    print(f"  Median (IQR): {desc['median']:.1f} ({desc['q1']:.1f}–{desc['q3']:.1f})")
    print(f"  Range:        {desc['min']:.1f}–{desc['max']:.1f}")


# ─── B. INTRA-TUMORAL VARIABILITY ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("B. INTRA-TUMORAL VARIABILITY (ROI 1 vs ROI 2 Pearson correlation)")
print("=" * 70)

ivar_results = {}
for metric, r1_col, r2_col, label in [
    ('lymp', 'lymp_ROI1', 'lymp_ROI2', 'Lymphocyte density'),
    ('tumor', 'tumor_ROI1', 'tumor_ROI2', 'Tumour cell density')
]:
    pair = complete[[r1_col, r2_col]].dropna()
    r, p = stats.pearsonr(pair[r1_col], pair[r2_col])
    # CV across all ROI values
    all_vals = pd.concat([complete[r1_col], complete[r2_col]]).dropna()
    cv = (all_vals.std() / all_vals.mean()) * 100
    ivar_results[metric] = {'r': r, 'p': p, 'cv': cv, 'n': len(pair)}
    print(f"\n{label}:")
    print(f"  n pairs = {len(pair)}")
    print(f"  Pearson r = {r:.3f}, {fmt_p(p)}")
    print(f"  CV (all ROIs) = {cv:.1f}%")


# ─── C. ASSOCIATIONS WITH CLINICOPATHOLOGIC FEATURES ─────────────────────────
print("\n" + "=" * 70)
print("C. ASSOCIATIONS WITH CLINICOPATHOLOGIC FEATURES (Mann-Whitney U)")
print("=" * 70)

assoc_results = {}

comparisons = [
    ('STAS', 'STAS', 0, 1, 'STAS-negative', 'STAS-positive'),
    ('pN_binary', 'pN', 0, 1, 'N0', 'N+'),
    ('Stage_I_vs_higher', 'Stage', 1, 0, 'Stage I', 'Stage II/III'),
    ('Lymphovascular_Invasion', 'LVI', 0, 1, 'LVI-negative', 'LVI-positive'),
    ('Visceral_Pleural_Invasion', 'VPI', 0, 1, 'VPI-negative', 'VPI-positive'),
]

for col, label, val0, val1, name0, name1 in comparisons:
    assoc_results[label] = {}
    print(f"\n--- {label} ---")
    for metric, mlabel in [('lymp_mean', 'Lymphocyte density'),
                             ('tumor_mean', 'Tumour cell density'),
                             ('ratio_mean', 'Tumour:lymphocyte ratio')]:
        sub = complete[[col, metric]].dropna()
        g0 = sub[sub[col] == val0][metric]
        g1 = sub[sub[col] == val1][metric]
        u, p = mwu_test(g0, g1)
        key = f"{label}_{metric}"
        assoc_results[key] = {
            'group0_label': name0, 'group0_n': len(g0),
            'group0_median': g0.median(), 'group0_q1': g0.quantile(0.25), 'group0_q3': g0.quantile(0.75),
            'group1_label': name1, 'group1_n': len(g1),
            'group1_median': g1.median(), 'group1_q1': g1.quantile(0.25), 'group1_q3': g1.quantile(0.75),
            'U': u, 'p': p
        }
        sig = significance_label(p) if not np.isnan(p) else "N/A"
        print(f"  {mlabel}:")
        print(f"    {name0} (n={len(g0)}): median {g0.median():.1f} ({g0.quantile(0.25):.1f}–{g0.quantile(0.75):.1f})")
        print(f"    {name1} (n={len(g1)}): median {g1.median():.1f} ({g1.quantile(0.25):.1f}–{g1.quantile(0.75):.1f})")
        print(f"    U={u:.0f}, {fmt_p(p)} [{sig}]")


# ─── D. SURVIVAL ANALYSIS ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("D. SURVIVAL ANALYSIS")
print("=" * 70)

from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test

surv = complete.dropna(subset=['Survival_months', 'Status', 'lymp_mean', 'tumor_mean', 'ratio_mean']).copy()
print(f"\nSurvival dataset: n={len(surv)}, events={surv['Status'].sum()}")

# Kaplan-Meier with log-rank
km_results = {}

for metric, mlabel in [('lymp_mean', 'lymphocyte density'),
                         ('tumor_mean', 'tumour cell density'),
                         ('ratio_mean', 'tumour:lymphocyte ratio')]:
    threshold = surv[metric].median()
    high = surv[surv[metric] >= threshold]
    low  = surv[surv[metric] <  threshold]

    lr = logrank_test(
        low['Survival_months'],  low['Status'],
        high['Survival_months'], high['Status']
    )

    # KM median survival
    kmf_low  = KaplanMeierFitter()
    kmf_high = KaplanMeierFitter()
    kmf_low.fit(low['Survival_months'],  low['Status'])
    kmf_high.fit(high['Survival_months'], high['Status'])

    med_low  = kmf_low.median_survival_time_
    med_high = kmf_high.median_survival_time_

    km_results[metric] = {
        'threshold': threshold,
        'n_low': len(low), 'events_low': int(low['Status'].sum()),
        'n_high': len(high), 'events_high': int(high['Status'].sum()),
        'med_low': med_low, 'med_high': med_high,
        'logrank_p': lr.p_value
    }

    sig = significance_label(lr.p_value)
    print(f"\nKaplan-Meier — {mlabel} (split at median {threshold:.1f}):")
    print(f"  Low (n={len(low)}, events={int(low['Status'].sum())}): median OS = {med_low:.1f} months")
    print(f"  High (n={len(high)}, events={int(high['Status'].sum())}): median OS = {med_high:.1f} months")
    print(f"  Log-rank {fmt_p(lr.p_value)} [{sig}]")

# Univariate Cox regression
print("\n--- Univariate Cox Regression ---")
cox_univar = {}

for metric, mlabel in [('lymp_mean', 'Lymphocyte density'),
                         ('tumor_mean', 'Tumour cell density'),
                         ('ratio_mean', 'Tumour:lymphocyte ratio')]:
    surv_temp = surv[['Survival_months', 'Status', metric]].dropna().copy()
    # Log-transform (add 1 to handle zeros)
    surv_temp[f'log_{metric}'] = np.log1p(surv_temp[metric])

    cph = CoxPHFitter()
    cph.fit(surv_temp[['Survival_months', 'Status', f'log_{metric}']],
            duration_col='Survival_months', event_col='Status')

    hr   = np.exp(cph.params_[f'log_{metric}'])
    ci_l = np.exp(cph.confidence_intervals_.loc[f'log_{metric}', '95% lower-bound'])
    ci_u = np.exp(cph.confidence_intervals_.loc[f'log_{metric}', '95% upper-bound'])
    p    = cph.summary.loc[f'log_{metric}', 'p']

    cox_univar[metric] = {'hr': hr, 'ci_l': ci_l, 'ci_u': ci_u, 'p': p}
    sig = significance_label(p)
    print(f"\n  {mlabel} (log-transformed):")
    print(f"    HR = {hr:.2f} (95% CI {ci_l:.2f}–{ci_u:.2f}), {fmt_p(p)} [{sig}]")


# ─── E. MULTIVARIABLE COX MODELS ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("E. MULTIVARIABLE COX REGRESSION MODELS")
print("=" * 70)

# Prepare multivariable dataset
mv_cols = ['Survival_months', 'Status', 'Stage_group', 'STAS', 'pN',
           'lymp_mean', 'tumor_mean']
mv = surv[mv_cols].dropna().copy()
mv['log_lymp']  = np.log1p(mv['lymp_mean'])
mv['log_tumor'] = np.log1p(mv['tumor_mean'])
print(f"\nMultivariable dataset: n={len(mv)}, events={mv['Status'].sum()}")

# Model 1: Base (Stage + STAS + pN)
print("\n--- Model 1: Base (Stage_group + STAS + pN) ---")
m1_cols = ['Survival_months', 'Status', 'Stage_group', 'STAS', 'pN']
m1_data = mv[m1_cols].copy()
cph1 = CoxPHFitter()
cph1.fit(m1_data, duration_col='Survival_months', event_col='Status')
print(cph1.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].to_string())
c1 = cph1.concordance_index_
print(f"C-statistic (Model 1): {c1:.3f}")

m1_results = {}
for var in ['Stage_group', 'STAS', 'pN']:
    row = cph1.summary.loc[var]
    m1_results[var] = {
        'hr': row['exp(coef)'],
        'ci_l': row['exp(coef) lower 95%'],
        'ci_u': row['exp(coef) upper 95%'],
        'p': row['p']
    }

# Model 2: Extended (Base + lymp + tumor)
print("\n--- Model 2: Extended (Base + log_lymp + log_tumor) ---")
m2_cols = ['Survival_months', 'Status', 'Stage_group', 'STAS', 'pN', 'log_lymp', 'log_tumor']
m2_data = mv[m2_cols].copy()
cph2 = CoxPHFitter()
cph2.fit(m2_data, duration_col='Survival_months', event_col='Status')
print(cph2.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].to_string())
c2 = cph2.concordance_index_
print(f"C-statistic (Model 2): {c2:.3f}")

m2_results = {}
for var in ['Stage_group', 'STAS', 'pN', 'log_lymp', 'log_tumor']:
    row = cph2.summary.loc[var]
    m2_results[var] = {
        'hr': row['exp(coef)'],
        'ci_l': row['exp(coef) lower 95%'],
        'ci_u': row['exp(coef) upper 95%'],
        'p': row['p']
    }


# ─── SAVE STATISTICAL SUMMARY ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SAVING STATISTICAL SUMMARY")
print("=" * 70)

lines = []
lines.append("=" * 70)
lines.append("STATISTICAL SUMMARY — LUNG ADENOCARCINOMA DIGITAL PATHOLOGY THESIS")
lines.append("=" * 70)
lines.append(f"Analysis date: 2026-05-11")
lines.append(f"Merged cases (clinical + density): {len(complete)}")
lines.append(f"Deaths (events): {int(complete['Status'].sum())}")
lines.append("")

# A
lines.append("─" * 70)
lines.append("A. DESCRIPTIVE STATISTICS")
lines.append("─" * 70)
for col, label in [('lymp_mean','Lymphocyte density (cells/mm²)'),
                    ('tumor_mean','Tumour cell density (cells/mm²)'),
                    ('ratio_mean','Tumour:lymphocyte ratio')]:
    d = desc_results[col]
    lines.append(f"{label} (n={d['n']}):")
    lines.append(f"  Mean ± SD:    {d['mean']:.2f} ± {d['sd']:.2f}")
    lines.append(f"  Median (IQR): {d['median']:.2f} ({d['q1']:.2f}–{d['q3']:.2f})")
    lines.append(f"  Range:        {d['min']:.2f}–{d['max']:.2f}")
    lines.append("")

# B
lines.append("─" * 70)
lines.append("B. INTRA-TUMORAL VARIABILITY (Pearson r, ROI 1 vs ROI 2)")
lines.append("─" * 70)
for metric, label in [('lymp','Lymphocyte density'), ('tumor','Tumour cell density')]:
    d = ivar_results[metric]
    lines.append(f"{label}: r={d['r']:.3f}, {fmt_p(d['p'])}, CV={d['cv']:.1f}%, n={d['n']} pairs")
lines.append("")

# C
lines.append("─" * 70)
lines.append("C. ASSOCIATIONS WITH CLINICOPATHOLOGIC FEATURES (Mann-Whitney U)")
lines.append("─" * 70)
for col, label, val0, val1, name0, name1 in comparisons:
    lines.append(f"\n{label}:")
    for metric, mlabel in [('lymp_mean','Lymphocyte density'),
                             ('tumor_mean','Tumour cell density'),
                             ('ratio_mean','Tumour:lymphocyte ratio')]:
        key = f"{label}_{metric}"
        d = assoc_results[key]
        lines.append(f"  {mlabel}:")
        lines.append(f"    {name0} (n={d['group0_n']}): {d['group0_median']:.1f} ({d['group0_q1']:.1f}–{d['group0_q3']:.1f})")
        lines.append(f"    {name1} (n={d['group1_n']}): {d['group1_median']:.1f} ({d['group1_q1']:.1f}–{d['group1_q3']:.1f})")
        lines.append(f"    U={d['U']:.0f}, {fmt_p(d['p'])}")
lines.append("")

# D
lines.append("─" * 70)
lines.append("D. SURVIVAL ANALYSIS")
lines.append("─" * 70)
lines.append(f"Survival dataset: n={len(surv)}, events={int(surv['Status'].sum())}")
lines.append("\nKaplan-Meier (log-rank):")
for metric, mlabel in [('lymp_mean','Lymphocyte density'),
                         ('tumor_mean','Tumour cell density'),
                         ('ratio_mean','Tumour:lymphocyte ratio')]:
    d = km_results[metric]
    lines.append(f"  {mlabel} (split at {d['threshold']:.1f}):")
    lines.append(f"    Low (n={d['n_low']}, events={d['events_low']}): median OS={d['med_low']:.1f} months")
    lines.append(f"    High (n={d['n_high']}, events={d['events_high']}): median OS={d['med_high']:.1f} months")
    lines.append(f"    Log-rank {fmt_p(d['logrank_p'])}")
lines.append("\nUnivariate Cox (log-transformed continuous):")
for metric, mlabel in [('lymp_mean','Lymphocyte density'),
                         ('tumor_mean','Tumour cell density'),
                         ('ratio_mean','Tumour:lymphocyte ratio')]:
    d = cox_univar[metric]
    lines.append(f"  {mlabel}: HR={d['hr']:.2f} (95% CI {d['ci_l']:.2f}–{d['ci_u']:.2f}), {fmt_p(d['p'])}")
lines.append("")

# E
lines.append("─" * 70)
lines.append("E. MULTIVARIABLE COX MODELS")
lines.append("─" * 70)
lines.append(f"Dataset: n={len(mv)}, events={int(mv['Status'].sum())}")
lines.append(f"\nModel 1 (Stage_group + STAS + pN), C-index={c1:.3f}:")
for var in ['Stage_group', 'STAS', 'pN']:
    d = m1_results[var]
    lines.append(f"  {var}: HR={d['hr']:.2f} (95% CI {d['ci_l']:.2f}–{d['ci_u']:.2f}), {fmt_p(d['p'])}")
lines.append(f"\nModel 2 (+ log_lymp + log_tumor), C-index={c2:.3f}:")
for var in ['Stage_group', 'STAS', 'pN', 'log_lymp', 'log_tumor']:
    d = m2_results[var]
    lines.append(f"  {var}: HR={d['hr']:.2f} (95% CI {d['ci_l']:.2f}–{d['ci_u']:.2f}), {fmt_p(d['p'])}")
lines.append(f"\nC-index improvement: {c2-c1:.3f} ({c1:.3f} → {c2:.3f})")

with open('statistical_summary.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print("Saved statistical_summary.txt")

# Store all results in a dict for the docx update
import json
results_dict = {
    'n_complete': len(complete),
    'n_events': int(complete['Status'].sum()),
    'desc': desc_results,
    'ivar': ivar_results,
    'assoc': assoc_results,
    'km': km_results,
    'cox_univar': cox_univar,
    'm1': {'results': m1_results, 'c_index': c1},
    'm2': {'results': m2_results, 'c_index': c2},
    'comparisons': [(col, label, val0, val1, name0, name1)
                    for col, label, val0, val1, name0, name1 in comparisons],
    'n_surv': len(surv),
    'n_mv': len(mv),
    'n_mv_events': int(mv['Status'].sum()),
}

# Convert numpy types for JSON serialisation
def convert(obj):
    if isinstance(obj, (np.integer,)): return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, dict): return {k: convert(v) for k, v in obj.items()}
    if isinstance(obj, list): return [convert(i) for i in obj]
    if isinstance(obj, tuple): return [convert(i) for i in obj]
    return obj

with open('results_cache.json', 'w') as f:
    json.dump(convert(results_dict), f, indent=2)
print("Saved results_cache.json")
print("\nAnalysis complete.")
