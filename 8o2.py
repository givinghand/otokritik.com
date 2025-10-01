
###########################################################################
##########
###########################################################################
##########
###########################################################################
##########
###########################################################################
##########
###########################################################################





"""
group_models_with_years_fixed.py

- Reads INPUT_CSV (sep=';').
- Groups rows by a small set of stable keys (MARKA, MODEL, SERI, DONANIM PAKETI,
  MOTOR silindir adedi, MOTOR silindir hacmi, TEMEL OZELLIKLER - Yakit Tipi).
- Produces TEMEL OZELLIKLER - Model Yillari as sorted, comma-separated years (expands ranges).
- Keeps all original columns (drops original model-year column and inserts new one right after
  TEMEL OZELLIKLER - Donanim Paketi).
- Writes OUTPUT_CSV and prints original/grouped row counts.
"""
from pathlib import Path
import pandas as pd
import re


# ------------- config -------------
INPUT_CSV = "CAR_DATA_FINAL_2.csv"
OUTPUT_CSV = "CAR_DATA_FINAL.csv"
SEP = ";"
ENC = "utf-8-sig"

# The columns we actually want to group by (stable keys)
GROUP_KEYS_WANTED = [
    "BASLIK",
]

NEW_MODEL_YEARS_COL = "TEMEL OZELLIKLER - Model Yillari"

OLD_MODEL_YEAR_CANDIDATES = [
    "TEMEL OZELLIKLER - Model Yili",
    "TEMEL OZELLIKLER - Model Yıl",
    "TEMEL OZELLIKLER - Model Yılı",
    "Model Yili",
    "Model Yılı",
    "ModelYili",
    "Model Yillari",
    "Model Yılları",
]

# ------------- helpers -------------
def find_column(columns, target):
    t = str(target).strip().lower()
    for c in columns:
        if str(c).strip().lower() == t:
            return c
    for c in columns:
        if t in str(c).lower():
            return c
    return None

def find_first_existing_column(columns, candidates):
    for cand in candidates:
        f = find_column(columns, cand)
        if f:
            return f
    # fallback: any column containing 'yil' or 'yıl'
    for c in columns:
        if "yil" in str(c).lower() or "yıl" in str(c).lower():
            return c
    return None

def expand_year_ranges(s):
    """Return list of years found in string s (supports ranges like 2018-2020)."""
    if pd.isna(s):
        return []
    text = str(s)
    text = re.sub(r"[–—−]", "-", text)
    years = []
    # ranges first
    for a, b in re.findall(r"\b(19\d{2}|20\d{2})\s*-\s*(19\d{2}|20\d{2})\b", text):
        a_i, b_i = int(a), int(b)
        if a_i <= b_i:
            rng = range(a_i, b_i + 1)
        else:
            rng = range(b_i, a_i + 1)
        for y in rng:
            if y not in years:
                years.append(y)
    # singles
    for y in re.findall(r"\b(19\d{2}|20\d{2})\b", text):
        yi = int(y)
        if yi not in years:
            years.append(yi)
    return years

def join_years_sorted(years):
    if not years:
        return ""
    ys = sorted(set(int(y) for y in years))
    return ", ".join(str(y) for y in ys)

def first_nonempty_in_series(seq):
    for v in seq:
        if pd.isna(v):
            continue
        s = str(v).strip()
        if s != "":
            return v
    return ""

def normalize_for_grouping(s):
    """Normalize a string for grouping: strip, lower, collapse spaces."""
    if pd.isna(s):
        return ""
    t = str(s).strip()
    t = re.sub(r"\s+", " ", t)
    return t.lower()

