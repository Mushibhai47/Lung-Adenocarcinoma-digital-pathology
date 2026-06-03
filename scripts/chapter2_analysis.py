"""
chapter2_analysis.py
Runs the full Chapter 2 statistical analysis from the SPSS ground-truth data.
Outputs chapter2_results.txt with all numbers needed to update the thesis.
"""
import sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pyreadstat
import pandas as pd
import numpy as np
from scipy import stats
from lifelines import KaplanMeierFitter, CoxPHFitter

# ── Load SPSS ──────────────────────────────────────────────────────────────
df_raw, meta = pyreadstat.read_sav(r'C:\Users\musha\Desktop\QuPath\Lung_june2025.sav')
vl = meta.variable_value_labels

df = df_raw.copy()

# ── Survival time ───────────────────────────────────────────────────────────
df['Surgery_date'] = pd.to_datetime(df['Surgery_date'])
df['dateofdeathorlastcontact'] = pd.to_datetime(df['dateofdeathorlastcontact'])
df['surv_months'] = (df['dateofdeathorlastcontact'] - df['Surgery_date']).dt.days / 30.44
df['event'] = df['Status'].astype(int)   # 1=dead, 0=alive/censored

# Remove zero/negative survival (data errors)
df = df[df['surv_months'] > 0].copy()
N = len(df)
n_events = df['event'].sum()

# ── Manual log-rank (corrected, avoids lifelines tied-time bug) ─────────────
def logrank(t1, e1, t2, e2):
    """Returns chi2, p-value."""
    times = np.sort(np.unique(np.concatenate([t1[e1==1], t2[e2==1]])))
    O, E = 0.0, 0.0
    V = 0.0
    for t in times:
        n1 = (t1 >= t).sum(); n2 = (t2 >= t).sum(); n = n1 + n2
        d1 = ((t1 == t) & (e1 == 1)).sum()
        d2 = ((t2 == t) & (e2 == 1)).sum()
        d = d1 + d2
        if n < 2 or d == 0: continue
        e_exp = d * n1 / n
        O += d1; E += e_exp
        V += d * n1 * n2 * (n - d) / (n**2 * (n - 1)) if n > 1 else 0
    if V == 0: return 0.0, 1.0
    chi2 = (O - E)**2 / V
    p = 1 - stats.chi2.cdf(chi2, df=1)
    return chi2, p

def km_stats(df_sub, group_col, group0_val, group1_val, label0, label1):
    """Run KM + logrank for a binary grouping."""
    g0 = df_sub[df_sub[group_col] == group0_val]
    g1 = df_sub[df_sub[group_col] == group1_val]
    kmf0 = KaplanMeierFitter(); kmf0.fit(g0['surv_months'], g0['event'])
    kmf1 = KaplanMeierFitter(); kmf1.fit(g1['surv_months'], g1['event'])
    chi2, p = logrank(
        g0['surv_months'].values, g0['event'].values,
        g1['surv_months'].values, g1['event'].values
    )
    # 5-year OS
    def fiveyear(kmf):
        t60 = kmf.survival_function_[kmf.survival_function_.index <= 60]
        return t60.iloc[-1, 0] * 100 if len(t60) > 0 else float('nan')
    s0 = fiveyear(kmf0); s1 = fiveyear(kmf1)
    med0 = kmf0.median_survival_time_
    med1 = kmf1.median_survival_time_
    return {
        'n0': len(g0), 'events0': g0['event'].sum(),
        'n1': len(g1), 'events1': g1['event'].sum(),
        'label0': label0, 'label1': label1,
        '5yr_os_0': s0, '5yr_os_1': s1,
        'median_os_0': med0, 'median_os_1': med1,
        'chi2': chi2, 'p': p
    }

def fmt_p(p):
    if p < 0.001: return "p < 0.001"
    if p < 0.01:  return f"p = {p:.3f}"
    return f"p = {p:.3f}"

