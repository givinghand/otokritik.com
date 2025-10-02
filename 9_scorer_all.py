#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pure-formula scorer (no dataset-dependent scaling).
- Uses fixed formula transforms tuned for a wider spread.
- No min/max scaling across dataset; adding rows won't affect existing scores.
- All scores are integers (rounded).
- Sub-scores: Performance, Ic_Hacim, Konfor, Guvenlik, Eko, Maintenance.
- GLOBAL_SCORE is weighted sum of integer sub-scores (no clipping).
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ----------------------------
# I/O
# ----------------------------
INPUT_CSV = "CAR_DATA_FINAL_3.csv"
OUTPUT_CSV = "CAR_DATA_FINAL_4_SC.csv"

# ----------------------------
# Column mappings (from your header)
# ----------------------------
COL = {
    "hp": "PERFORMANS - Beygir Gucu",
    "tork": "PERFORMANS - Azami Tork",
    "hiz": "PERFORMANS - Azami Hiz",
    "accel": "PERFORMANS - 0 - 100 Km Hizlanma",
    "agirlik": "AGIRLIK & OLCULER - Agirlik",
    "genislik": "AGIRLIK & OLCULER - Genislik",
    "uzunluk": "AGIRLIK & OLCULER - Uzunluk",
    "yukseklik": "AGIRLIK & OLCULER - Yukseklik",
    "silindir_adedi": "MOTOR (Icten Yanmali) - Silindir Adedi",
    "silindir_hacmi": "MOTOR (Icten Yanmali) - Silindir Hacmi",
    "batarya_kapasite": "MOTOR (Elektrikli) - Batarya Kapasitesi",
    "elek_ortalama": "MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)",
    "comb_consumption": "YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km)",
    "mtv": "EKONOMI - MTV",
    "jant_capi": "LASTIK & JANT - Jant Capi",
    "hava_yastigi": "YOLCU EMNIYETI - Hava Yastigi Adedi",
    "ncap": "YOLCU EMNIYETI - NCAP/ANCAP Adedi",
    "yakitturu": "TEMEL OZELLIKLER - Yakit Turu",
    "ekonomi_bakim": "EKONOMI - Bakim Masrafi (Tahmini)",
}

# ----------------------------
# Helpers
# ----------------------------
def safe_series(df: pd.DataFrame, col_name: str, default=0.0) -> pd.Series:
    """Return numeric Series for column if exists; else Series of default (index aligned)."""
    if col_name in df.columns:
        return pd.to_numeric(df[col_name], errors="coerce").fillna(default)
    else:
        return pd.Series([default] * len(df), index=df.index)

def int_round_series(s: pd.Series) -> pd.Series:
    """Round to nearest whole number and convert to integer dtype (keep NaN as NaN)."""
    s_num = pd.to_numeric(s, errors="coerce")
    # keep NaN as NaN, otherwise round
    rounded = s_num.round().astype('Int64')  # pandas nullable integer
    return rounded

# ----------------------------
# Pure formula scoring functions
# ----------------------------
def compute_performance_score(df: pd.DataFrame) -> pd.Series:
    """
    Fixed formula for performance.
    Intuition:
      - horsepower and torque strong positive contributors
      - top speed positive
      - 0-100 accel: lower (faster) is better -> subtract higher times
      - weight penalizes performance
    Formula tuned to produce wider spread (typical results ~20..150)
    """
    hp = safe_series(df, COL["hp"], 0.0)
    tork = safe_series(df, COL["tork"], 0.0)
    hiz = safe_series(df, COL["hiz"], 0.0)
    accel = safe_series(df, COL["accel"], 0.0)
    weight = safe_series(df, COL["agirlik"], 0.0)

    # fixed formula (no dataset-dependent factors)
    # coefficients chosen experimentally to produce wider spread.
    raw = (
        10.0  # base bias
        + (hp * 0.25)        # horsepower: each hp -> 0.25 points
        + (tork * 0.12)      # torque effect
        + (hiz * 0.6)        # top speed significant
        - (accel * 6.0)      # accel seconds penalize strongly
        - (weight * 0.02)    # weight penalty (kg -> small)
    )
    return int_round_series(raw)


