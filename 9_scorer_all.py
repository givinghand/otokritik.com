#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pure-formula scorer without dataset scaling.
- Uses fixed formulas to transform raw data into scores.
- The formulas are tuned to produce results generally in the 20-100 range.
- No min/max scaling; each row is calculated independently.
- All final scores are rounded to integers.
- Sub-scores: performans, Ic_Hacim, Konfor, Guvenlik, Eko, bakim.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re

# ----------------------------
# I/O
# ----------------------------
INPUT_CSV = "CAR_DATA_FINAL_3.csv"
OUTPUT_CSV = "CAR_DATA_FINAL_4_SC.csv"

# ----------------------------
# Calculation Parameters & Weights
# ----------------------------

# Weights are used conceptually to tune formula coefficients
SECURITY_WEIGHTS = {"airbag": 0.30, "ncap": 0.50, "weight": 0.10, "height": 0.10}
performans_WEIGHTS = {"hiz": 0.2, "tork": 0.2, "hp": 0.2, "accel": 0.2, "weight": 0.2}
IC_HACIM_WEIGHTS = {"genislik": 1/3, "uzunluk": 1/3, "yukseklik": 1/3}
KONFOR_WEIGHTS = {"ic": 0.25, "agirlik": 0.35, "taban": 0.075, "kesit": 0.075, "jant": 0.25}

# ----------------------------
# Helper Functions
# ----------------------------
def clean_numeric(x):
    if pd.isna(x): return np.nan
    s = str(x).strip()
    if s == "": return np.nan
    s = (s.replace("₺", "").replace("TL", "").replace("tl", "")
          .replace("kW/sa", "").replace("kWh", "").replace("%", "")
          .replace("Ön:", "").replace("Arka:", "")
          .replace("Şanzıman Bulunmuyor", "").replace("Şanziman Bulunmuyor", "")
          .replace(",", "."))
    s = re.sub(r"[^0-9\.\-]", "", s)
    if s == "": return np.nan
    try: return float(s)
    except: return np.nan

def safe_numeric_series(df: pd.DataFrame, col_name: str, default=0.0) -> pd.Series:
    """Safely get a numeric series from a DataFrame, cleaning and filling NaNs."""
    if col_name in df.columns:
        # Apply the cleaning function and then convert to numeric
        return df[col_name].apply(clean_numeric).fillna(default)
    else:
        return pd.Series([default] * len(df), index=df.index)

def int_round_series(s: pd.Series) -> pd.Series:
    """Round to nearest whole number and convert to integer dtype."""
    return s.round().astype('Int64')

# ----------------------------
# Pure Formula Scoring Functions
# ----------------------------

####################################
# ✅ bakim SCORE ✅
####################################

def compute_bakim_score(df: pd.DataFrame) -> pd.Series:
   
    def parse_fuel_type(s):
        if not isinstance(s, str): return "other"
        s_low = s.lower()
        if "elektrik" in s_low or "bev" in s_low: return "elektrik"
        if "dizel" in s_low: return "dizel"
        if "lpg" in s_low: return "benzin+lpg"
        if "benzin" in s_low or "fosil" in s_low: return "benzin"
        return "other"

    def get_trans_factor(s):
        if not isinstance(s, str): return 1.0
        s_low = s.lower()
        for k, v in TRANS_FACTORS.items():
            if k in s_low: return v
        return 1.0
    
    FUEL_FACTORS = {"dizel": 1, "benzin": 0.75, "benzin+lpg": 0.9, "elektrik": 0.55}
    TRANS_FACTORS = {"otomatik": 1, "manuel": 0.7, "redükt": 0.0, "redukt": 0.0}  

    trans_factor = df.get("SANZIMAN & CEKIS SISTEMI - Sanziman Turu", pd.Series([""]*len(df))).fillna("").apply(get_trans_factor)
    fuel_factor = df.get("TEMEL OZELLIKLER - Yakit Turu", pd.Series([""]*len(df))).fillna("").apply(parse_fuel_type).map(FUEL_FACTORS).fillna(1.0)
    hp  = safe_numeric_series(df, "PERFORMANS - Beygir Gucu")
    cyl = safe_numeric_series(df, "MOTOR (Icten Yanmali) - Silindir Adedi")
    cc  = safe_numeric_series(df, "MOTOR (Icten Yanmali) - Silindir Hacmi")

    cost_raw =  ( (trans_factor * 15) + (fuel_factor * 15) + (hp / 150 * 15) + (cyl / 4 * 15) + (cc / 1600 * 15) )

    score = 20 + (cost_raw)

    return int_round_series(score)


####################################
# ✅ performans SCORE ✅
####################################

def compute_performans_score(df: pd.DataFrame) -> pd.Series:
   
    hiz    = safe_numeric_series(df, "PERFORMANS - Azami Hiz")
    tork   = safe_numeric_series(df, "PERFORMANS - Azami Tork")
    hp     = safe_numeric_series(df, "PERFORMANS - Beygir Gucu")
    accel  = safe_numeric_series(df, "PERFORMANS - 0 - 100 Km Hizlanma")
    weight = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")

    perf_raw = ( (hp / 150 * 15) + (tork / 250 * 10) + (hiz / 175 * 10) - (accel / 10 * 15) - (weight / 1500 * 15) )

    score = 20 + (perf_raw)

    return int_round_series(score)