def fmt_med(m):
    if pd.isna(m) or np.isinf(m): return "not reached"
    return f"{m:.1f} months"

lines = []
def pr(s=""): lines.append(s); print(s)

pr("=" * 70)
pr("CHAPTER 2 STATISTICAL ANALYSIS -- ACTUAL DATA FROM SPSS")
pr(f"Analysis date: 2026-05-28")
pr(f"Total cohort: n = {N}")
pr(f"Death events: {n_events}  |  Alive/censored: {N - n_events}")
pr("=" * 70)

# ─── A. COHORT CHARACTERISTICS ────────────────────────────────────────────
pr()
pr("-" * 70)
pr("A. COHORT CHARACTERISTICS")
pr("-" * 70)

age = df['Patient_age']
pr(f"Age: mean {age.mean():.1f} years (SD {age.std():.1f}; range {int(age.min())}–{int(age.max())})")

sex = df['Patient_sex'].map(vl['Patient_sex'])
pr(f"Sex: Female {(sex=='F').sum()} ({100*(sex=='F').mean():.1f}%), Male {(sex=='M').sum()} ({100*(sex=='M').mean():.1f}%)")

surv = df['surv_months']
pr(f"Follow-up: median {surv.median():.1f} months (IQR {surv.quantile(0.25):.1f}–{surv.quantile(0.75):.1f}; range {surv.min():.1f}–{surv.max():.1f})")

pr()
pr("STAGING (actual from SPSS):")
stg = df['Stage_group'].map(vl['Stage_group'])
stg_I   = (df['Stage_group'] <= 4).sum()
stg_II  = ((df['Stage_group'] >= 5) & (df['Stage_group'] <= 6)).sum()
stg_III = (df['Stage_group'] >= 7).sum()
pr(f"  Stage I  (IA1+IA2+IA3+IB): {stg_I} ({100*stg_I/N:.1f}%)")
pr(f"    IA1: {(df['Stage_group']==1).sum()}, IA2: {(df['Stage_group']==2).sum()}, "
   f"IA3: {(df['Stage_group']==3).sum()}, IB: {(df['Stage_group']==4).sum()}")
pr(f"  Stage II (IIA+IIB):         {stg_II} ({100*stg_II/N:.1f}%)")
pr(f"    IIA: {(df['Stage_group']==5).sum()}, IIB: {(df['Stage_group']==6).sum()}")
pr(f"  Stage III(IIIA+IIIB):       {stg_III} ({100*stg_III/N:.1f}%)")
pr(f"    IIIA: {(df['Stage_group']==7).sum()}, IIIB: {(df['Stage_group']==8).sum()}")

pr()
pr("NODAL STATUS:")
pN = df['pN'].map(vl['pN'])
pr(f"  N0: {(pN=='N0').sum()} ({100*(pN=='N0').mean():.1f}%)")
pr(f"  N1: {(pN=='N1').sum()} ({100*(pN=='N1').mean():.1f}%)")
pr(f"  N2: {(pN=='N2').sum()} ({100*(pN=='N2').mean():.1f}%)")
pr(f"  N+ (N1+N2): {(df['pN']>0).sum()} ({100*(df['pN']>0).mean():.1f}%)")

pr()
pr("HISTOLOGIC FEATURES:")
stas = df['STAS'].map(vl['STAS'])
pr(f"  STAS positive: {(stas=='Yes').sum()} ({100*(stas=='Yes').mean():.1f}%)")
pr(f"  STAS unknown:  {(stas=='unknown').sum()}")
lvi = df['Lymphovascular_Invasion'].map(vl['Lymphovascular_Invasion'])
pr(f"  LVI positive:  {(lvi=='Yes').sum()} ({100*(lvi=='Yes').mean():.1f}%)")
vpi = df['Visceral_Pleural_Invasion'].map(vl['Visceral_Pleural_Invasion'])
pr(f"  VPI positive:  {(vpi=='yes').sum()} ({100*(vpi=='yes').mean():.1f}%)")
pr(f"  Margins positive: {(df['Margins']==1).sum()} ({100*(df['Margins']==1).mean():.1f}%)")