def compute_ic_hacim_score(df: pd.DataFrame) -> pd.Series:
    """
    Cabin volume proxy:
    - Use width * length * height (units assumed mm or cm depending on your source).
    - The formula scales it up to a wider numeric range (no dataset scaling).
    """
    gen = safe_series(df, COL["genislik"], 0.0)     # e.g., mm or cm
    uz = safe_series(df, COL["uzunluk"], 0.0)
    yuk = safe_series(df, COL["yukseklik"], 0.0)

    # We try to be robust: if values seem like mm (>1000), convert to meters; if they look like cm use as cm.
    # But to keep pure formula, assume input in mm or cm; we'll compute an approximate cubic-decimeter
    # If values look like <100 (likely meters), multiply to get consistent units.
    gen_m = gen.copy()
    uz_m = uz.copy()
    yuk_m = yuk.copy()

    # basic heuristics:
    # if a dimension > 1000 assume mm -> convert to meters
    gen_m = gen_m.where(gen_m <= 1000, gen_m / 1000.0)
    uz_m = uz_m.where(uz_m <= 1000, uz_m / 1000.0)
    yuk_m = yuk_m.where(yuk_m <= 1000, yuk_m / 1000.0)

    # if still small (<1), maybe were in meters already; keep as is.
    # compute approximate volume in liters ~ m^3 * 1000
    volume_l = (gen_m * uz_m * yuk_m) * 1000.0  # liters approximation

    # map liters to a wider score range using fixed multiplier
    raw = 20.0 + (volume_l * 0.4) + 10.0  # baseline 30 + proportional
    # (this yields values in a broader band; no dataset min/max)
    return int_round_series(raw)


def compute_konfor_score(df: pd.DataFrame, ic_score: pd.Series) -> pd.Series:
    """
    Comfort formula:
      - Weighted contribution from ic_score (space)
      - seat count, presence of (auto) climate, leather seats, suspension proxy (absent) etc.
    """
    # ic_score is already integer series (nullable int). Convert to numeric filler for formula.
    ic_num = pd.to_numeric(ic_score, errors="coerce").fillna(30.0)

    koltuk_sayisi = safe_series(df, "KOLTUKLAR & IC DOSEME - Koltuk Sayisi", 5.0)
    klima_flag = df.get("ISITMA & SOGUTMA - Klima", pd.Series([""] * len(df))).astype(str).fillna("").str.contains("Var|Otomatik", case=False, regex=True).astype(int)
    doseme = df.get("KOLTUKLAR & IC DOSEME - Koltuk Dosemesi Tipi", pd.Series([""] * len(df))).astype(str).fillna("")
    deri_flag = doseme.str.contains("Deri", case=False, regex=True).astype(int)
    taban = safe_series(df, "LASTIK & JANT - Taban Genisligi", 0.0)
    kesit = safe_series(df, "LASTIK & JANT - Kesit Orani", 0.0)
    jant = safe_series(df, COL["jant_capi"], 0.0)

    raw = (
        10.0
        + ic_num * 0.3
        + koltuk_sayisi * 3.0
        + klima_flag * 12.0
        + deri_flag * 14.0
        + (taban * 0.12)
        + (kesit * 0.08)
        - (jant * 0.15)  # larger jants slightly reduce comfort
    )
    return int_round_series(raw)


def compute_guvenlik_score(df: pd.DataFrame, ic_score: pd.Series) -> pd.Series:
    """
    Safety formula:
      - airbag count, NCAP stars, cabin (ic_score) contribute positively
      - weight gives small penalty
    """
    airbag = safe_series(df, COL["hava_yastigi"], 0.0)
    ncap = safe_series(df, COL["ncap"], 0.0)
    weight = safe_series(df, COL["agirlik"], 0.0)

    raw = (
        5.0
        + airbag * 8.0
        + ncap * 12.0
        + pd.to_numeric(ic_score, errors="coerce").fillna(30.0) * 0.08
        - (weight * 0.01)
    )
    return int_round_series(raw)


def compute_eko_score(df: pd.DataFrame, maint_score: pd.Series) -> pd.Series:
    """
    Economy formula:
      - For ICE cars use L/100km: less is better
      - For EVs use kWh/100km: less is better (treated similarly)
      - MTV (tax) penalizes
      - jant size penalizes slightly
      - maintenance score included as component (higher maintenance score -> better economy if we defined it that way)
    """
    comb = safe_series(df, COL["comb_consumption"], np.nan)
    elec = safe_series(df, COL["elek_ortalama"], np.nan)
    mtv = safe_series(df, COL["mtv"], 0.0)
    jant = safe_series(df, COL["jant_capi"], 0.0)

    fuel_col = df.get(COL["yakitturu"], pd.Series([""] * len(df))).astype(str).fillna("").str.lower()
    is_electric = fuel_col.str.contains("elektrik") | fuel_col.str.contains("bev")

    # Default consumption: if electric and elec present use elec, else comb
    consumption = comb.copy().fillna(np.nan)
    # replace where electric and elec present
    mask_elec = is_electric & elec.notna()
    consumption.loc[mask_elec] = elec.loc[mask_elec]

    # build economy score: smaller consumption better -> invert, scale with fixed factors
    # We use baseline inversion with safe defaults
    cons_for_calc = consumption.fillna(8.0)  # assume 8 L/100 typical if missing
    cons_component = 120.0 - (cons_for_calc * 7.0)  # bigger factor to increase spread

    mtv_component = 120.0 - (mtv * 1.5)
    jant_component = 100.0 - (jant * 0.5)

    # maintenance_score is integer series; convert numeric
    maint_num = pd.to_numeric(maint_score, errors="coerce").fillna(80.0)

    raw = (
        10.0
        + cons_component * 0.25
        + mtv_component * 0.10
        + jant_component * 0.05
        + maint_num * 0.60 * 0.5  # include some effect of maintenance but not overpower
    )
    return int_round_series(raw)