####################################
# ✅ VOLUME SCORE ✅
####################################

def compute_ic_hacim_score(df: pd.DataFrame) -> pd.Series:

    gen = safe_numeric_series(df, "AGIRLIK & OLCULER - Genislik")
    uz  = safe_numeric_series(df, "AGIRLIK & OLCULER - Uzunluk")
    yuk = safe_numeric_series(df, "AGIRLIK & OLCULER - Yukseklik")

    volume_raw = (gen / 1750) * (uz / 4000) * (yuk / 1500)

    score = 20 + (volume_raw * 50)

    return int_round_series(score)


####################################
# ✅ COMFORT SCORE ✅
####################################

def compute_konfor_score(df: pd.DataFrame, ic_score: pd.Series) -> pd.Series:

    agirlik = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")
    taban = safe_numeric_series(df, "LASTIK & JANT - Taban Genisligi")
    kesit   = safe_numeric_series(df, "LASTIK & JANT - Kesit Orani" * 100)
    jant    = safe_numeric_series(df, "LASTIK & JANT - Jant Capi")
    ic_numeric = pd.to_numeric(ic_score, errors='coerce').fillna(50)

    comf_raw = ( (ic_numeric / 4.5) + (agirlik / 1500 * 15) + (taban / 215 * 10) + (kesit / 55 * 10) + (jant / 16 * 20) )

    score = 20 + (comf_raw)

    return int_round_series(score)


####################################
# ✅ SAFETY SCORE ✅
####################################


def compute_guvenlik_score(df: pd.DataFrame, ic_score: pd.Series) -> pd.Series:

    airbag = safe_numeric_series(df, "YOLCU EMNIYETI - Hava Yastigi Adedi")
    ncap   = safe_numeric_series(df, "YOLCU EMNIYETI - NCAP/ANCAP Adedi")
    agirlik = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")
    ic_numeric = pd.to_numeric(ic_score, errors='coerce').fillna(50)

    safe_raw = ( (ncap / 1 * 15) + (airbag / 1 * 3) + (agirlik / 1500 * 15) + (ic_numeric / 4.5) )
    
    score = 20 + (safe_raw)

    return int_round_series(score)


####################################
# ✅ ECO SCORE ✅
####################################

def compute_eko_score(df: pd.DataFrame, maint_score: pd.Series) -> pd.Series:
    
    def parse_fuel_type(s):
        if not isinstance(s, str): return "other"
        s_low = s.lower()
        if "elektrik" in s_low or "bev" in s_low: return "elektrik"
        if "dizel" in s_low: return "dizel"
        if "lpg" in s_low: return "benzin+lpg"
        if "benzin" in s_low or "fosil" in s_low: return "benzin"
        return "other"
    
    comb = safe_numeric_series(df, "YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km)")
    elec = safe_numeric_series(df, "MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)")
    mtv  = safe_numeric_series(df, "EKONOMI - MTV")
    jant = safe_numeric_series(df, "LASTIK & JANT - Jant Capi")

    fuel_col = df.get("TEMEL OZELLIKLER - Yakit Turu", pd.Series([""]*len(df))).fillna("").astype(str).apply(parse_fuel_type)
    is_electric = (fuel_col == "elektrik")
    consumption = comb.where(~is_electric, elec)
    consumption = consumption.fillna(8.0)
    maint_numeric = pd.to_numeric(maint_score, errors='coerce').fillna(50)

    score = ( (comb * 0.20) + (mtv * 0.15) + (jant * 0.15) + (maint_numeric * 0.50) )

    return int_round_series(score)


# ----------------------------
# Orchestration
# ----------------------------

def calculate_all_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Orchestrates the calculation of all sub-scores."""
    bakim = compute_bakim_score(df)
    ic_hacim = compute_ic_hacim_score(df)
    performans = compute_performans_score(df)
    konfor = compute_konfor_score(df, ic_hacim)
    guvenlik = compute_guvenlik_score(df, ic_hacim)
    eko = compute_eko_score(df, bakim)

    df_out = df.copy()
    df_out["bakim_Score"] = bakim
    df_out["performans_Score"] = performans
    df_out["Ic_Hacim_Score"] = ic_hacim
    df_out["Konfor_Score"] = konfor
    df_out["Guvenlik_Score"] = guvenlik
    df_out["Eko_Score"] = eko

    return df_out


# ----------------------------
# Main
# ----------------------------

def main():
    p = Path(INPUT_CSV)
    if not p.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(p, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False, na_values=["", "NaN", "nan"])
    df.columns = [str(c).strip() for c in df.columns]

    df_scored = calculate_all_scores(df)

    df_scored.to_csv(OUTPUT_CSV, sep=";", index=False, encoding="utf-8-sig")
    print(f"✅ Scoring complete with pure formula logic. Output: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()