pr()
pr("HISTOLOGIC GROWTH PATTERN (predominant):")
patt = df['Tumor_predominant_pattern'].map(vl['Tumor_predominant_pattern'])
patt_counts = patt[patt != 'NA'].value_counts()
patt_n = patt[patt != 'NA'].shape[0]
for name, cnt in patt_counts.items():
    pr(f"  {name}: {cnt} ({100*cnt/N:.1f}%)")
pr(f"  Not assessable/NA: {(patt=='NA').sum()}")

pr()
pr("PATHOLOGICAL DIAGNOSIS:")
diag = df['Pathological_diagnosis'].map(vl['Pathological_diagnosis'])
for name, cnt in diag.value_counts().items():
    pr(f"  {name}: {cnt} ({100*cnt/N:.1f}%)")

pr()
pr("MOLECULAR RESULTS (n=173 total; 109 not tested):")
mol = df['Molecular_results'].map(vl['Molecular_results'])
mol_tested = df[df['Molecular_results'] > 0]
n_tested = len(mol_tested)
pr(f"  Not tested: {(df['Molecular_results']==0).sum()} ({100*(df['Molecular_results']==0).mean():.1f}%)")
pr(f"  Tested: {n_tested}")
for code, name in [(1,'no mutation'),(2,'EGFR exon 19 del'),(3,'EGFR other'),
                   (6,'EGFR L858R'),(7,'EGFR mut21'),(4,'ALK rearrangement'),
                   (9,'ALK fusion'),(5,'ROS1 rearrangement'),(10,'RET fusion'),
                   (8,'KRAS G12C')]:
    cnt = (df['Molecular_results']==code).sum()
    if cnt > 0:
        pr(f"    {name}: {cnt} ({100*cnt/n_tested:.1f}% of tested)")

# EGFR total
egfr_n = df['Molecular_results'].isin([2,3,6,7]).sum()
pr(f"  TOTAL EGFR mutations: {egfr_n} ({100*egfr_n/n_tested:.1f}% of tested; {100*egfr_n/N:.1f}% of all)")
kras_n = (df['Molecular_results']==8).sum()
pr(f"  NOTE: KRAS G12C only {kras_n} cases -- too few for survival analysis")

pr()
pr("PDL1 IHC (n=105 tested):")
pdl1 = df['PDL1_IHQ'].map(vl['PDL1_IHQ'])
pdl1_tested = df[df['PDL1_IHQ'] != 9]
pr(f"  PDL1 <1%%:     {(df['PDL1_IHQ']==0).sum()} ({100*(df['PDL1_IHQ']==0).sum()/len(pdl1_tested):.1f}% of tested)")
pr(f"  PDL1 >=1%%:    {(df['PDL1_IHQ']==1).sum()} ({100*(df['PDL1_IHQ']==1).sum()/len(pdl1_tested):.1f}% of tested)")
pr(f"  Not tested:   {(df['PDL1_IHQ']==9).sum()}")

pr()
pr("VIMENTIN IHC (n=140 tested):")
vim_tested = df[df['Vimentine_IHQ'] != 9]
pr(f"  Vimentin negative: {(df['Vimentine_IHQ']==0).sum()} ({100*(df['Vimentine_IHQ']==0).sum()/len(vim_tested):.1f}% of tested)")
pr(f"  Vimentin positive: {(df['Vimentine_IHQ']==1).sum()} ({100*(df['Vimentine_IHQ']==1).sum()/len(vim_tested):.1f}% of tested)")
pr(f"  Not tested:        {(df['Vimentine_IHQ']==9).sum()}")

