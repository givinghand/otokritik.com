#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pure-formula scorer without dataset scaling.
- Uses fixed formulas to transform raw data into scores.
- The formulas are tuned to produce results generally in the 20-100 range.
- No min/max scaling; each row is calculated independently.
- All final scores are rounded to integers.
- Sub-scores: Performance, Ic_Hacim, Konfor, Guvenlik, Eko, Maintenance.
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
PERFORMANCE_WEIGHTS = {"hiz": 0.2, "tork": 0.2, "hp": 0.2, "accel": 0.2, "weight": 0.2}
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
# ✅ MAINTANENCE SCCORE ✅
####################################

def compute_maintenance_score(df: pd.DataFrame) -> pd.Series:
    """
    Estimates a raw maintenance cost and converts it to a score (higher = better/cheaper).
    The formula inverts the cost so that lower costs yield scores closer to 100.
    """
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

    # Vectorized extraction of factors
    trans_factor = df.get("SANZIMAN & CEKIS SISTEMI - Sanziman Turu", pd.Series([""]*len(df))).fillna("").apply(get_trans_factor)
    fuel_factor = df.get("TEMEL OZELLIKLER - Yakit Turu", pd.Series([""]*len(df))).fillna("").apply(parse_fuel_type).map(FUEL_FACTORS).fillna(1.0)
    hp  = safe_numeric_series(df, "PERFORMANS - Beygir Gucu")
    cyl = safe_numeric_series(df, "MOTOR (Icten Yanmali) - Silindir Adedi")
    cc  = safe_numeric_series(df, "MOTOR (Icten Yanmali) - Silindir Hacmi")

    # Normalize values before applying coefficients
    hp_norm  = hp / 150
    cyl_norm = cyl / 4
    cc_norm  = cc / 1600

    # Calculate estimated raw cost
    cost_raw =  ((trans_factor * 10) + (fuel_factor * 10) + (hp_norm * 10) + (cyl_norm * 10) + (cc_norm * 10))

    # Convert cost to score: higher cost -> lower score.
    # Tuned to produce scores in the target range for typical costs.
    score = 120 - (cost_raw)
    return int_round_series(score)


####################################
# ✅ PERFORMANCE SCCORE ✅
####################################

def compute_performance_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculates performance score using a fixed formula. Higher values for hp, torque,
    and speed increase the score, while higher acceleration time and weight decrease it.
    """
    hiz    = safe_numeric_series(df, "PERFORMANS - Azami Hiz")
    tork   = safe_numeric_series(df, "PERFORMANS - Azami Tork")
    hp     = safe_numeric_series(df, "PERFORMANS - Beygir Gucu")
    accel  = safe_numeric_series(df, "PERFORMANS - 0 - 100 Km Hizlanma", default=15) # Default penalty
    weight = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")

    # Fixed formula with tuned coefficients to target the 20-100 range
    score = (
        20.0             # Base score
        + (hp * 0.22)    # Each HP adds points
        + (tork * 0.10)  # Each Nm of torque adds points
        + (hiz * 0.15)   # Top speed contributes
        - (accel * 4.0)  # Each second of acceleration subtracts points (penalty)
        - (weight * 0.015) # Weight penalizes performance
    )
    return int_round_series(score)

def compute_ic_hacim_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculates an interior volume proxy score from external dimensions.
    Assumes dimensions are in mm.
    """
    gen = safe_numeric_series(df, "AGIRLIK & OLCULER - Genislik")
    uz  = safe_numeric_series(df, "AGIRLIK & OLCULER - Uzunluk")
    yuk = safe_numeric_series(df, "AGIRLIK & OLCULER - Yukseklik")

    # Calculate volume in cubic meters, assuming inputs are in mm
    volume_m3 = (gen / 1000.0) * (uz / 1000.0) * (yuk / 1000.0)

    # Convert volume to a score with a baseline and multiplier
    score = 30.0 + (volume_m3 * 4.5)
    return int_round_series(score)

