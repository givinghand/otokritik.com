
from pathlib import Path
import pandas as pd
import unicodedata
import re

# ---------- CONFIG (fixed filenames) ----------
INPUT_CSV = "CAR_DATA_FINAL_4_SC.csv"
OUTPUT_CSV = "CAR_DATA_FINAL_5.csv"
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
    print(f"Wrote: {OUTPUT_CSV} (rows={len(df_fixed)}, cols={len(df_fixed.columns)})")

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

# ---------- CONFIG ----------
INPUT_CSV = "CAR_DATA_FINAL_4_SC.csv"
OUTPUT_CSV = "CAR_DATA_FINAL_5.csv"
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

def detect_delimiter(sample_line: str):
    """
    Choose delimiter heuristically using first non-empty line.
    Prefer ';' if appears more often than ',' otherwise use ','.
    """
    if sample_line is None:
        return ';'
    # count occurrences (ignore commas within quotes — but this is a heuristic)
    sc = sample_line.count(';')
    cc = sample_line.count(',')
    return ';' if sc >= cc else ','

# normalize string for matching (strip, lower, remove diacritics & non-alnum)
def normalize(colname: str) -> str:
    if colname is None:
        return ""
    s = str(colname).strip().lower()
    # replace turkish characters with ascii equivalents
    trans = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUa iuAIU".replace(" ", ""))  # simple
    # safer approach: remove diacritics
    import unicodedata
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # keep only alnum
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
        print(f"Error: input file not found: {inp}")
        return

    # read first non-empty line to choose delimiter
    with inp.open("r", encoding=ENCODING, newline='') as f:
        first_line = ""
        for _ in range(10):
            first_line = f.readline()
            if first_line:
                break
    delimiter = detect_delimiter(first_line)
    # reopen to read properly
    with inp.open("r", encoding=ENCODING, newline='') as f_in:
        reader = csv.reader(f_in, delimiter=delimiter)
        try:
            original_header = next(reader)
        except StopIteration:
            print("Error: input CSV is empty.")
            return
        original_header = [h.strip() for h in original_header]

        # build normalized index map
        idx_map = build_index_map(original_header)

        pick_indices = []   # each element: index in original header or None
        new_header = []
        missing_keys = []
        used_original_cols = set()

        for orig_key, new_name in MAPPING.items():
            matched_idx = None
            # prefer exact match (case-sensitive after stripping)
            if orig_key in original_header:
                matched_idx = original_header.index(orig_key)
                used_original_cols.add(original_header[matched_idx])
            else:
                # try normalized match
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

        # extras are original columns not matched (preserve order)
        extras = [c for c in original_header if c not in used_original_cols]

        final_header = list(new_header)
        if APPEND_EXTRAS:
            final_header.extend(extras)

        # Now read all rows and write output
    # Re-open input and output and do actual row processing (so header detection and data reading consistent)
    with inp.open("r", encoding=ENCODING, newline='') as f_in, outp.open("w", encoding=ENCODING, newline='') as f_out:
        reader = csv.reader(f_in, delimiter=delimiter)
        writer = csv.writer(f_out, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

        original_header = next(reader)  # we've already read once above but reopen ensures same pointer
        original_header = [h.strip() for h in original_header]

        # write new header
        writer.writerow(final_header)

        row_count = 0
        for row in reader:
            # preserve row even if shorter/longer than header
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
            row_count += 1

    # summary
    # number of columns in output
    out_cols = len(final_header)
    print(f"Output written: {outp!s}")
    if missing_keys:
        print("\nThe following mapping keys were NOT found in input header (these will be empty columns in output):")
        for k in missing_keys:
            print(" -", k)
    if extras:
        print("\nInput CSV contains extra columns not in mapping:")
        for e in extras:
            print(" -", e, ("(appended)" if APPEND_EXTRAS else "(not appended)"))

    print(f"\nDone. Rows written: {row_count}, Columns written: {out_cols}")
    # also print original counts
    # count original rows quickly
    orig_rows = 0
    with inp.open("r", encoding=ENCODING, newline='') as f:
        for _ in f:
            orig_rows += 1
    # subtract header line
    orig_rows = max(0, orig_rows - 1)
    print(f"Original rows (excluding header): {orig_rows}, Original columns: {len(original_header)}")

if __name__ == '__main__':
    main()