# ─── B. SURVIVAL ANALYSIS ──────────────────────────────────────────────────
pr()
pr("-" * 70)
pr("B. KAPLAN-MEIER SURVIVAL ANALYSIS")
pr("-" * 70)
pr(f"(n={N}, {n_events} death events)")
pr()

def print_km(label, res):
    pr(f"{label}:")
    pr(f"  {res['label0']} (n={res['n0']}, events={res['events0']}): "
       f"5-yr OS = {res['5yr_os_0']:.1f}%, median OS = {fmt_med(res['median_os_0'])}")
    pr(f"  {res['label1']} (n={res['n1']}, events={res['events1']}): "
       f"5-yr OS = {res['5yr_os_1']:.1f}%, median OS = {fmt_med(res['median_os_1'])}")
    sig = "SIGNIFICANT" if res['p'] < 0.05 else "not significant"
    pr(f"  Log-rank chi2 = {res['chi2']:.3f}, {fmt_p(res['p'])} [{sig}]")
    pr()

# STAS (exclude unknown)
df_stas = df[df['STAS'].isin([0,1])].copy()
pr(f"STAS analysis: n={len(df_stas)} (1 unknown excluded)")
res = km_stats(df_stas, 'STAS', 0, 1, 'STAS-negative', 'STAS-positive')
print_km("STAS", res)
stas_res = res

# LVI
res = km_stats(df, 'Lymphovascular_Invasion', 0, 1, 'LVI-negative', 'LVI-positive')
print_km("Lymphovascular invasion (LVI)", res)
lvi_res = res

# VPI
res = km_stats(df, 'Visceral_Pleural_Invasion', 0, 1, 'VPI-negative', 'VPI-positive')
print_km("Visceral pleural invasion (VPI)", res)
vpi_res = res

# pN (N0 vs N+)
df_pn = df.copy(); df_pn['Nplus'] = (df_pn['pN'] > 0).astype(int)
res = km_stats(df_pn, 'Nplus', 0, 1, 'N0', 'N+ (N1 or N2)')
print_km("Nodal status (pN)", res)
pn_res = res

# Stage group (I vs II/III)
df_stg = df.copy()
df_stg['stg_bin'] = (df_stg['Stage_group'] >= 5).astype(int)
res = km_stats(df_stg, 'stg_bin', 0, 1, 'Stage I', 'Stage II/III')
print_km("Pathologic stage (I vs II/III)", res)
stg_res = res

# Sex
res = km_stats(df, 'Patient_sex', 0, 1, 'Male', 'Female')
print_km("Sex (M vs F)", res)
sex_res = res

# PDL1 (only tested cases, exclude 9)
df_pdl1 = df[df['PDL1_IHQ'].isin([0,1])].copy()
pr(f"PDL1 analysis: n={len(df_pdl1)} tested cases")
res = km_stats(df_pdl1, 'PDL1_IHQ', 0, 1, 'PDL1 <1%', 'PDL1 >=1%')
print_km("PD-L1 expression (IHC)", res)
pdl1_res = res

# Vimentin (only tested cases, exclude 9)
df_vim = df[df['Vimentine_IHQ'].isin([0,1])].copy()
pr(f"Vimentin analysis: n={len(df_vim)} tested cases")
res = km_stats(df_vim, 'Vimentine_IHQ', 0, 1, 'Vimentin-negative', 'Vimentin-positive')
print_km("Vimentin IHC", res)
vim_res = res

# Solid pattern (solid vs non-solid, among those with known pattern)
df_patt2 = df[df['Tumor_predominant_pattern'].isin([1,2,3,4,5])].copy()
df_patt2['solid_bin'] = (df_patt2['Tumor_predominant_pattern'] == 1).astype(int)
pr(f"Solid pattern analysis: n={len(df_patt2)} (NA excluded)")
res = km_stats(df_patt2, 'solid_bin', 0, 1, 'Non-solid predominant', 'Solid predominant')
print_km("Predominant solid pattern", res)
solid_res = res