def compute_konfor_score(df: pd.DataFrame, ic_score: pd.Series) -> pd.Series:
    """
    Calculates comfort score from interior space, weight, and tire properties.
    A higher aspect ratio and weight are positive, while a larger rim diameter is negative.
    """
    agirlik = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")
    kesit   = safe_numeric_series(df, "LASTIK & JANT - Kesit Orani")
    jant    = safe_numeric_series(df, "LASTIK & JANT - Jant Capi")

    # Convert nullable int ic_score to numeric for calculation
    ic_numeric = pd.to_numeric(ic_score, errors='coerce').fillna(50)

    # Formula tuned to reflect weights and produce target range scores
    score = (
        40.0              # Base comfort score
        + (ic_numeric * 0.25)  # Larger space is more comfortable
        + (agirlik * 0.01)     # Heavier cars often have a smoother ride
        + (kesit * 0.5)        # Thicker tire sidewalls add comfort
        - (jant * 2.0)         # Larger rims reduce comfort (less sidewall)
    )
    return int_round_series(score)

def compute_guvenlik_score(df: pd.DataFrame, ic_score: pd.Series) -> pd.Series:
    """
    Calculates safety score from airbags, NCAP rating, weight, and vehicle size.
    All factors contribute positively to the score.
    """
    airbag = safe_numeric_series(df, "YOLCU EMNIYETI - Hava Yastigi Adedi")
    ncap   = safe_numeric_series(df, "YOLCU EMNIYETI - NCAP/ANCAP Adedi")
    weight = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")
    ic_numeric = pd.to_numeric(ic_score, errors='coerce').fillna(50)

    # Formula tuned to emphasize NCAP and airbags, as per weights
    score = (
        5.0
        + (ncap * 10.0)   # Each NCAP star is worth 10 points
        + (airbag * 4.0)  # Each airbag is worth 4 points
        + (weight * 0.01) # Heavier cars are generally safer in collisions
        + (ic_numeric * 0.1) # Larger cars offer more crumple zone
    )
    return int_round_series(score)

def compute_eko_score(df: pd.DataFrame, maint_score: pd.Series) -> pd.Series:
    """
    Calculates economy score from consumption, tax (MTV), rim size, and maintenance.
    The final score is a weighted average of score components.
    """
    comb = safe_numeric_series(df, "YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km)")
    elec = safe_numeric_series(df, "MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)")
    mtv  = safe_numeric_series(df, "EKONOMI - MTV")
    jant = safe_numeric_series(df, "LASTIK & JANT - Jant Capi")

    fuel_col = df.get("TEMEL OZELLIKLER - Yakit Turu", pd.Series([""]*len(df))).fillna("").astype(str).apply(parse_fuel_type)
    is_electric = (fuel_col == "elektrik")
    consumption = comb.where(~is_electric, elec)
    consumption = consumption.fillna(8.0) # Assume 8L/100km if missing

    maint_numeric = pd.to_numeric(maint_score, errors='coerce').fillna(50)

    # Create score components where higher is better (more economical)
    cons_comp = 100 - (consumption * 6.0)
    mtv_comp  = 100 - (mtv / 100.0)
    jant_comp = 100 - (jant * 1.5)

    # Weighted average of components
    score = (
        (cons_comp * 0.20) +
        (mtv_comp * 0.15) +
        (jant_comp * 0.15) +
        (maint_numeric * 0.50)
    )
    return int_round_series(score)

# ----------------------------
# Orchestration
# ----------------------------
def calculate_all_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Orchestrates the calculation of all sub-scores."""
    maintenance = compute_maintenance_score(df)
    ic_hacim = compute_ic_hacim_score(df)

    performance = compute_performance_score(df)
    konfor = compute_konfor_score(df, ic_hacim)
    guvenlik = compute_guvenlik_score(df, ic_hacim)
    eko = compute_eko_score(df, maintenance)

    df_out = df.copy()
    df_out["Maintenance_Score"] = maintenance
    df_out["Performance_Score"] = performance
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