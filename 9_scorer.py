#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import re
from pathlib import Path
from pandas.api.types import is_string_dtype

# ===============================
# Sabitler ve Ağırlıklar
# ===============================
INPUT_CSV  = "CAR_DATA_FINAL.csv"
OUTPUT_CSV = "CAR_DATA_SCORED.csv"

BASE_MAINT = 100.0
HP_COEFF   = 0.4
CYL_COEFF  = 0.3
CC_COEFF   = 0.3

FUEL_FACTORS = {
    "dizel": 1.2,
    "benzin": 1,
    "benzin+lpg": 1.1,
    "elektrik": 0.8,
}

TRANS_FACTORS = {
    "otomatik": 1.2,
    "manuel": 1.0,
    "redükt": 0.0,
    "redukt": 0.0,
}

SECURITY_WEIGHTS = {  # toplam 1.0
    "airbag": 0.30,
    "ncap": 0.50,
    "weight": 0.10,
    "height": 0.10,
}

PERFORMANCE_WEIGHTS = {  # 5 parametre eşit
    "hiz": 0.2,
    "tork": 0.2,
    "hp": 0.2,
    "accel": 0.2,
    "weight": 0.2,
}

IC_HACIM_WEIGHTS = {  # 3 parametre eşit
    "genislik": 1/3,
    "uzunluk": 1/3,
    "yukseklik": 1/3,
}

KONFOR_WEIGHTS = {  # kullanıcı girişi
    "ic": 0.25,
    "agirlik": 0.35,
    "taban": 0.075,
    "kesit": 0.075,
    "jant": 0.25,
}

NEW_COLUMNS = [
    "EKONOMI - Bakim Masrafi (Tahmini)",
    "Performance_Score",
    "Ic_Hacim_Score",
    "Konfor_Score",
    "Guvenlik_Score",
    "Eko_Score",
]

GROUP_COLS = [
    "TEMEL OZELLIKLER - Yakit Turu",
    "TEMEL OZELLIKLER - Arac Turu",
    "TEMEL OZELLIKLER - Govde Tipi",
    "TEMEL OZELLIKLER - Segment",
]

# ===============================
# Yardımcı Fonksiyonlar
# ===============================
def clean_numeric(x):
    """Karakter içeren sayıları temizle ve float olarak döndür."""
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s == "":
        return np.nan
    s = (s.replace("₺", "")
           .replace("TL", "")
           .replace("tl", "")
           .replace("kW/sa", "")
           .replace("kWh", "")
           .replace("%", "")
           .replace("Ön:", "")
           .replace("Arka:", "")
           .replace("Şanzıman Bulunmuyor", "")
           .replace("Şanziman Bulunmuyor", "")
           .replace(",", "."))
    s = re.sub(r"[^0-9\.\-]", "", s)
    if s == "":
        return np.nan
    try:
        return float(s)
    except:
        return np.nan

def parse_fuel_type(s):
    if not isinstance(s, str):
        return "other"
    s_low = s.lower()
    if "elektrik" in s_low or "bev" in s_low:
        return "elektrik"
    if "dizel" in s_low:
        return "dizel"
    if "lpg" in s_low:
        return "benzin+lpg"
    if "benzin" in s_low or "fosil" in s_low:
        return "benzin"
    return "other"

def get_trans_factor(s):
    if not isinstance(s, str):
        return 1.0
    s_low = s.lower()
    for k, v in TRANS_FACTORS.items():
        if k in s_low:
            return v
    return 1.0

def scale_50_100(series, invert=False):
    """Grup içinde min=50, max=100 olacak şekilde ölçekler."""
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().sum() == 0:
        return pd.Series([np.nan] * len(s), index=s.index)
    if invert:
        s = -s
    min_s, max_s = s.min(), s.max()
    if abs(max_s - min_s) < 1e-9:
        return pd.Series([100.0] * len(s), index=s.index)
    return 50 + (s - min_s) / (max_s - min_s) * 50

def round_half_up_series(s):
    """Half-up kuralıyla en yakın tam sayıya yuvarla."""
    s_float = pd.to_numeric(s, errors="coerce")
    mask = s_float.notna()
    out = pd.Series([np.nan] * len(s_float), index=s_float.index)
    if mask.any():
        out.loc[mask] = np.floor(s_float.loc[mask].astype(float) + 0.5).astype(int)
    return out