# EGFR (among tested only)
df_egfr = mol_tested.copy()
df_egfr['egfr'] = df_egfr['Molecular_results'].isin([2,3,6,7]).astype(int)
pr(f"EGFR analysis: n={len(df_egfr)} tested cases")
res = km_stats(df_egfr, 'egfr', 0, 1, 'EGFR wild-type', 'EGFR-mutant')
print_km("EGFR mutation (among tested)", res)
egfr_res = res

# ─── C. UNIVARIATE COX ────────────────────────────────────────────────────
pr("-" * 70)
pr("C. UNIVARIATE COX REGRESSION")
pr("-" * 70)
pr()

univar_results = {}
cox_df = df.copy()
cox_df['Nplus'] = (cox_df['pN'] > 0).astype(int)
cox_df['stg_bin'] = (cox_df['Stage_group'] >= 5).astype(int)
cox_df = cox_df[cox_df['STAS'].isin([0,1])].copy()

for varname, col, label in [
    ('STAS', 'STAS', 'STAS (0=No, 1=Yes)'),
    ('LVI', 'Lymphovascular_Invasion', 'LVI (0=No, 1=Yes)'),
    ('VPI', 'Visceral_Pleural_Invasion', 'VPI (0=No, 1=Yes)'),
    ('pN+', 'Nplus', 'pN+ (0=N0, 1=N+)'),
    ('Stage_II/III', 'stg_bin', 'Stage II/III (0=I, 1=II/III)'),
    ('Sex_F', 'Patient_sex', 'Sex (0=M, 1=F)'),
]:
    try:
        cph = CoxPHFitter()
        tmp = cox_df[['surv_months','event',col]].dropna()
        cph.fit(tmp, duration_col='surv_months', event_col='event', formula=col)
        hr = np.exp(cph.params_[col])
        ci_lo = np.exp(cph.confidence_intervals_.iloc[0,0])
        ci_hi = np.exp(cph.confidence_intervals_.iloc[0,1])
        p = cph.summary['p'].values[0]
        sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else ""
        pr(f"  {label}:")
        pr(f"    HR = {hr:.2f} (95%% CI {ci_lo:.2f}–{ci_hi:.2f}), {fmt_p(p)} {sig}")
        univar_results[varname] = {'hr': hr, 'ci_lo': ci_lo, 'ci_hi': ci_hi, 'p': p}
    except Exception as e:
        pr(f"  {label}: ERROR {e}")
pr()

# PDL1 univariate Cox
try:
    df_pdl1_cox = df_pdl1[['surv_months','event','PDL1_IHQ']].dropna()
    cph = CoxPHFitter()
    cph.fit(df_pdl1_cox, duration_col='surv_months', event_col='event', formula='PDL1_IHQ')
    hr = np.exp(cph.params_['PDL1_IHQ'])
    ci_lo = np.exp(cph.confidence_intervals_.iloc[0,0])
    ci_hi = np.exp(cph.confidence_intervals_.iloc[0,1])
    p = cph.summary['p'].values[0]
    sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else ""
    pr(f"  PD-L1 >=1%% (n={len(df_pdl1_cox)}):")
    pr(f"    HR = {hr:.2f} (95%% CI {ci_lo:.2f}–{ci_hi:.2f}), {fmt_p(p)} {sig}")
    univar_results['PDL1'] = {'hr': hr, 'ci_lo': ci_lo, 'ci_hi': ci_hi, 'p': p}
except Exception as e:
    pr(f"  PDL1: ERROR {e}")

