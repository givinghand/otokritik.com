import pandas as pd
import numpy as np
from pathlib import Path
import re

# ----------------------------
# I/O
# ----------------------------

INPUT_CSV = "CAR_DATA_FINAL_3.csv"
OUTPUT_CSV = "CAR_DATA_FINAL_4.csv"

# ----------------------------
# Calculation Parameters & Weights
# ----------------------------

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
# ✅ BAKIM SCORE ✅
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
    
    FUEL_FACTORS = {"dizel": 18, "benzin": 10, "benzin+lpg": 14, "elektrik": 8}
    TRANS_FACTORS = {"otomatik": 14, "manuel": 7, "redükt": 0.0, "redukt": 0.0}  

    trans_factor = df.get("SANZIMAN & CEKIS SISTEMI - Sanziman Turu", pd.Series([""]*len(df))).fillna("").apply(get_trans_factor)
    fuel_factor = df.get("TEMEL OZELLIKLER - Yakit Turu", pd.Series([""]*len(df))).fillna("").apply(parse_fuel_type).map(FUEL_FACTORS).fillna(1.0)
    hp  = safe_numeric_series(df, "PERFORMANS - Beygir Gucu")
    cyl = safe_numeric_series(df, "MOTOR (Icten Yanmali) - Silindir Adedi")
    cc  = safe_numeric_series(df, "MOTOR (Icten Yanmali) - Silindir Hacmi")

    cost_raw =  ( (trans_factor) + (fuel_factor) + (hp / 25) + (cyl * 3) + (cc / 120) )
    score = 130 - (cost_raw)

    return int_round_series(score)


####################################
# ✅ PERFORMANS SCORE ✅
####################################

def compute_performans_score(df: pd.DataFrame) -> pd.Series:
   
    hiz    = safe_numeric_series(df, "PERFORMANS - Azami Hiz")
    tork   = safe_numeric_series(df, "PERFORMANS - Azami Tork")
    hp     = safe_numeric_series(df, "PERFORMANS - Beygir Gucu")
    accel  = safe_numeric_series(df, "PERFORMANS - 0 - 100 Km Hizlanma", default=12)
    weight = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")

    perf_raw = ( (hp / 15) + (tork / 20) + (hiz / 15) + ( 150 / accel) - (weight / 100) )

    score = 20 + (perf_raw)

    return int_round_series(score)


####################################
# ✅ VOLUME SCORE ✅
####################################

def compute_ic_hacim_score(df: pd.DataFrame) -> pd.Series:

    gen = safe_numeric_series(df, "AGIRLIK & OLCULER - Genislik")
    uz  = safe_numeric_series(df, "AGIRLIK & OLCULER - Uzunluk")
    yuk = safe_numeric_series(df, "AGIRLIK & OLCULER - Yukseklik")

    volume_raw = (gen / 1000) * (uz / 1000) * (yuk / 1000)

    score = (volume_raw * 6)

    return int_round_series(score)


####################################
# ✅ COMFORT SCORE ✅
####################################

def compute_konfor_score(df: pd.DataFrame, ic_score: pd.Series) -> pd.Series:

    agirlik = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")
    taban = safe_numeric_series(df, "LASTIK & JANT - Taban Genisligi")
    kesit   = safe_numeric_series(df, "LASTIK & JANT - Kesit Orani")
    jant    = safe_numeric_series(df, "LASTIK & JANT - Jant Capi")
    ic_numeric = pd.to_numeric(ic_score, errors='coerce').fillna(0)

    comf_raw = ( (ic_numeric / 5) + (agirlik / 75) + (taban / 15) + (kesit / 4) + ((jant-14) * 5) )

    score = (comf_raw)

    return int_round_series(score)


####################################
# ✅ SAFETY SCORE ✅
####################################

