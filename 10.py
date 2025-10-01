#!/usr/bin/env python3
"""
rename_reorder_car_data.py

Reads CAR_DATA_SCORED.csv, renames & reorders columns according to the provided mapping
and writes CAR_DATA.csv. Cell contents are preserved exactly (no dtype conversion).

If you want extras from the original file appended to the end, set APPEND_EXTRAS = True.
"""

import csv
import re
from collections import OrderedDict
from pathlib import Path

# ---------- CONFIG ----------
INPUT_CSV = "CAR_DATA_SCORED.csv"
OUTPUT_CSV = "CAR_DATA_ORDER.csv"
APPEND_EXTRAS = False  # set True if you want columns not in mapping appended to output

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
    ("Performance_Score", "PERFORMANS - PERFORMANS PUANI"),
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
    ("EKONOMI - Bakim Masrafi (Tahmini)", "EKONOMI - Tahmini Bakim Masrafi"),
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

def normalize(s: str) -> str:
    if s is None:
        return ""
    s = s.lower()
    # turkce karakter donusumu (basit)
    trans = str.maketrans(
        "iğusocIĞUSOC",
        "igusocigusoc",
    )
    s = s.translate(trans)
    # remove non-alphanumeric
    s = re.sub(r'[^a-z0-9]', '', s)
    return s


def build_index_map(header):
    """Return dict: normalized_name -> (index, original_name)"""
    idx_map = {}
    for i, h in enumerate(header):
        idx_map[normalize(h)] = (i, h)
    return idx_map