# Vimentin univariate Cox
try:
    df_vim_cox = df_vim[['surv_months','event','Vimentine_IHQ']].dropna()
    cph = CoxPHFitter()
    cph.fit(df_vim_cox, duration_col='surv_months', event_col='event', formula='Vimentine_IHQ')
    hr = np.exp(cph.params_['Vimentine_IHQ'])
    ci_lo = np.exp(cph.confidence_intervals_.iloc[0,0])
    ci_hi = np.exp(cph.confidence_intervals_.iloc[0,1])
    p = cph.summary['p'].values[0]
    sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else ""
    pr(f"  Vimentin positive (n={len(df_vim_cox)}):")
    pr(f"    HR = {hr:.2f} (95%% CI {ci_lo:.2f}–{ci_hi:.2f}), {fmt_p(p)} {sig}")
    univar_results['Vimentin'] = {'hr': hr, 'ci_lo': ci_lo, 'ci_hi': ci_hi, 'p': p}
except Exception as e:
    pr(f"  Vimentin: ERROR {e}")

# ─── D. MULTIVARIABLE COX ─────────────────────────────────────────────────
pr()
pr("-" * 70)
pr("D. MULTIVARIABLE COX REGRESSION")
pr("-" * 70)
pr()

# Select variables with p < 0.10 in univariate
eligible = [var for var, r in univar_results.items() if r['p'] < 0.10]
pr(f"Variables eligible (p < 0.10 univariate): {eligible}")
pr()

# Model 1: conventional factors (STAS, LVI, VPI, pN, Stage)
model1_vars = ['STAS', 'Lymphovascular_Invasion', 'Visceral_Pleural_Invasion', 'Nplus', 'stg_bin']
cox_mv = cox_df[['surv_months','event'] + model1_vars].dropna()
pr(f"Model 1 (STAS + LVI + VPI + pN+ + Stage): n={len(cox_mv)}, events={cox_mv['event'].sum()}")
try:
    cph1 = CoxPHFitter()
    cph1.fit(cox_mv, duration_col='surv_months', event_col='event')
    pr(f"  C-index: {cph1.concordance_index_:.3f}")
    for var in model1_vars:
        hr = np.exp(cph1.params_[var])
        ci_lo = np.exp(cph1.confidence_intervals_.loc[var].iloc[0])
        ci_hi = np.exp(cph1.confidence_intervals_.loc[var].iloc[1])
        p = cph1.summary['p'].loc[var]
        sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else ""
        names = {'STAS':'STAS','Lymphovascular_Invasion':'LVI','Visceral_Pleural_Invasion':'VPI',
                 'Nplus':'pN+','stg_bin':'Stage II/III'}
        pr(f"  {names.get(var,var)}: HR={hr:.2f} (95%% CI {ci_lo:.2f}–{ci_hi:.2f}), {fmt_p(p)} {sig}")
except Exception as e:
    pr(f"  ERROR: {e}")

pr()

# Model 2: add PDL1 (among tested cases only -- n reduced)
df_pdl1_mv = df[df['PDL1_IHQ'].isin([0,1]) & df['STAS'].isin([0,1])].copy()
df_pdl1_mv['Nplus'] = (df_pdl1_mv['pN'] > 0).astype(int)
df_pdl1_mv['stg_bin'] = (df_pdl1_mv['Stage_group'] >= 5).astype(int)
model2_vars = ['STAS','Lymphovascular_Invasion','Visceral_Pleural_Invasion','Nplus','stg_bin','PDL1_IHQ']
cox_mv2 = df_pdl1_mv[['surv_months','event'] + model2_vars].dropna()
pr(f"Model 2 (+ PDL1, among tested n={len(cox_mv2)}, events={cox_mv2['event'].sum()}):")
try:
    cph2 = CoxPHFitter()
    cph2.fit(cox_mv2, duration_col='surv_months', event_col='event')
    pr(f"  C-index: {cph2.concordance_index_:.3f}")
    for var in model2_vars:
        hr = np.exp(cph2.params_[var])
        ci_lo = np.exp(cph2.confidence_intervals_.loc[var].iloc[0])
        ci_hi = np.exp(cph2.confidence_intervals_.loc[var].iloc[1])
        p = cph2.summary['p'].loc[var]
        sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else ""
        names = {'STAS':'STAS','Lymphovascular_Invasion':'LVI','Visceral_Pleural_Invasion':'VPI',
                 'Nplus':'pN+','stg_bin':'Stage II/III','PDL1_IHQ':'PDL1 >=1%'}
        pr(f"  {names.get(var,var)}: HR={hr:.2f} (95%% CI {ci_lo:.2f}–{ci_hi:.2f}), {fmt_p(p)} {sig}")