def compute_guvenlik_score(df: pd.DataFrame, ic_score: pd.Series) -> pd.Series:

    airbag = safe_numeric_series(df, "YOLCU EMNIYETI - Hava Yastigi Adedi")
    ncap   = safe_numeric_series(df, "YOLCU EMNIYETI - NCAP/ANCAP Adedi")
    agirlik = safe_numeric_series(df, "AGIRLIK & OLCULER - Agirlik")
    ic_numeric = pd.to_numeric(ic_score, errors='coerce').fillna(0)

    # NCAP puanını koşullu olarak hesapla
    ncap_points = (ncap - 3) * 25
    ncap_points[ncap <= 3] = 0

    # Airbag puanını koşullu olarak hesapla
    airbag_points = (airbag - 2) * 5
    airbag_points[airbag <= 2] = 0

    # Tüm puanları toplayarak safe_raw değerini oluştur
    safe_raw = ncap_points + airbag_points + (agirlik / 120) + (ic_numeric / 10)
    
    score = 20 + (safe_raw)

    return int_round_series(score)


####################################
# ✅ ECO SCORE ✅
####################################

def compute_eko_score(df: pd.DataFrame, maint_score: pd.Series , comf_score: pd.Series) -> pd.Series:
    
    def parse_fuel_type(s):
        if not isinstance(s, str): return "other"
        s_low = s.lower()
        if "elektrik" in s_low or "bev" in s_low: return "elektrik"
        if "dizel" in s_low: return "dizel"
        if "lpg" in s_low: return "benzin+lpg"
        if "benzin" in s_low or "fosil" in s_low: return "benzin"
        return "other"
    
    comb = safe_numeric_series(df, "YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km)")
    mtv  = safe_numeric_series(df, "EKONOMI - MTV")

    fuel_col = df.get("TEMEL OZELLIKLER - Yakit Turu", pd.Series([""]*len(df))).fillna("").astype(str).apply(parse_fuel_type)
    is_electric = (fuel_col == "elektrik")
    
    adjusted_comb = comb.where(~is_electric, comb / 3.0)
    adjusted_comb = adjusted_comb.fillna(8.0)

    maint_numeric = pd.to_numeric(maint_score, errors='coerce').fillna(0)
    comf_numeric = pd.to_numeric(comf_score, errors='coerce').fillna(0)

    eco_raw = ( (adjusted_comb * 4) + (mtv / 300) + ((comf_numeric - 50) / 3) ) + ((-maint_numeric + 20) / 3)
    score = 100 - (eco_raw)

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
    eko = compute_eko_score(df, bakim, konfor)

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






############################################
#-------------------------------------------
############################################
#-------------------------------------------






from pathlib import Path
import pandas as pd
import unicodedata
import re

# ---------- CONFIG (fixed filenames) ----------
INPUT_CSV = "CAR_DATA_FINAL_4.csv"
OUTPUT_CSV = "CAR_DATA_FINAL_4.csv"
ENCODING = "utf-8-sig"

# Transliteration map (Turkish -> ASCII)
_TRANSLIT_MAP = {
    "ç": "c", "Ç": "C",
    "ğ": "g", "Ğ": "G",
    "ı": "i", "İ": "I",
    "ö": "o", "Ö": "O",
    "ş": "s", "Ş": "S",
    "ü": "u", "Ü": "U",
    "â": "a", "Â": "A",
    "î": "i", "Î": "I",
    "û": "u", "Û": "U",
}
_TRANSLIT_TABLE = str.maketrans(_TRANSLIT_MAP)

def detect_delimiter(path: Path, sample_lines: int = 8) -> str:
    """Heuristic: read first few non-empty lines and choose ';' if more semicolons, else comma."""
    sem, com = 0, 0
    with path.open("r", encoding=ENCODING, errors="ignore") as f:
        for _ in range(sample_lines):
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if line == "":
                continue
            sem += line.count(";")
            com += line.count(",")
    # prefer semicolon if equal or greater
    return ";" if sem >= com else ","

def transliterate_text(x: str) -> str:
    """Transliterate Turkish chars in a single string, preserve other characters."""
    if pd.isna(x):
        return x
    s = str(x)
    # first try to fix common mojibake issues: re-decode if looks like mojibake
    if any(ch in s for ch in ("Ã", "Â", "Ä")):
        try:
            s2 = s.encode("latin1").decode("utf-8")
            # if result looks more ascii-like, use it
            if re.search(r"[A-Za-zİŞŞĞÇÖÜıığçöü]", s2):
                s = s2
        except Exception:
            pass
    # normalize and remove combining diacritics
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # translate Turkish characters using table (covers uppercase too)
    s = s.translate(_TRANSLIT_TABLE)
    return s