# ===============================
# Skor Hesaplama Fonksiyonları
# ===============================
def compute_maintenance_cost(df):
    df_copy = df.copy()

    def compute_row_cost(row):
        base = BASE_MAINT
        trans_factor = get_trans_factor(row.get("SANZIMAN & CEKIS SISTEMI - Sanziman Turu", ""))
        fuel_key = parse_fuel_type(row.get("TEMEL OZELLIKLER - Yakit Turu",
                                           row.get("TEMEL OZELLIKLER - Yakıt Turu", "")))
        fuel_factor = FUEL_FACTORS.get(fuel_key, 1.0)
        hp  = clean_numeric(row.get("PERFORMANS - Beygir Gucu", np.nan))
        cyl = clean_numeric(row.get("MOTOR (Icten Yanmali) - Silindir Adedi", np.nan))
        cc  = clean_numeric(row.get("MOTOR (Icten Yanmali) - Silindir Hacmi", np.nan))

        hp_norm  = (hp / 1000.0) if not np.isnan(hp) else 0.0
        cyl_norm = (cyl / 12.0)  if not np.isnan(cyl) else 0.0
        cc_norm  = (cc / 6000.0) if not np.isnan(cc) else 0.0

        return base * trans_factor * fuel_factor * (1.0 +
                                                    hp_norm * HP_COEFF +
                                                    cyl_norm * CYL_COEFF +
                                                    cc_norm * CC_COEFF)

    df_copy["cost_raw"] = df_copy.apply(compute_row_cost, axis=1)

    scores = []
    for _, group in df_copy.groupby(GROUP_COLS):
        grp_scaled = scale_50_100(group["cost_raw"], invert=True).fillna(50.0)
        scores.append(pd.Series(grp_scaled.values, index=group.index))

    return pd.concat(scores).sort_index().round(2)

def compute_performance_score(df):
    scores = []
    for _, group in df.groupby(GROUP_COLS):
        hiz    = scale_50_100(pd.to_numeric(group.get("PERFORMANS - Azami Hiz"), errors="coerce")).fillna(50.0)
        tork   = scale_50_100(pd.to_numeric(group.get("PERFORMANS - Azami Tork"), errors="coerce")).fillna(50.0)
        hp     = scale_50_100(pd.to_numeric(group.get("PERFORMANS - Beygir Gucu"), errors="coerce")).fillna(50.0)
        accel  = scale_50_100(pd.to_numeric(group.get("PERFORMANS - 0 - 100 Km Hizlanma"),
                                            errors="coerce"), invert=True).fillna(50.0)
        weight = scale_50_100(pd.to_numeric(group.get("AGIRLIK & OLCULER - Agirlik"),
                                            errors="coerce")).fillna(50.0)

        comp = (hiz    * PERFORMANCE_WEIGHTS["hiz"] +
                tork   * PERFORMANCE_WEIGHTS["tork"] +
                hp     * PERFORMANCE_WEIGHTS["hp"] +
                accel  * PERFORMANCE_WEIGHTS["accel"] +
                weight * PERFORMANCE_WEIGHTS["weight"])

        scores.append(pd.Series(comp.values, index=group.index))

    return pd.concat(scores).sort_index().round(2)

def compute_ic_hacim_score(df):
    scores = []
    for _, group in df.groupby(GROUP_COLS):
        gen = scale_50_100(pd.to_numeric(group.get("AGIRLIK & OLCULER - Genislik"), errors="coerce")).fillna(50.0)
        uz  = scale_50_100(pd.to_numeric(group.get("AGIRLIK & OLCULER - Uzunluk"), errors="coerce")).fillna(50.0)
        yuk = scale_50_100(pd.to_numeric(group.get("AGIRLIK & OLCULER - Yukseklik"), errors="coerce")).fillna(50.0)

        comp = (gen * IC_HACIM_WEIGHTS["genislik"] +
                uz  * IC_HACIM_WEIGHTS["uzunluk"] +
                yuk * IC_HACIM_WEIGHTS["yukseklik"])

        scores.append(pd.Series(comp.values, index=group.index))

    return pd.concat(scores).sort_index().round(2)

def compute_konfor_score(df, ic_score):
    scores = []
    for _, group in df.groupby(GROUP_COLS):
        ic      = ic_score.loc[group.index].fillna(50.0)
        agirlik = scale_50_100(pd.to_numeric(group.get("AGIRLIK & OLCULER - Agirlik"), errors="coerce")).fillna(50.0)
        taban   = scale_50_100(pd.to_numeric(group.get("LASTIK & JANT - Taban Genisligi"), errors="coerce")).fillna(50.0)
        kesit   = scale_50_100(pd.to_numeric(group.get("LASTIK & JANT - Kesit Orani"), errors="coerce")).fillna(50.0)
        jant    = scale_50_100(pd.to_numeric(group.get("LASTIK & JANT - Jant Capi"), errors="coerce")).fillna(50.0)

        comp = (ic      * KONFOR_WEIGHTS["ic"] +
                agirlik * KONFOR_WEIGHTS["agirlik"] +
                taban   * KONFOR_WEIGHTS["taban"] +
                kesit   * KONFOR_WEIGHTS["kesit"] +
                jant    * KONFOR_WEIGHTS["jant"])

        scores.append(pd.Series(comp.values, index=group.index))

    return pd.concat(scores).sort_index().round(2)