except Exception as e:
    pr(f"  ERROR: {e}")

pr()
pr("=" * 70)
pr("KEY FINDINGS SUMMARY FOR CHAPTER 2")
pr("=" * 70)
pr(f"1. Cohort: n={N}, {n_events} deaths, median follow-up {surv.median():.1f} months")
pr(f"   Sex: {(sex=='F').sum()} female ({100*(sex=='F').mean():.1f}%), mean age {age.mean():.1f} years")
pr(f"2. Stage: I={stg_I} ({100*stg_I/N:.1f}%), II={stg_II} ({100*stg_II/N:.1f}%), III={stg_III} ({100*stg_III/N:.1f}%)")
pr(f"3. STAS={stas_res['n1']} cases ({100*stas_res['n1']/(stas_res['n0']+stas_res['n1']):.1f}%), "
   f"5-yr OS: {stas_res['5yr_os_0']:.1f}% vs {stas_res['5yr_os_1']:.1f}%, log-rank {fmt_p(stas_res['p'])}")
pr(f"4. LVI={lvi_res['n1']} cases ({100*lvi_res['n1']/N:.1f}%), "
   f"5-yr OS: {lvi_res['5yr_os_0']:.1f}% vs {lvi_res['5yr_os_1']:.1f}%, log-rank {fmt_p(lvi_res['p'])}")
pr(f"5. VPI={vpi_res['n1']} cases ({100*vpi_res['n1']/N:.1f}%), "
   f"5-yr OS: {vpi_res['5yr_os_0']:.1f}% vs {vpi_res['5yr_os_1']:.1f}%, log-rank {fmt_p(vpi_res['p'])}")
pr(f"6. N+={pn_res['n1']} cases ({100*pn_res['n1']/N:.1f}%), "
   f"5-yr OS: {pn_res['5yr_os_0']:.1f}% vs {pn_res['5yr_os_1']:.1f}%, log-rank {fmt_p(pn_res['p'])}")
pr(f"7. Stage II/III={stg_res['n1']} cases, "
   f"5-yr OS Stage I: {stg_res['5yr_os_0']:.1f}% vs Stage II/III: {stg_res['5yr_os_1']:.1f}%, log-rank {fmt_p(stg_res['p'])}")
pr(f"8. PDL1 (n={pdl1_res['n0']+pdl1_res['n1']} tested): PDL1<1%%: {pdl1_res['5yr_os_0']:.1f}% vs PDL1>=1%%: {pdl1_res['5yr_os_1']:.1f}%, log-rank {fmt_p(pdl1_res['p'])}")
pr(f"9. Vimentin (n={vim_res['n0']+vim_res['n1']} tested): neg: {vim_res['5yr_os_0']:.1f}% vs pos: {vim_res['5yr_os_1']:.1f}%, log-rank {fmt_p(vim_res['p'])}")
pr(f"10. EGFR (n={egfr_res['n0']+egfr_res['n1']} tested): WT: {egfr_res['5yr_os_0']:.1f}% vs mutant: {egfr_res['5yr_os_1']:.1f}%, log-rank {fmt_p(egfr_res['p'])}")
pr(f"11. Solid pattern (n={solid_res['n0']+solid_res['n1']}): non-solid: {solid_res['5yr_os_0']:.1f}% vs solid: {solid_res['5yr_os_1']:.1f}%, log-rank {fmt_p(solid_res['p'])}")

out_path = r'C:\Users\musha\Desktop\QuPath\chapter2_results.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"\nSaved to {out_path}")