def transliterate_dataframe(df: pd.DataFrame, transliterate_column_names: bool = True):
    """Transliterate column names and all object/string columns. Returns new df and stats."""
    df_out = df.copy(deep=True)
    colname_changes = {}
    if transliterate_column_names:
        new_cols = []
        for c in df_out.columns:
            c_new = transliterate_text(c)
            if c_new != c:
                colname_changes[c] = c_new
            new_cols.append(c_new)
        df_out.columns = new_cols

    replacements = 0
    per_col = {}
    # choose columns to transliterate: all object/string columns
    for col in df_out.columns:
        # skip numeric columns (but we read everything as str - check dtype)
        # we still transliterate only if a string-like column (object) or arbitrary (we read as str)
        series = df_out[col].astype(object)
        changed = 0
        # apply transliteration elementwise but keep NaN as-is
        def _apply_val(v):
            nonlocal changed
            if pd.isna(v):
                return v
            s = str(v)
            s2 = transliterate_text(s)
            if s2 != s:
                changed += 1
            return s2
        df_out[col] = series.map(_apply_val)
        if changed:
            replacements += changed
            per_col[col] = changed

    stats = {"total_replacements": replacements, "per_col": per_col, "colname_changes": colname_changes}
    return df_out, stats

def main():
    p = Path(INPUT_CSV)
    if not p.exists():
        print(f"ERROR: input file not found: {p}")
        return

    delim = detect_delimiter(p)
    print(f"Detected delimiter: {repr(delim)}")

    # read everything as strings to preserve content exactly
    df = pd.read_csv(p, sep=delim, dtype=str, encoding=ENCODING, keep_default_na=False, na_values=["", "NaN", "nan"])
    print(f"Read CSV: rows={len(df)}, cols={len(df.columns)}")

    df_fixed, stats = transliterate_dataframe(df, transliterate_column_names=True)

    print("Column name changes:", stats["colname_changes"] if stats["colname_changes"] else "none")
    print("Value replacements total:", stats["total_replacements"])
    if stats["per_col"]:
        print("Per-column replacements (sample):")
        for k, v in list(stats["per_col"].items())[:10]:
            print(f"  {k}: {v}")

    # write output using the same delimiter as detected
    df_fixed.to_csv(OUTPUT_CSV, sep=delim, index=False, encoding=ENCODING)
    print(f"✅ Wrote: {OUTPUT_CSV} (rows={len(df_fixed)}, cols={len(df_fixed.columns)})")

if __name__ == "__main__":
    main()










#################################################################################
#################################################################################
#################################################################################








#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rename_reorder_car_data_fixed.py

Fixed version of the renaming & reordering script.

Improvements / fixes:
 - Auto-detects delimiter (prefers ';' if present otherwise ',').
 - Robust header matching: case-insensitive, strips whitespace and normalizes
   Turkish characters / punctuation so mapping keys match even if slightly different.
 - Preserves all data rows (no accidental dropping).
 - Prints summary: original rows/cols, written rows/cols and missing mapping keys.
 - Keeps cell contents exactly as read (no dtype conversion).