def main():
    inp = Path(INPUT_CSV)
    outp = Path(OUTPUT_CSV)

    if not inp.exists():
        print(f"Hata: input dosyasi bulunamadi: {inp}")
        return

    with inp.open("r", encoding="utf-8", newline='') as f_in:
        reader = csv.reader(f_in, delimiter=';')
        try:
            original_header = next(reader)
        except StopIteration:
            print("Hata: input CSV bos.")
            return
        original_header = [h.strip() for h in original_header]

        idx_map = build_index_map(original_header)

        pick_indices = []   # each element: index in original header or None
        new_header = []
        missing_keys = []
        used_original_cols = set()

        for orig_key, new_name in MAPPING.items():
            matched_idx = None
            # exact
            if orig_key in original_header:
                matched_idx = original_header.index(orig_key)
                used_original_cols.add(orig_key)
            else:
                nkey = normalize(orig_key)
                if nkey in idx_map:
                    matched_idx = idx_map[nkey][0]
                    used_original_cols.add(idx_map[nkey][1])
                else:
                    matched_idx = None

            pick_indices.append(matched_idx)
            new_header.append(new_name)
            if matched_idx is None:
                missing_keys.append(orig_key)

        extras = [c for c in original_header if c not in used_original_cols]
        final_header = list(new_header)
        if APPEND_EXTRAS:
            final_header.extend(extras)

    # write output preserving cell content exactly
    with inp.open("r", encoding="utf-8", newline='') as f_in, outp.open("w", encoding="utf-8", newline='') as f_out:
        reader = csv.reader(f_in, delimiter=';')
        writer = csv.writer(f_out, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # skip original header
        next(reader)

        # write new header
        writer.writerow(final_header)

        for row in reader:
            out_row = []
            for idx in pick_indices:
                if idx is None:
                    out_row.append("")
                else:
                    out_row.append(row[idx] if idx < len(row) else "")
            if APPEND_EXTRAS:
                for e in extras:
                    e_idx = original_header.index(e)
                    out_row.append(row[e_idx] if e_idx < len(row) else "")
            writer.writerow(out_row)

    # report
    print(f"Cikti yazildi: {outp}")
    if missing_keys:
        print("\nAsağidaki mapping anahtarlari input CSV'de bulunamadi ve ciktita bos sutun olarak yer alacak:")
        for k in missing_keys:
            print(" -", k)
    if extras:
        print("\nInput CSV icinde ama mapping'te olmayan ekstra sutunlar:")
        for e in extras:
            print(" -", e, ("(eklendi)" if APPEND_EXTRAS else "(eklenmedi)"))


if __name__ == '__main__':
    main()





###########################################################################################################






#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for tokens like: "6.Haz", "5.Şub", "3.Eyl", "9.Nis"
Runs improved normalization + conversion and prints results.
"""

import re
import unicodedata

_MONTH_MAP = {
    "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
    "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12,
    "oca":1,"sub":2,"şub":2,"subat":2,"mar":3,"nis":4,"may":5,
    "haz":6,"tem":7,"agu":8,"ağu":8,"eyl":9,"eki":10,"kas":11,"ara":12
}

def normalize_text(s: str) -> str:
    """Normalize string: remove BOM/zero-width, normalize unicode, replace weird dots/spaces, lower."""
    if s is None:
        return ""
    # ensure str
    s = str(s)
    # remove BOM and zero-width and control chars
    s = s.replace("\ufeff", "")
    s = s.replace("\u200b", "")  # zero width space
    s = s.replace("\u200c", "")
    s = s.replace("\u200d", "")
    # normalize to NFKC first
    s = unicodedata.normalize("NFKC", s)
    # replace various dot-like separators with plain dot
    s = re.sub(r"[·•·⋅•・]", ".", s)
    # replace other punctuation commonly used as separators (em dash, en dash) with dot/space
    s = re.sub(r"[–—−]", "-", s)
    # replace non-breaking spaces
    s = s.replace("\u00A0", " ")
    # strip outer whitespace
    s = s.strip()
    return s

def _norm_token(tok: str) -> str:
    t = normalize_text(tok).lower()
    # remove diacritics / combining marks
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return t

# relaxed regex (accept letters including Turkish, dots, spaces, hyphens)
_RE_DAY_MONTH = re.compile(r'^\s*(\d{1,2})[.\-/\s]+([A-Za-zÇĞİŞÜÖçğışüö]+)\s*$', re.UNICODE)
_RE_MONTH_NUM = re.compile(r'^\s*([A-Za-zÇĞİŞÜÖçğışüö]+)[.\-/\s]+([0-9]+(?:[.,][0-9]+)?)\s*$', re.UNICODE)
_RE_FULL_NUMERIC = re.compile(r'^\s*[-+]?\d+(?:[.,]\d+)?\s*$')

def month_token_to_num(tok: str):
    if tok is None:
        return None
    t = _norm_token(tok)
    # try decreasing lengths
    for L in (len(t), 4, 3, 2):
        key = t[:L]
        if key in _MONTH_MAP:
            return _MONTH_MAP[key]
    return None

def convert_value(val: str):
    s_orig = val
    s = normalize_text(val)
    if s == "":
        return s
    # if already numeric-ish, unify comma->dot and return
    if _RE_FULL_NUMERIC.match(s):
        return s.replace(",", ".")
    m = _RE_DAY_MONTH.match(s)
    if m:
        day_tok, mon_tok = m.group(1), m.group(2)
        monnum = month_token_to_num(mon_tok)
        if monnum:
            return f"{int(day_tok)}.{monnum}"
    m2 = _RE_MONTH_NUM.match(s)
    if m2:
        mon_tok, num_tok = m2.group(1), m2.group(2)
        monnum = month_token_to_num(mon_tok)
        if monnum:
            return f"{monnum}.{num_tok.replace(',', '.')}"
    # fallback: try splitting by '.' and see if any token matches month
    parts = re.split(r'[.\-/\s]+', s)
    for i, p in enumerate(parts):
        if month_token_to_num(p):
            # if month is first and second is numeric -> month.num
            if i == 0 and len(parts) > 1 and re.match(r'^\d+([.,]\d+)?$', parts[1]):
                return f"{month_token_to_num(p)}.{parts[1].replace(',', '.')}"
            # if month is second and first numeric -> day.monthnum
            if i == 1 and re.match(r'^\d+$', parts[0]):
                return f"{int(parts[0])}.{month_token_to_num(p)}"
    # no match -> return original (normalized)
    return s_orig

# Quick test on your examples
samples = ["6.Haz", "5.Şub", "3.Eyl", "9.Nis", "11.Mar", "Mar.40", "Nis.35", "3.Eyl ", " 5.Şub", "AĞu.40", "AÄŸu.40"]
print("Test conversions:")
for t in samples:
    fixed = convert_value(t)
    print(f"  {t!r}  ->  {fixed!r}")








############################################################################################################






#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_date_like_columns.py

- Reads CSV (sep=';') with dtype=str to avoid pandas auto-conversion.
- Target columns listed in COLUMNS_TO_FIX are cleaned of tokens like:
    "6.Haz", "5.Şub", "3.Eyl", "Mar.40", "AÄŸu.40", "Nis.35", "11.Mar", etc.
- Uses normalization + mojibake attempt + month-token mapping (Turkish + English).
- Replaces values in-place, standardizes decimal separator to dot, attempts to cast to float.
- Prints summary + sample conversions; writes OUTPUT_CSV.
"""

from pathlib import Path
import pandas as pd
import re
import unicodedata

# --------- CONFIG ----------
INPUT_CSV = "CAR_DATA_ORDER.csv"   # input file (sep=';')
OUTPUT_CSV = "CAR_DATA_ORDER_FIXED.csv"
SEP = ";"
ENC = "utf-8-sig"

# columns to fix (change to your exact column names if different)
COLUMNS_TO_FIX = [
    "PERFORMANS - 0-100 Km Hizlanma",
    "EKONOMI - Ortalama Yakit Tuketimi (100 km)",
    "EKONOMI - Sehir Ici Tuketim (100 km)",
    "EKONOMI - Sehir Disi Tuketim (100 km)",
]

# ---------- month mapping ----------
# includes english 3-letter and Turkish short forms
_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "oca": 1, "sub": 2, "şub": 2, "subat": 2, "mar": 3, "nis": 4, "may": 5,
    "haz": 6, "tem": 7, "agu": 8, "ağu": 8, "eyl": 9, "eki": 10, "kas": 11, "ara": 12,
    # some common variants
    "oc":1, "ocak":1, "şub.":2
}