def compute_maintenance_score(df: pd.DataFrame) -> pd.Series:
    """
    Maintenance: use a direct financial proxy -> lower costs are better (higher score)
    Use fixed formula where typical maintenance yields scores in wider band.
    """
    hp = safe_series(df, COL["hp"], 0.0)
    cyl = safe_series(df, COL["silindir_adedi"], 0.0)
    cc = safe_series(df, COL["silindir_hacmi"], 0.0)
    explicit_maint = safe_series(df, COL["ekonomi_bakim"], np.nan)

    base_cost = 2000.0 + hp * 22.0 + cyl * 85.0 + cc * 0.5
    combined_cost = base_cost.copy()
    has_explicit = ~explicit_maint.isna()
    if has_explicit.any():
        combined_cost.loc[has_explicit] = (base_cost.loc[has_explicit] + explicit_maint.loc[has_explicit]) / 2.0

    # convert to score: invert cost but scaled stronger to widen range
    raw = 150.0 - (combined_cost / 1000.0) * 12.0  # cost dominating factor -> wider spread
    return int_round_series(raw)

# ----------------------------
# Orchestration
# ----------------------------
def compute_global_scores(df: pd.DataFrame) -> pd.DataFrame:
    # Calculate pure formulas (no dataset scaling)
    maintenance = compute_maintenance_score(df)        # Int series
    performance = compute_performance_score(df)
    ic_hacim = compute_ic_hacim_score(df)
    konfor = compute_konfor_score(df, ic_hacim)
    guvenlik = compute_guvenlik_score(df, ic_hacim)
    ekonomi = compute_eko_score(df, maintenance)

    # assign to dataframe (as integers)
    df["Performance_Score"] = performance
    df["Ic_Hacim_Score"] = ic_hacim
    df["Konfor_Score"] = konfor
    df["Guvenlik_Score"] = guvenlik
    df["Eko_Score"] = ekonomi
    df["Maintenance_Score"] = maintenance

    # Global score: weighted integer sum of sub-scores (weights fixed)
    # Use numeric conversion, treat missing as 0 in sum (but earlier functions filled defaults)
    perf_n = pd.to_numeric(df["Performance_Score"], errors="coerce").fillna(0)
    maint_n = pd.to_numeric(df["Maintenance_Score"], errors="coerce").fillna(0)
    ic_n = pd.to_numeric(df["Ic_Hacim_Score"], errors="coerce").fillna(0)
    guv_n = pd.to_numeric(df["Guvenlik_Score"], errors="coerce").fillna(0)
    eko_n = pd.to_numeric(df["Eko_Score"], errors="coerce").fillna(0)
    kon_n = pd.to_numeric(df["Konfor_Score"], errors="coerce").fillna(0)

    raw_global = (
        perf_n * 0.30 +
        maint_n * 0.20 +
        ic_n   * 0.20 +
        guv_n  * 0.20 +
        eko_n  * 0.10
    )
    # round to integer
    df["GLOBAL_SCORE"] = raw_global.round().astype('Int64')

    return df

# ----------------------------
# Main
# ----------------------------
def main():
    p = Path(INPUT_CSV)
    if not p.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(p, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False, na_values=["", "NaN", "nan"])
    # trim whitespace
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    df_scored = compute_global_scores(df)

    # Save (convert Int64 to plain int where possible)
    # Replace pandas Int64 with Python int/NaN for CSV friendliness
    for c in ["Performance_Score","Ic_Hacim_Score","Konfor_Score","Guvenlik_Score","Eko_Score","Maintenance_Score","GLOBAL_SCORE"]:
        if c in df_scored.columns:
            df_scored[c] = df_scored[c].astype('Int64')

    df_scored.to_csv(OUTPUT_CSV, sep=";", index=False, encoding="utf-8-sig")
    print(f"✅ Scoring complete. Output: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
