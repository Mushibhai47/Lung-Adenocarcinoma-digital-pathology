"""
merge_results.py
=================
1. Cleans lymphocyte_results.csv and tumor_cell_results.csv
   (removes duplicate rows from multiple script runs — keeps last run per slide+region)
2. Calculates per-region and per-case summary statistics
3. Reads Lung_june2025.xlsx and adds new columns:
   - Lymphocyte density per region (region 1 & 2)
   - Mean lymphocyte density (across all regions)
   - Tumor cell density per region (region 1 & 2)
   - Mean tumor cell density
   - Tumor/Lymphocyte ratio
4. Saves updated Excel as Results_Final.xlsx
5. Prints basic statistics
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

BASE = Path(r"C:\Users\musha\Desktop\QuPath")

# ============================================================
# STEP 1: Load and clean CSVs
# ============================================================

def clean_csv(filepath, value_col):
    """Load CSV, remove duplicate runs (keep last per image+region), return clean df."""
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()

    # Extract slide ID (e.g. R1-S16 from the filename)
    df['slide_id'] = df['Image'].str.extract(r'(R\d+-S\d+)')

    # Keep only last occurrence of each slide+region (last run = most recent parameters)
    df = df.drop_duplicates(subset=['slide_id', 'Region_Index'], keep='last')
    df = df.reset_index(drop=True)

    print(f"\n{filepath.name}: {len(df)} rows after deduplication ({df['slide_id'].nunique()} slides)")
    return df

lymp_df  = clean_csv(BASE / "lymphocyte_results.csv",   "Lymphocyte_Density_per_mm2")
tumor_df = clean_csv(BASE / "tumor_cell_results.csv",   "Tumor_Cell_Density_per_mm2")

# ============================================================
# STEP 2: Per-case summary (mean across regions)
# ============================================================

def summarize_per_case(df, density_col, prefix):
    """Pivot regions wide, add mean column."""
    pivot = df.pivot_table(
        index='slide_id',
        columns='Region_Index',
        values=density_col,
        aggfunc='first'
    ).reset_index()
    pivot.columns = [f'{prefix}_Region{int(c)}' if isinstance(c, (int, float)) else c
                     for c in pivot.columns]
    region_cols = [c for c in pivot.columns if c.startswith(prefix + '_Region')]
    pivot[f'{prefix}_Mean'] = pivot[region_cols].mean(axis=1)
    return pivot

lymp_summary  = summarize_per_case(lymp_df,  'Lymphocyte_Density_per_mm2',  'LymphDensity')
tumor_summary = summarize_per_case(tumor_df, 'Tumor_Cell_Density_per_mm2', 'TumorDensity')

# Merge lymphocyte and tumor summaries
summary = lymp_summary.merge(tumor_summary, on='slide_id', how='outer')

# Tumor / Lymphocyte ratio
summary['Tumor_Lymph_Ratio'] = np.where(
    summary['LymphDensity_Mean'] > 0,
    summary['TumorDensity_Mean'] / summary['LymphDensity_Mean'],
    np.nan
)

print(f"\n=== PER-CASE SUMMARY ({len(summary)} slides) ===")
print(summary[['slide_id','LymphDensity_Mean','TumorDensity_Mean','Tumor_Lymph_Ratio']].to_string(index=False))

# ============================================================
# STEP 3: Load Excel and merge
# ============================================================

excel_path = BASE / "Lung_june2025.xlsx"
print(f"\nReading {excel_path.name}...")

xl = pd.ExcelFile(excel_path)
print(f"Sheets: {xl.sheet_names}")

# Read first sheet
clinical_df = xl.parse(xl.sheet_names[0])
print(f"Clinical data: {len(clinical_df)} rows, {len(clinical_df.columns)} columns")
print(f"Columns: {list(clinical_df.columns)}")
print(clinical_df.head(3).to_string())

# ============================================================
# STEP 4: Match slide IDs to clinical cases
# ============================================================
# The slide_id format is R1-S16, R2-S3 etc.
# Try to find a matching column in the Excel

# Print unique slide IDs from CSVs for reference
print(f"\nUnique slide IDs in QuPath data:\n{sorted(summary['slide_id'].tolist())}")

# Try to find a slide/sample ID column in clinical data
id_cols = [c for c in clinical_df.columns if any(k in str(c).lower()
           for k in ['slide', 'sample', 'id', 'case', 'num', 'rack', 'slot'])]
print(f"\nPotential ID columns in Excel: {id_cols}")

# ============================================================
# STEP 5: Save clean summary CSV regardless of Excel match
# ============================================================

summary_out = BASE / "qupath_summary.csv"
summary.to_csv(summary_out, index=False)
print(f"\nSaved per-case summary to: {summary_out.name}")

# ============================================================
# STEP 6: Basic statistics
# ============================================================

print("\n=== DESCRIPTIVE STATISTICS ===")
stats_cols = [c for c in summary.columns if c != 'slide_id']
print(summary[stats_cols].describe().round(2).to_string())

# ============================================================
# STEP 7: Save outputs
# ============================================================

# Save clean CSVs
lymp_df.to_csv(BASE / "lymphocyte_results_clean.csv", index=False)
tumor_df.to_csv(BASE / "tumor_cell_results_clean.csv", index=False)
print(f"\nSaved clean CSVs: lymphocyte_results_clean.csv, tumor_cell_results_clean.csv")
print("\nDone. Now share the Excel column names so we can match slide IDs to cases.")