# normalize month keys (strip diacritics)
def _norm_token(t: str) -> str:
    if t is None:
        return ""
    t = str(t).strip()
    # try to fix mojibake by re-decoding (common pattern: latin1-decoded utf-8 bytes)
    try:
        if "Ã" in t or "Ä" in t or "Â" in t:
            t_try = t.encode("latin1").decode("utf-8")
            # if decoding yields ascii letters or known month fragments, use it
            if any(ch.isalpha() for ch in t_try):
                t = t_try
    except Exception:
        pass
    # normalize unicode, remove combining marks
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.lower()
    # replace turkish special chars to ascii equivalents (already removed combining marks above)
    t = t.replace("ğ", "g").replace("ç", "c").replace("ş", "s").replace("ı", "i").replace("ö", "o").replace("ü", "u")
    # keep only letters
    t = re.sub(r'[^a-z]', '', t)
    return t

# quick lookup helper
_MONTH_MAP_NORMALIZED = { _norm_token(k): v for k, v in _MONTH_MAP.items() }

def month_token_to_num(tok: str):
    if not tok:
        return None
    key = _norm_token(tok)
    if key in _MONTH_MAP_NORMALIZED:
        return _MONTH_MAP_NORMALIZED[key]
    # try prefixes
    for L in (4, 3, 2):
        if key[:L] in _MONTH_MAP_NORMALIZED:
            return _MONTH_MAP_NORMALIZED[key[:L]]
    return None

# ---------- normalizers ----------
_RE_DAY_MONTH = re.compile(r'^\s*(\d{1,2})[.\-/\s]+([A-Za-zÇĞİŞÜÖçğışüöÃÄÂ]+)\s*$', re.UNICODE)
_RE_MONTH_NUM = re.compile(r'^\s*([A-Za-zÇĞİŞÜÖçğışüöÃÄÂ]+)[.\-/\s]+([0-9]+(?:[.,][0-9]+)?)\s*$', re.UNICODE)
_RE_NUMERIC = re.compile(r'^\s*[-+]?\d+(?:[.,]\d+)?\s*$')

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\ufeff", "")
    s = s.replace("\u200b", "")
    s = s.strip()
    # normalize weird dot-like separators to '.'
    s = re.sub(r'[·•·⋅•・]', '.', s)
    # normalize dashes
    s = re.sub(r'[–—−]', '-', s)
    # normalize unicode
    s = unicodedata.normalize("NFKC", s)
    return s