# ------------- main grouping logic -------------
def group_keep_all_columns(df):
    cols = list(df.columns)

    # resolve actual group key names from CSV columns
    actual_keys = []
    for wanted in GROUP_KEYS_WANTED:
        found = find_column(cols, wanted)
        actual_keys.append(found)

    missing_keys = [GROUP_KEYS_WANTED[i] for i,k in enumerate(actual_keys) if k is None]
    if missing_keys:
        raise KeyError(f"Missing grouping columns (check names): {missing_keys}\nAvailable columns: {cols}")

    # find existing model-year column to read from (if any)
    model_year_col = find_first_existing_column(cols, OLD_MODEL_YEAR_CANDIDATES)
    helper_col = "__MODEL_YEAR_HELPER__"
    df2 = df.copy()
    if model_year_col is not None:
        df2[model_year_col] = df2[model_year_col].fillna("").astype(str).str.strip()
    else:
        df2[helper_col] = ""
        model_year_col = helper_col

    # build a normalized copy to group on (doesn't overwrite original df2)
    df_norm = df2.copy()
    for k in actual_keys:
        df_norm[k] = df_norm[k].apply(normalize_for_grouping)

    # group on normalized columns (so small text differences won't break grouping)
    grouped = df_norm.groupby(actual_keys, sort=False)

    out_rows = []
    for norm_key_vals, grp_norm in grouped:
        # grp_norm.index gives indexes of original df2 rows that belong to this group
        grp_orig = df2.loc[grp_norm.index]

        # start building output row using original column order and values
        row = {}
        # set group key fields using first non-empty original values
        if isinstance(norm_key_vals, tuple):
            for col_name, _norm_val in zip(actual_keys, norm_key_vals):
                row[col_name] = first_nonempty_in_series(grp_orig[col_name].tolist())
        else:
            row[actual_keys[0]] = first_nonempty_in_series(grp_orig[actual_keys[0]].tolist())

        # for all other original columns keep first non-empty
        for c in cols:
            if c in row:
                continue
            row[c] = first_nonempty_in_series(grp_orig[c].tolist())

        # aggregate model years from the original model_year_col content
        all_years = []
        for raw in grp_orig[model_year_col].tolist():
            yrs = expand_year_ranges(raw)
            for y in yrs:
                if y not in all_years:
                    all_years.append(y)
        row[NEW_MODEL_YEARS_COL] = join_years_sorted(all_years)

        out_rows.append(row)

    # build resulting DataFrame preserving column order, remove old model-year column, insert new one
    result_cols = cols.copy()
    old_col_found = find_first_existing_column(cols, OLD_MODEL_YEAR_CANDIDATES)
    if old_col_found and old_col_found in result_cols:
        result_cols.remove(old_col_found)

    # insert new MODEL YILLARI column right after 'TEMEL OZELLIKLER - Donanim Paketi' if possible
    insert_after = find_column(result_cols, "TEMEL OZELLIKLER - Donanim Paketi")
    if insert_after and insert_after in result_cols:
        idx = result_cols.index(insert_after) + 1
        if NEW_MODEL_YEARS_COL not in result_cols:
            result_cols.insert(idx, NEW_MODEL_YEARS_COL)
    else:
        if NEW_MODEL_YEARS_COL not in result_cols:
            result_cols.append(NEW_MODEL_YEARS_COL)

    result = pd.DataFrame(out_rows, columns=result_cols)

    # drop helper col if created
    if helper_col in result.columns:
        result = result.drop(columns=[helper_col])

    return result

# ------------- CLI -------------
def main():
    p = Path(INPUT_CSV)
    if not p.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")
    df = pd.read_csv(p, sep=SEP, encoding=ENC, dtype=str)
    print(f"Original rows: {len(df)}")
    result = group_keep_all_columns(df)
    result.to_csv(OUTPUT_CSV, sep=SEP, index=False, encoding=ENC)
    print(f"Grouped rows: {len(result)}")
    print("Done")

if __name__ == "__main__":
    main()




###########################################################################
##########
###########################################################################
##########
###########################################################################
##########
###########################################################################
##########
###########################################################################



#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_model_years.py

- Reads CSV
- Expands "TEMEL OZELLIKLER - Model Yillari" so that if there are >= 3 years,
  missing years between min and max are filled in.
"""

import pandas as pd
from pathlib import Path

# ---------- CONFIG ----------
INPUT_CSV = "CAR_DATA_FINAL.csv"          # change if needed
OUTPUT_CSV = "CAR_DATA_FINAL.csv"
SEP = ";"
ENC = "utf-8-sig"
COLUMN_NAME = "TEMEL OZELLIKLER - Model Yillari"
# ----------------------------

def fix_years(cell):
    if not isinstance(cell, str) or cell.strip() == "":
        return cell
    try:
        years = sorted({int(y.strip()) for y in cell.split(",") if y.strip().isdigit()})
    except ValueError:
        return cell  # if something unexpected
    if len(years) < 3:
        return ", ".join(str(y) for y in years)
    # fill missing years between min and max
    full_range = list(range(min(years), max(years) + 1))
    return ", ".join(str(y) for y in full_range)

def main():
    p = Path(INPUT_CSV)
    if not p.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(p, sep=SEP, encoding=ENC, dtype=str, keep_default_na=False)

    if COLUMN_NAME not in df.columns:
        raise KeyError(f"Column '{COLUMN_NAME}' not found in CSV")

    before = df[COLUMN_NAME].copy()
    df[COLUMN_NAME] = df[COLUMN_NAME].apply(fix_years)

    changes = (before != df[COLUMN_NAME]).sum()
    print(f"Fixed {changes} rows in '{COLUMN_NAME}'")

    df.to_csv(OUTPUT_CSV, sep=SEP, encoding=ENC, index=False)
    print(f"Saved fixed CSV to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