def compute_guvenlik_score(df, ic_score):
    scores = []
    for _, group in df.groupby(GROUP_COLS):
        idx       = group.index
        raw_airbg = pd.to_numeric(group.get("YOLCU EMNIYETI - Hava Yastigi Adedi"), errors="coerce")
        raw_ncap  = pd.to_numeric(group.get("YOLCU EMNIYETI - NCAP/ANCAP Adedi"), errors="coerce")
        raw_wgt   = pd.to_numeric(group.get("AGIRLIK & OLCULER - Agirlik"), errors="coerce")

        airbag = scale_50_100(raw_airbg).fillna(50.0)
        ncap   = scale_50_100(raw_ncap).fillna(50.0)
        weight = scale_50_100(raw_wgt).fillna(50.0)
        ic     = ic_score.loc[idx].fillna(50.0)

        comp = (airbag * SECURITY_WEIGHTS["airbag"] +
                ncap   * SECURITY_WEIGHTS["ncap"] +
                weight * SECURITY_WEIGHTS["weight"] +
                ic     * SECURITY_WEIGHTS["height"])

        had_any_raw = raw_airbg.notna() | raw_ncap.notna() | raw_wgt.notna() | pd.notna(ic)
        comp_series = pd.Series(comp.values, index=idx)
        comp_series.loc[~had_any_raw] = np.nan

        scores.append(comp_series)

    return pd.concat(scores).sort_index().round(2)

def compute_eko_score(df, maint_score):
    scores = []
    for _, group in df.groupby(GROUP_COLS):
        comb = pd.to_numeric(group.get("YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km)"),
                             errors="coerce")
        elec = pd.to_numeric(group.get("MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)"),
                             errors="coerce")
        mtv  = pd.to_numeric(group.get("EKONOMI - MTV"), errors="coerce")
        jant = pd.to_numeric(group.get("LASTIK & JANT - Jant Capi"), errors="coerce")

        # elektrik tüketimi
        fuel_col = group.get("TEMEL OZELLIKLER - Yakit Turu").fillna("").astype(str).apply(parse_fuel_type)
        use_elec = (fuel_col == "elektrik")

        consumption = comb.copy()
        if "elec" in locals():
            consumption.loc[use_elec.index] = consumption.loc[use_elec.index].fillna(np.nan)
            consumption.loc[use_elec] = elec.loc[use_elec]

        cons_s  = scale_50_100(consumption, invert=True).fillna(50.0)
        mtv_s   = scale_50_100(mtv, invert=True).fillna(50.0)
        jant_s  = scale_50_100(jant, invert=True).fillna(50.0)
        maint_s = maint_score.loc[group.index].fillna(50.0)

        comp = (cons_s  * 0.20 +
                mtv_s   * 0.15 +
                jant_s  * 0.10 +
                maint_s * 0.55)

        had_any_raw = (pd.to_numeric(consumption, errors="coerce").notna() |
                       pd.to_numeric(mtv, errors="coerce").notna() |
                       pd.to_numeric(jant, errors="coerce").notna() |
                       maint_s.notna())

        comp_series = pd.Series(comp.values, index=group.index)
        comp_series.loc[~had_any_raw] = np.nan

        scores.append(comp_series)

    return pd.concat(scores).sort_index().round(2)

# ===============================
# Main
# ===============================
def main():
    p = Path(INPUT_CSV)
    if not p.exists():
        raise FileNotFoundError(f"Girdi CSV bulunamadı: {INPUT_CSV}")

    df_orig = pd.read_csv(p, sep=";", engine="python",
                          encoding="utf-8-sig", dtype=str,
                          keep_default_na=False, na_values=["", "NaN", "nan"])
    df_orig.columns = [str(c).strip() for c in df_orig.columns]

    # boş/unnamed kolonları at
    cols_to_drop = [c for c in df_orig.columns if (c.strip() == "" or c.startswith("Unnamed"))]
    if cols_to_drop:
        df_orig = df_orig.drop(columns=cols_to_drop)

    df = df_orig.copy()
    for col in df.columns:
        if is_string_dtype(df[col]):
            df[col] = df[col].str.strip()

    # Skor hesaplamaları
    maint_score = compute_maintenance_cost(df)
    ic_score    = compute_ic_hacim_score(df)

    df[NEW_COLUMNS[0]] = maint_score
    df[NEW_COLUMNS[1]] = compute_performance_score(df)
    df[NEW_COLUMNS[2]] = ic_score
    df[NEW_COLUMNS[3]] = compute_konfor_score(df, ic_score)
    df[NEW_COLUMNS[4]] = compute_guvenlik_score(df, ic_score)
    df[NEW_COLUMNS[5]] = compute_eko_score(df, maint_score)

    # Yuvarlama
    for col in NEW_COLUMNS:
        if col in df.columns:
            df[col] = round_half_up_series(df[col])

    # CSV kaydet
    final_cols = list(df_orig.columns) + [c for c in NEW_COLUMNS if c not in df_orig.columns]
    for c in final_cols:
        if c not in df.columns:
            df[c] = np.nan

    df[final_cols].to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ Çıktı hazır: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