def convert_token_to_numeric_string(val: str):
    """
    Return standardized numeric string or original value if not convertible.
    Examples:
      "6.Haz" -> "6.6"
      "5.Şub" -> "5.2"
      "Mar.40" -> "3.40"
      "AÄŸu.40" -> "8.40" (via mojibake fix)
      "10.0" -> "10.0" (keeps)
    """
    if val is None:
        return val
    s = normalize_text(val)
    if s == "":
        return s
    # already numeric-ish -> replace comma by dot
    if _RE_NUMERIC.match(s):
        return s.replace(",", ".")
    # day.monthname -> day.monthnum (e.g. 11.Mar -> 11.3)
    m = _RE_DAY_MONTH.match(s)
    if m:
        day_tok, mon_tok = m.group(1), m.group(2)
        monnum = month_token_to_num(mon_tok)
        if monnum:
            return f"{int(day_tok)}.{monnum}"
    # monthname.number -> monthnum.number (Mar.40 -> 3.40)
    m2 = _RE_MONTH_NUM.match(s)
    if m2:
        mon_tok, num_tok = m2.group(1), m2.group(2)
        monnum = month_token_to_num(mon_tok)
        if monnum:
            # standardize numeric part to use dot
            num_tok = num_tok.replace(",", ".")
            return f"{monnum}.{num_tok}"
    # fallback: split on separators, try to find month token anywhere
    parts = re.split(r'[.\-/\s]+', s)
    for i, p in enumerate(parts):
        mn = month_token_to_num(p)
        if mn:
            # if month first and second numeric -> mn.num
            if i == 0 and len(parts) > 1 and re.match(r'^\d+(?:[.,]\d+)?$', parts[1]):
                return f"{mn}.{parts[1].replace(',', '.')}"
            # if month second and first numeric -> day.mn
            if i == 1 and re.match(r'^\d+$', parts[0]):
                return f"{int(parts[0])}.{mn}"
    # else return original (no change)
    return val

# ---------- main apply ----------
def main():
    p = Path(INPUT_CSV)
    if not p.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")
    df = pd.read_csv(p, sep=SEP, dtype=str, encoding=ENC)
    print(f"Read CSV: rows={len(df)}, cols={len(df.columns)}")

    total_replacements = 0
    per_col = {}
    examples = {}

    for col in COLUMNS_TO_FIX:
        if col not in df.columns:
            print(f"Warning: column not found -> {col!r}; skipping.")
            continue
        ser = df[col].astype(str).fillna("")
        new_vals = []
        col_count = 0
        col_examples = []
        for orig in ser.tolist():
            fixed = convert_token_to_numeric_string(orig)
            # if fixed differs and both not empty equal
            if (isinstance(orig, str) and orig.strip() != "") and (fixed != orig):
                col_count += 1
                if len(col_examples) < 8:
                    col_examples.append((orig, fixed))
            new_vals.append(fixed)
        # assign back (strings)
        df[col] = new_vals
        total_replacements += col_count
        per_col[col] = col_count
        examples[col] = col_examples

        # try cast to numeric (float) in-place if many conversions happened or numeric look majority
        # We'll attempt to convert column values to numeric and keep original if dtype doesn't change useful.
        coerced = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")
        num_non_na = coerced.notna().sum()
        # if there are more than zero numeric entries, replace with numbers where possible
        if num_non_na > 0:
            df[col] = coerced

    # summary
    print("\nTotal replacements:", total_replacements)
    for c, cnt in per_col.items():
        print(f"  {c}: {cnt}")
        if examples[c]:
            print("    examples:")
            for a, b in examples[c]:
                print(f"      {a!r}  ->  {b!r}")

    # write output
    outp = Path(OUTPUT_CSV)
    df.to_csv(outp, sep=SEP, index=False, encoding=ENC)
    print(f"\nWrote: {outp}  (rows={len(df)}, cols={len(df.columns)})")
    print("Done")

if __name__ == "__main__":
    main()