"""

from pathlib import Path
import csv
import re
from collections import OrderedDict
import unicodedata # Import moved to top for clarity

# ---------- CONFIG ----------
INPUT_CSV = "CAR_DATA_FINAL_4.csv"
OUTPUT_CSV = "CAR_DATA_FINAL_4.csv"
APPEND_EXTRAS = False  # set True if you want columns not in mapping appended to output
ENCODING = "utf-8-sig"

# ---------- MAPPING (original_name -> new_name) ----------
MAPPING = OrderedDict([
    # TEMEL BILGILER
    ("BASLIK", "TEMEL BILGILER - Baslik"),
    ("TEMEL OZELLIKLER - Arac Turu", "TEMEL BILGILER - Arac Turu"),
    ("TEMEL OZELLIKLER - Govde Tipi", "TEMEL BILGILER - Govde Tipi"),
    ("TEMEL OZELLIKLER - Segment", "TEMEL BILGILER - Segment"),
    ("MARKA", "TEMEL BILGILER - Marka"),
    ("TEMEL OZELLIKLER - Seri", "TEMEL BILGILER - Seri"),
    ("MODEL", "TEMEL BILGILER - Model"),
    ("TEMEL OZELLIKLER - Donanim Paketi", "TEMEL BILGILER - Donanim Paketi"),
    ("TEMEL OZELLIKLER - Model Yillari", "TEMEL BILGILER - Model Yili"),
    ("TEMEL OZELLIKLER - Ait Oldugu Ulke", "TEMEL BILGILER - Uretim Ulkesi"),

    # MOTOR
    ("TEMEL OZELLIKLER - Yakit Turu", "MOTOR - Yakit Turu"),
    ("TEMEL OZELLIKLER - Yakit Tipi", "MOTOR - Yakit Tipi"),
    ("TEMEL OZELLIKLER - Motor Tipi", "MOTOR - Motor Tipi"),
    ("MOTOR (Icten Yanmali) - Besleme Tipi", "MOTOR (Fosil Yakit) - Besleme Tipi"),
    ("MOTOR (Icten Yanmali) - Silindir Adedi", "MOTOR (Fosil Yakit) - Silindir Adedi"),
    ("MOTOR (Icten Yanmali) - Silindir Hacmi", "MOTOR (Fosil Yakit) - Silindir Hacmi"),
    ("MOTOR (Icten Yanmali) - Yakit Puskurtme", "MOTOR (Fosil Yakit) - Yakit Puskurtme"),
    ("MOTOR (Elektrikli) - Motor Gucu", "MOTOR (Elektrik) - Motor Gucu"),
    ("MOTOR (Elektrikli) - Batarya Kapasitesi", "MOTOR (Elektrik) - Batarya Kapasitesi"),
    ("MOTOR (Elektrikli) - Batarya Tipi", "MOTOR (Elektrik) - Batarya Tipi"),

    # SANZIMAN
    ("SANZIMAN & CEKIS SISTEMI - Sanziman Turu", "SANZIMAN - Sanziman Turu"),
    ("SANZIMAN & CEKIS SISTEMI - Sanziman Modeli", "SANZIMAN - Sanziman Modeli"),
    ("SANZIMAN & CEKIS SISTEMI - Sanziman Kademesi", "SANZIMAN - Vites Sayisi"),

    # PERFORMANS
    ("performans_Score", "PERFORMANS - PERFORMANS PUANI"),
    ("PERFORMANS - Beygir Gucu", "PERFORMANS - Beygir Gucu"),
    ("PERFORMANS - Azami Tork", "PERFORMANS - Azami Tork"),
    ("PERFORMANS - Azami Hiz", "PERFORMANS - Azami Hiz"),
    ("PERFORMANS - 0 - 100 Km Hizlanma", "PERFORMANS - 0-100 Km Hizlanma"),

    # CEKIS SISTEMI
    ("SANZIMAN & CEKIS SISTEMI - Cekis", "CEKIS SISTEMI - Cekis Turu"),
    ("SANZIMAN & CEKIS SISTEMI - Cekis Kontrol Sistemi", "CEKIS SISTEMI - Cekis Kontrol Sistemi"),

    # BOYUTLAR
    ("Konfor_Score", "BOYUTLAR - KONFOR PUANI"),
    ("Ic_Hacim_Score", "BOYUTLAR - Ic Hacim"),
    ("AGIRLIK & OLCULER - Uzunluk", "BOYUTLAR - Uzunluk"),
    ("AGIRLIK & OLCULER - Genislik", "BOYUTLAR - Genislik"),
    ("AGIRLIK & OLCULER - Yukseklik", "BOYUTLAR - Yukseklik"),
    ("AGIRLIK & OLCULER - Agirlik", "BOYUTLAR - Ağirlik"),
    ("BAGAJ OZELLIKLERI - Bagaj Hacmi (5 Koltuk)", "BOYUTLAR - Bagaj Hacmi (Standart)"),
    ("BAGAJ OZELLIKLERI - Bagaj Hacmi (2 Koltuk)", "BOYUTLAR - Bagaj Hacmi (Genisletilmis)"),

    # LASTIK & JANT
    ("LASTIK & JANT - Lastik Ebatlari", "LASTIK & JANT - Lastik Ebatlari"),
    ("LASTIK & JANT - Jant Capi", "LASTIK & JANT - Jant Capi"),
    ("LASTIK & JANT - Kesit Orani", "LASTIK & JANT - Kesit Orani"),
    ("LASTIK & JANT - Taban Genisligi", "LASTIK & JANT - Taban Genisliği"),

    # DIS DONANIM
    ("DIS GOVDE - Kapi Sayisi", "DIS DONANIM - Kapi Sayisi"),
    ("LAMBALAR & AYDINLATMA - Far Tipi", "DIS DONANIM- Far Tipi"),
    ("LAMBALAR & AYDINLATMA - Sis Farlari", "DIS DONANIM- Sis Farlari"),

    # IC DONANIM
    ("KOLTUKLAR & IC DOSEME - Koltuk Sayisi", "IC DONANIM - Koltuk Sayisi"),
    ("KOLTUKLAR & IC DOSEME - Koltuk Dosemesi Tipi", "IC DONANIM - Doseme Tipi"),
    ("KOLTUKLAR & IC DOSEME - Surucu Koltugu Ayarlari", "IC DONANIM - Surucu Koltuğu Ayarlari"),
    ("KOLTUKLAR & IC DOSEME - On Yolcu Koltugu Ayarlari", "IC DONANIM - On Yolcu Koltuğu Ayarlari"),
    ("ISITMA & SOGUTMA - Klima", "IC DONANIM - Klima"),

    # SENSORLER
    ("GOSTERGELER & SENSORLER - Far Sensoru", "SENSORLER - Far Sensoru"),
    ("GOSTERGELER & SENSORLER - Yagmur Sensoru", "SENSORLER - Yağmur Sensoru"),
    ("GOSTERGELER & SENSORLER - Lastik Basinc Sensoru", "SENSORLER - Lastik Basinc Sensoru"),
    ("GOSTERGELER & SENSORLER - Park Sensoru & Yardimi", "SENSORLER - Park Sensoru & Yardimcisi"),

    # GUVENLIK
    ("Guvenlik_Score", "GUVENLIK - GUVEN PUANI"),
    ("YOLCU EMNIYETI - Hava Yastigi Adedi", "GUVENLIK - Hava Yastiği Adedi"),
    ("YOLCU EMNIYETI - NCAP/ANCAP Adedi", "GUVENLIK - NCAP/ANCAP Puani"),

    # EKONOMI
    ("Eko_Score", "EKONOMI - EKO PUANI"),
    ("bakim_Score", "EKONOMI - Tahmini Bakim Masrafi"),
    ("EKONOMI - MTV", "EKONOMI - Yillik MTV Tutari"),
    ("YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km)", "EKONOMI - Ortalama Yakit Tuketimi (100 km)"),
    ("YAKIT TUKETIMI & EMISYON - Sehir Ici Tuketim (100 km)", "EKONOMI - Sehir Ici Tuketim (100 km)"),
    ("YAKIT TUKETIMI & EMISYON - Sehir Disi Tuketim (100 km)", "EKONOMI - Sehir Disi Tuketim (100 km)"),
    ("YAKIT TUKETIMI & EMISYON - Yakit Kapasitesi (lt)", "EKONOMI (Fosil Yakit) - Yakit Kapasitesi (lt)"),
    ("MOTOR (Elektrikli) - Menzil (WLTP - Birlesik)", "EKONOMI (Elektrik) - Menzil (WLTP - Birlesik)"),
    ("MOTOR (Elektrikli) - Menzil (WLTP - Sehir Ici)", "EKONOMI (Elektrik) - Menzil (WLTP - Sehir Ici)"),
    ("MOTOR (Elektrikli) - Sarj Suresi", "EKONOMI (Elektrik) - Sarj Suresi"),

    # EMISYON
    ("YAKIT TUKETIMI & EMISYON - Emisyon Standardi", "EMISYON - Emisyon Standardi"),
    ("YAKIT TUKETIMI & EMISYON - Ortalama Emisyon", "EMISYON - Ortalama Emisyon"),
])

# -------------------------------------------------------------------------

def detect_delimiter(sample_line: str):
    """
    Choose delimiter heuristically using first non-empty line.
    Prefer ';' if appears more often than ',' otherwise use ','.
    """
    if not sample_line:
        return ';'
    sc = sample_line.count(';')
    cc = sample_line.count(',')
    return ';' if sc >= cc else ','

def normalize(colname: str) -> str:
    """Normalize string for matching (strip, lower, remove diacritics & non-alnum)"""
    if colname is None:
        return ""
    s = str(colname).strip().lower()
    s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def build_index_map(header):
    """Return dict: normalized_name -> (index, original_name)"""
    return {normalize(h): (i, h) for i, h in enumerate(header)}

def main():
    inp = Path(INPUT_CSV)
    outp = Path(OUTPUT_CSV)
    if not inp.exists():
        print(f"Error: input file not found: {inp}")
        return

    # --- Step 1: Read all data from the source file into memory ---
    original_header = []
    all_data_rows = []
    delimiter = ','

    try:
        # First, detect delimiter
        with inp.open("r", encoding=ENCODING, newline='') as f:
            first_line = f.readline()
            delimiter = detect_delimiter(first_line)

        # Now, read all content using the detected delimiter
        with inp.open("r", encoding=ENCODING, newline='') as f_in:
            reader = csv.reader(f_in, delimiter=delimiter)
            original_header = [h.strip() for h in next(reader)]
            all_data_rows = list(reader) # Read all remaining rows into memory

    except FileNotFoundError:
        print(f"Error: input file not found: {inp}")
        return
    except StopIteration:
        print("Input CSV file is empty. Nothing to do.")
        return

    # --- Step 2: Process headers and prepare mappings (in memory) ---
    idx_map = build_index_map(original_header)

    pick_indices = []
    new_header = []
    missing_keys = []
    used_original_cols = set()

    for orig_key, new_name in MAPPING.items():
        nkey = normalize(orig_key)
        if nkey in idx_map:
            matched_idx, original_col_name = idx_map[nkey]
            pick_indices.append(matched_idx)
            used_original_cols.add(original_col_name)
        else:
            pick_indices.append(None)
            missing_keys.append(orig_key)
        new_header.append(new_name)

    extras = [c for c in original_header if c not in used_original_cols]
    final_header = list(new_header)
    if APPEND_EXTRAS:
        final_header.extend(extras)

    # --- Step 3: Write the processed data from memory back to the file ---
    with outp.open("w", encoding=ENCODING, newline='') as f_out:
        writer = csv.writer(f_out, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(final_header)

        for row in all_data_rows:
            out_row = []
            for idx in pick_indices:
                if idx is None:
                    out_row.append("")
                else:
                    out_row.append(row[idx] if idx < len(row) else "")

            if APPEND_EXTRAS:
                for e in extras:
                    try:
                        e_idx = original_header.index(e)
                        out_row.append(row[e_idx] if e_idx < len(row) else "")
                    except ValueError:
                        out_row.append("") # Should not happen, but for safety
            writer.writerow(out_row)

    # --- Step 4: Print Summary ---
    print(f"Output written: {outp!s}")
    if missing_keys:
        print("\nThe following mapping keys were NOT found in input header (these will be empty columns in output):")
        for k in missing_keys:
            print(" -", k)
    if extras:
        print("\nInput CSV contains extra columns not in mapping:")
        for e in extras:
            print(" -", e, ("(appended)" if APPEND_EXTRAS else "(not appended)"))

    print(f"\nDone.")
    print(f"Original rows (excluding header): {len(all_data_rows)}, Original columns: {len(original_header)}")
    print(f"Rows written: {len(all_data_rows)}, Columns written: {len(final_header)}")


if __name__ == '__main__':
    main()

