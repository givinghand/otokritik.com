import pandas as pd
import unicodedata
import re
from pathlib import Path

INPUT = "car_data_missing_data_fix_7.csv"   # your input CSV
OUTPUT = "car_data_missing_data_fix_8.csv"  # output after modifications

# Columns to drop
DROP_COLS = [
    # Previous set
    "CAMLAR & AYNALAR - Acilir Tavan",
    "CAMLAR & AYNALAR - Arka Yan Cam Ayarlari",
    "CAMLAR & AYNALAR - Ic Dikiz Aynasi",
    "CAMLAR & AYNALAR - On Yan Cam Ayarlari",
    "CAMLAR & AYNALAR - Panoramik Cam Tavan",
    "CAMLAR & AYNALAR - Yan Dikiz Aynalari",
    "DIREKSIYON OZELLIKLERI - Direksiyon Ozellikleri",
    "DIREKSIYON OZELLIKLERI - Direksiyon Sistemi",
    "DIS GOVDE - Dis Govde Ozellikleri",
    "FRENLER & SUSPANSIYON - ABS Fren Sistemi",
    "FRENLER & SUSPANSIYON - Arka Suspansiyonlar",
    "FRENLER & SUSPANSIYON - Ayarlanir Suspansiyon",
    "FRENLER & SUSPANSIYON - Fren Destek Sistemleri",
    "FRENLER & SUSPANSIYON - On Suspansiyonlar",
    "GOSTERGELER & SENSORLER - Gostergeler & Bildirimler",
    "ISITMA & SOGUTMA - Torpido Ozellikleri",
    "KOLTUKLAR & IC DOSEME - Kol Dayama",
    "MUZIK & EGLENCE - Harici Giris - Cikis",
    "NAVIGASYON & BLUETOOTH - Bluetooth Telefon",
    "NAVIGASYON & BLUETOOTH - Navigasyon",
    "SANZIMAN & CEKIS SISTEMI - Cekis Kontrol Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Denge Kontrol Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Yorgunluk Tespit Sistemi",	
    "TEMEL OZELLIKLER - Engelli Bireyler Icin OTV Muafiyeti",
    "YOLCU EMNIYETI - Carpisma Testi (NCAP/ANCAP)",
    "YOLCU EMNIYETI - Hava Yastigi",
    "YOLCU EMNIYETI - Hava Yastigi Cesitleri",
    "YOLCU EMNIYETI - NCAP/ANCAP Yili",
    "KOLTUKLAR & IC DOSEME - Koltuk Isitma - Sogutma",

]

def normalize_str_for_match(s: str) -> str:
    """Normalize column name to ASCII lowercase alphanum for fuzzy matching."""
    if s is None:
        return ""
    # Unicode normalize -> remove diacritics -> lowercase
    s2 = unicodedata.normalize("NFKD", str(s))
    s2 = s2.encode("ascii", "ignore").decode("ascii")
    s2 = s2.lower()
    # remove non-alphanumeric characters
    s2 = re.sub(r'[^a-z0-9]', '', s2)
    return s2

def find_baslik_cols(columns):
    """Return list of columns that look like 'Baslık' in various encodings/variants."""
    baslik_matches = []
    for c in columns:
        norm = normalize_str_for_match(c)
        # look for 'baslik' (baslik is 'baslık' without diacritics)
        if "baslik" in norm or "basklik" in norm or (norm.startswith("bas") and "lk" in norm):
            baslik_matches.append(c)
    return baslik_matches

def main():
    p = Path(INPUT)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p.resolve()}")

    df = pd.read_csv(INPUT, dtype=str, low_memory=False)

    # 1) Drop columns that exist in the dataframe
    present_to_drop = [c for c in DROP_COLS if c in df.columns]
    if present_to_drop:
        df.drop(columns=present_to_drop, inplace=True)

    # 2) Find any 'Baslık' variants and rename them to BASLIK
    baslik_cols = find_baslik_cols(df.columns)
    renamed = {}
    if baslik_cols:
        # If multiple matches, pick the first as BASLIK and drop/rename others by appending suffix
        first = baslik_cols[0]
        renamed[first] = "BASLIK"
        # If there are additional similarly-named columns, rename them too but avoid duplicate names
        for extra in baslik_cols[1:]:
            # create a unique name
            newname = "BASLIK_" + re.sub(r'[^0-9a-zA-Z]', '', normalize_str_for_match(extra))[:10]
            # ensure uniqueness
            i = 1
            base_new = newname
            while newname in df.columns or newname in renamed.values():
                newname = f"{base_new}_{i}"
                i += 1
            renamed[extra] = newname
        df.rename(columns=renamed, inplace=True)

    # 3) Ensure BASLIK exists as a column. If not present but a column named exactly "Baslık" exists, rename it.
    if "BASLIK" not in df.columns:
        # already tried fuzzy match; if none found, try some exact alternatives
        alt_names = ["BaÅŸlÄ±k ", "BaÅŸlÄ±k", "BaÅŸlÄ±k", "Baslık", "Baslık", "Baslik", "BaÅŸlÄ±k"]
        for alt in alt_names:
            if alt in df.columns:
                df.rename(columns={alt: "BASLIK"}, inplace=True)
                renamed[alt] = "BASLIK"
                break

    # 4) Move BASLIK to be the first column if it exists
    if "BASLIK" in df.columns:
        cols = ["BASLIK"] + [c for c in df.columns if c != "BASLIK"]
        df = df[cols]

    # 5) Save output
    df.to_csv(OUTPUT, index=False)

    # 6) Print summary
    print("Done.")
    print(f"Input file: {p.resolve()}")
    print(f"Output file: {Path(OUTPUT).resolve()}")
    print(f"Columns dropped: {len(present_to_drop)}")
    if renamed:
        print("Columns renamed:")
        for old, new in renamed.items():
            print(f"  - '{old}' -> '{new}'")
    else:
        print("No 'Baslık' variants found/renamed.")
    print("Final column count:", len(df.columns))

if __name__ == "__main__":
    main()





###########################################################################
#CITROEN BERLINGO FIX
###########################################################################

#!/usr/bin/env python3
import pandas as pd

IN="car_data_missing_data_fix_8.csv"
OUT="car_data_missing_data_fix_8.csv"

df=pd.read_csv(IN, dtype=str, low_memory=False).fillna("")

# ensure cols exist
for c in ("MARKA","MODEL","TEMEL OZELLIKLER - Seri",
          "TEMEL OZELLIKLER - Arac Turu","TEMEL OZELLIKLER - Govde Tipi"):
    if c not in df.columns: df[c]=""

mask = (df["MARKA"].str.strip().str.lower()=="citroen") & \
       ( (df["MODEL"].str.lower()+ " " + df["TEMEL OZELLIKLER - Seri"].str.lower()).str.contains("berlingo") )

a_changes = ((df.loc[mask,"TEMEL OZELLIKLER - Arac Turu"].str.strip().str.lower()=="binek")).sum()
g_changes = ((df.loc[mask,"TEMEL OZELLIKLER - Govde Tipi"].str.strip().str.lower()=="mpv")).sum()
d_changes = ((df.loc[mask,"TEMEL OZELLIKLER - Segment"].str.strip().str.lower()=="mpv")).sum()

df.loc[mask & df["TEMEL OZELLIKLER - Arac Turu"].str.strip().str.lower().eq("binek"),
       "TEMEL OZELLIKLER - Arac Turu"] = "Ticari"
df.loc[mask & df["TEMEL OZELLIKLER - Govde Tipi"].str.strip().str.lower().eq("mpv"),
       "TEMEL OZELLIKLER - Govde Tipi"] = "Kombi"
df.loc[mask & df["TEMEL OZELLIKLER - Segment"].str.strip().str.lower().eq("mpv"),
       "TEMEL OZELLIKLER - Segment"] = "Hafif Ticari"

df.to_csv(OUT, index=False)
print(f"Done. Arac Turu changed: {a_changes}, Govde Tipi changed: {g_changes}. Output: {OUT}")



##############################################################
#REORDER
##############################################################


#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

INPUT  = "car_data_missing_data_fix_8.csv"  # change if needed
OUTPUT = "car_data_missing_data_fix_8.csv"

SORT_COLS = [
    "TEMEL OZELLIKLER - Arac Turu",
    "TEMEL OZELLIKLER - Govde Tipi",
    "TEMEL OZELLIKLER - Segment",
]

p = Path(INPUT)
if not p.exists():
    raise FileNotFoundError(f"Input not found: {p.resolve()}")

df = pd.read_csv(p, dtype=str, low_memory=False)

# Ensure sort columns exist
for c in SORT_COLS:
    if c not in df.columns:
        df[c] = ""

# Create lowercase keys to sort case-insensitively, use stable sort
temp_keys = [f"__s{i}" for i, _ in enumerate(SORT_COLS)]
for tk, col in zip(temp_keys, SORT_COLS):
    df[tk] = df[col].fillna("").astype(str).str.strip().str.lower()

df.sort_values(by=temp_keys, inplace=True, kind="mergesort")
df.drop(columns=temp_keys, inplace=True)

df.to_csv(OUTPUT, index=False)
print(f"Done. Saved sorted file: {Path(OUTPUT).resolve()}")



############################################################################

############################################################################

#!/usr/bin/env python3
import csv
import os

IN = "car_data_missing_data_fix_8.csv"
OUT = IN + ".tmp"

TARGET = {
    "Fiat Topolino 8.2 HP (4x2)",
    "Fiat Topolino Plus 8.2 HP (4x2)",
}
BASLIK_NAME = "BASLIK"
SEGMENT_NAME = "TEMEL OZELLIKLER - Segment"

# detect delimiter quickly
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(1024)
    dialect = csv.Sniffer().sniff(sample) if sample else csv.get_dialect("excel")

with open(IN, "r", encoding="utf-8", newline="") as fin, open(OUT, "w", encoding="utf-8", newline="") as fout:
    reader = csv.reader(fin, dialect)
    writer = csv.writer(fout, dialect)

    header = next(reader)
    # find columns (case-insensitive fallback)
    def find(colname):
        for i, h in enumerate(header):
            if h.strip().lower() == colname.lower():
                return i
        for i, h in enumerate(header):
            if colname.lower() in h.strip().lower():
                return i
        return None

    bi = find(BASLIK_NAME)
    si = find(SEGMENT_NAME)

    if bi is None:
        raise SystemExit("BASLIK column not found.")

    if si is None:
        # add segment column if missing
        header.append(SEGMENT_NAME)
        si = len(header) - 1

    writer.writerow(header)

    for row in reader:
        # ensure row has enough columns
        if len(row) <= si:
            row += [""] * (si + 1 - len(row))
        if row[bi].strip() in TARGET:
            row[si] = "A"
        writer.writerow(row)

# replace original file
os.replace(OUT, IN)
print("Done.")

############################################################################

############################################################################

#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

TARGET_PREFIX = "2021 Toyota Corolla 1.5 125 PS"
MTV_VALUE = "8421"
BASLIK_COL = "BASLIK"
MTV_COL = "TEMEL OZELLIKLER - Motorlu Tasit Vergisi"

# read and detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096)
    f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    reader = csv.reader(f, dialect)
    rows = list(reader)

if not rows:
    print("Input file is empty. Exiting.")
    sys.exit(0)

header = rows[0]
# find indices
try:
    bi = [h.strip() for h in header].index(BASLIK_COL)
except ValueError:
    print(f"Column '{BASLIK_COL}' not found in header. Exiting.")
    sys.exit(1)

if MTV_COL in header:
    mi = header.index(MTV_COL)
else:
    header.append(MTV_COL)
    mi = len(header) - 1

# process rows
out_rows = [header]
for r in rows[1:]:
    # ensure row length
    if len(r) <= mi:
        r = r + [""] * (mi + 1 - len(r))
    if r[bi].strip().startswith(TARGET_PREFIX):
        r[mi] = MTV_VALUE
    out_rows.append(r)

# write back using same dialect
with open(TMP, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, dialect)
    writer.writerows(out_rows)

os.replace(TMP, IN)
print("Done.")

############################################################################

############################################################################

#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

BASLIK_COL = "BASLIK"
CILINDIR_AD_COL = "MOTOR (Icten Yanmali) - Silindir Adedi"
CILINDIR_HACIM_COL = "MOTOR (Icten Yanmali) - Silindir Hacmi"

TARGET_PREFIX = "MG E-HS Plug-in Hybrid"
NEW_AD = "4"
NEW_HACIM = "1490 cc"

# read whole file, detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    txt = f.read(4096)
    f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(txt)
    except Exception:
        dialect = csv.excel
    reader = csv.reader(f, dialect)
    rows = list(reader)

if not rows:
    print("Input file empty. Exiting.")
    sys.exit(0)

header = rows[0]
# locate or create columns
def find_col(name):
    for i, h in enumerate(header):
        if h.strip().lower() == name.lower():
            return i
    for i, h in enumerate(header):
        if name.lower() in h.strip().lower():
            return i
    return None

bi = find_col(BASLIK_COL)
if bi is None:
    print("BASLIK column not found. Exiting.")
    sys.exit(1)

ai = find_col(CILINDIR_AD_COL)
hi = find_col(CILINDIR_HACIM_COL)

# if missing, append columns to header
if ai is None:
    header.append(CILINDIR_AD_COL)
    ai = len(header) - 1
if hi is None:
    header.append(CILINDIR_HACIM_COL)
    hi = len(header) - 1

out_rows = [header]

for r in rows[1:]:
    if len(r) <= max(bi, ai, hi):
        r = r + [""] * (max(bi, ai, hi) + 1 - len(r))
    baslik = r[bi].strip()
    if baslik.startswith(TARGET_PREFIX):
        r[ai] = NEW_AD
        r[hi] = NEW_HACIM
    out_rows.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, dialect)
    writer.writerows(out_rows)

os.replace(TMP, IN)
print("Done.")

############################################################################

############################################################################

#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

BASLIK_COL = "BASLIK"
TARGET_COL = "MOTOR (Icten Yanmali) - Silindir Hacmi"

# mapping: if BASLIK startswith key -> set value
MAP = {
    "2018 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "1500 cc",
    "2015 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "1500 cc",
    "2016 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "1500 cc",
    "2017 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "1500 cc",
    "2021 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Crosstar Executive": "1500 cc",
    "2021 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Executive": "1500 cc",
    "2022 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Crosstar Executive": "1500 cc",
    "2022 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Executive": "1500 cc",
    "2023 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Crosstar Executive": "1500 cc",
    "2023 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Executive": "1500 cc",
    "2020 Hyundai i20 1.0 T-GDI 48V MHEV 100 PS DCT Style Plus": "1000 cc",
    "2024 Renault Clio 1.6 E-Tech Full Hybrid 145 BG Techno Esprit Alpine": "1600 cc",
    "2017 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Cool": "1500 cc",
    "2017 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Spirit": "1500 cc",
    "2017 Toyota Yaris 1.5 Hybrid 100 PS e-CVT X-Trend": "1500 cc",
    "2018 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Cool": "1500 cc",
    "2018 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Spirit": "1500 cc",
    "2018 Toyota Yaris 1.5 Hybrid 100 PS e-CVT X-Trend": "1500 cc",
    "2019 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Cool": "1500 cc",
    "2019 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Spirit X-Trend": "1500 cc",
    "2020 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Cool": "1500 cc",
    "2020 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Spirit X-Trend": "1500 cc",
    "2020 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Dream": "1500 cc",
    "2020 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Flame": "1500 cc",
    "2020 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Passion": "1500 cc",
    "2021 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Dream": "1500 cc",
    "2021 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Flame": "1500 cc",
    "2021 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Passion": "1500 cc",
    "2022 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Dream": "1500 cc",
    "2022 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Flame": "1500 cc",
    "2022 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Passion": "1500 cc",
    "2023 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Dream": "1500 cc",
    "2023 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Flame": "1500 cc",
    "2023 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Passion": "1500 cc",
    "2015 Toyota Yaris 1.5 Hybrid 100 PS Cool": "1500 cc",
    "2015 Toyota Yaris 1.5 Hybrid 100 PS Spirit": "1500 cc",
    "2016 Toyota Yaris 1.5 Hybrid 100 PS Cool": "1500 cc",
    "2016 Toyota Yaris 1.5 Hybrid 100 PS Spirit": "1500 cc",
    "2022 Fiat Egea HB 1.5 T4 Hibrit 130 HP Otomatik Urban": "1500 cc",
    "2022 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik Active": "1000 cc",
    "2022 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik ST-Line": "1000 cc",
    "2022 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik Titanium": "1000 cc",
    "2023 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik Active": "1000 cc",
    "2023 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik ST-Line": "1000 cc",
    "2023 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik Titanium": "1000 cc",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Active Skypack": "1798 cc",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Active": "1798 cc",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Advance Skypack": "1798 cc",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Advance": "1798 cc",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Premium": "1798 cc",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Active Skypack": "1798 cc",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Active": "1798 cc",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Advance Skypack": "1798 cc",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Advance": "1798 cc",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Premium": "1798 cc",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Dream X-Pack": "1798 cc",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Dream": "1798 cc",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "1798 cc",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Flame": "1798 cc",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "1798 cc",
    "2022 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Dream X-Pack": "1798 cc",
    "2022 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Dream": "1798 cc",
    "2022 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "1798 cc",
    "2022 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Flame": "1798 cc",
    "2021 Volkswagen Golf 1.0 eTSI 110 PS DSG Life": "1000 cc",
    "2021 Volkswagen Golf 1.0 eTSI 110 PS DSG R-Line": "1000 cc",
    "2021 Volkswagen Golf 1.0 eTSI 110 PS DSG Style": "1000 cc",
    "2021 Volkswagen Golf 1.0 eTSI 150 PS DSG R-Line": "1000 cc",
    "2021 Volkswagen Golf 1.0 eTSI 150 PS DSG Style": "1000 cc",
    "2022 Volkswagen Golf 1.0 eTSI 110 PS DSG Life": "1000 cc",
    "2022 Volkswagen Golf 1.0 eTSI 110 PS DSG R-Line": "1000 cc",
    "2022 Volkswagen Golf 1.0 eTSI 110 PS DSG Style": "1000 cc",
    "2022 Volkswagen Golf 1.5 eTSI 150 PS DSG R-Line": "1000 cc",
    "2022 Volkswagen Golf 1.5 eTSI 150 PS DSG Style": "1000 cc",
    "2023 Volkswagen Golf 1.0 eTSI 110 PS DSG Life": "1000 cc",
    "2023 Volkswagen Golf 1.0 eTSI 110 PS DSG R-Line": "1000 cc",
    "2023 Volkswagen Golf 1.0 eTSI 110 PS DSG Style": "1000 cc",
    "2023 Volkswagen Golf 1.5 eTSI 150 PS DSG R-Line": "1500 cc",
    "2023 Volkswagen Golf 1.5 eTSI 150 PS DSG Style": "1500 cc",
    "2016 Porsche 918 Spyder Hibrit 4.6 887 HP PDK (4x4)": "4590 cc",
    "2022 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Easy": "1500 cc",
    "2022 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Lounge": "1500 cc",
    "2022 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Urban": "1500 cc",
    "2023 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Easy": "1500 cc",
    "2023 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Lounge": "1500 cc",
    "2023 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Urban": "1500 cc",
    "2018 Hyundai Ioniq Hybrid 1.6 GDI 141 PS DCT Elite Plus": "1590 cc",
    "2017 Hyundai Ioniq Hybrid 1.6 GDI 141 PS DCT Elite Plus": "1590 cc",
    "2021 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Elite": "999 cc",
    "2021 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Premium": "999 cc",
    "2021 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Elite": "1500 cc",
    "2021 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Premium": "1500 cc",
    "2022 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Elite": "999 cc",
    "2022 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Premium": "999 cc",
    "2022 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Elite": "1500 cc",
    "2022 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Premium": "1500 cc",
    "2023 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Elite": "999 cc",
    "2023 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Premium": "999 cc",
    "2023 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Elite": "1500 cc",
    "2023 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Premium": "1500 cc",
    "2023 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Sportline": "1500 cc",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "1798 cc",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "1798 cc",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame": "1798 cc",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "1798 cc",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion": "1798 cc",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Vision": "1798 cc",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "1798 cc",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "1798 cc",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame": "1798 cc",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "1798 cc",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion": "1798 cc",
    "2021 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "1798 cc",
    "2021 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "1798 cc",
    "2021 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame": "1798 cc",
    "2021 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "1798 cc",
    "2022 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "1798 cc",
    "2022 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "1798 cc",
    "2022 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame": "1798 cc",
    "2022 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "1798 cc",
    "2023 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream X-Pack": "1798 cc",
    "2023 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "1798 cc",
    "2023 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "1798 cc",
    "2023 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "1798 cc",
    "2019 Toyota Camry Hibrit 2.5 218 HP e-CVT Passion": "2499 cc",
    "2020 BMW 530i xDrive 2.0 252 BG Otomatik S.Ed.Luxury Line (4x4)": "1999 cc",
    "2021 BMW 530i xDrive 2.0 252 BG Otomatik S.Ed.Luxury Line (4x4)": "1999 cc",
    "2022 BMW 530i xDrive 2.0 252 BG Otomatik S.Ed.Luxury Line (4x4)": "1999 cc",
    "2023 BMW 530i xDrive 2.0 252 BG Otomatik Luxury Line (4x4)": "1999 cc",
    "2023 BMW 530i xDrive 2.0 252 BG Otomatik M Sport (4x4)": "1999 cc",
    "2020 Volvo S90 B6 Mild Hibrit 2.0 300 HP AWD Geartronic Inscription (4x4)": "1999 cc",
    "2020 Volvo S90 B6 Mild Hibrit 2.0 300 HP AWD Geartronic R-Design (4x4)": "1999 cc",
    "2019 Volvo S90 T8 Plug-in Hibrit 2.0 407 HP EAWD Geartronic Inscription (4x4)": "1999 cc",
    "2019 Volvo S90 T8 Plug-in Hibrit 2.0 407 HP EAWD Geartronic R-Design (4x4)": "1999 cc",
    "2020 Volvo S90 T8 Plug-in Hibrit 2.0 407 HP EAWD Geartronic Inscription (4x4)": "1999 cc",
    "2020 Volvo S90 T8 Plug-in Hibrit 2.0 407 HP EAWD Geartronic R-Design (4x4)": "1999 cc",
    "2015 Mercedes S 400 Hybrid 3.5 306 PS 7G-Ttronic": "3498 cc",
    "2020 Ford Puma 1.0 EcoBoost 125 PS Otomatik ST-Line (4x2)": "999 cc",
    "2020 Ford Puma 1.0 EcoBoost 125 PS Otomatik Style (4x2)": "999 cc",
    "2020 Ford Puma 1.0 EcoBoost 95 PS Style (4x2)": "999 cc",
    "2020 Ford Puma Hibrit 1.0 EcoBoost 155 PS ST-Line (4x2)": "999 cc",
    "2021 Ford Puma Hibrit 1.0 EcoBoost 155 PS ST-Line (4x2)": "999 cc",
    "2022 Ford Puma Hibrit 1.0 EcoBoost 155 PS Otomatik ST-Line (4x2)": "999 cc",
    "2021 Hyundai Kona 1.6 CRDI 48V MHEV 136 PS DCT Style (4x2)": "1599 cc",
    "2023 Renault Captur 1.3 Mild Hybrid 140 BG EDC Icon (4x2)": "1299 cc",
    "2023 Renault Captur 1.3 Mild Hybrid 140 BG EDC Touch Plus (4x2)": "1299 cc",
    "2023 Renault Captur 1.3 Mild Hybrid 155 BG EDC R.S.Line (4x2)": "1299 cc",
    "2024 Renault Austral 1.3 Mild Hybrid 160 HP Techno (4x2)": "1299 cc",
    "2024 Renault Austral 1.3 Mild Hybrid 160 HP Techno Esprit Alpine (4x2)": "1299 cc",
    "2024 Renault Duster 1.2 Mild Hybrid 130 HP Advanced (4x4)": "1199 cc",
    "2024 Renault Duster 1.2 Mild Hybrid 130 HP Techno (4x4)": "1199 cc",
    "2024 Renault Duster 1.6 E-Tech Full Hybrid 145 HP Evolution (4x2)": "1598 cc",
    "2024 Renault Duster 1.6 E-Tech Full Hybrid 145 HP Techno (4x2)": "1598 cc",
    "2019 Toyota RAV4 Hybrid 2.5 222 HP e-CVT Flame (4x4)": "2499 cc",
    "2019 Toyota RAV4 Hybrid 2.5 222 HP e-CVT Passion (4x4)": "2499 cc",
    "2019 Toyota RAV4 Hybrid 2.5 222 HP e-CVT Passion X-Pack (4x4)": "2499 cc",
    "2016 Toyota RAV4 2.5 Hybrid 197 PS Premium Plus (4x4)": "2499 cc",
    "2023 Nissan X-Trail 1.5 DIG-T 163 BG X-Tronic CVT Platinum Premium (4x2)": "1500 cc",
    "2023 Nissan X-Trail 1.5 DIG-T 163 BG X-Tronic CVT Skypack (4x2)": "1500 cc",
    "2018 Audi Q8 50 3.0 TDI 286 HP Quattro Tiptronic (4x4)": "3000 cc",
    "2017 BMW X5 xDrive40e iPerformance 2.0 313 BG Otomatik (4x4)": "1999 cc",
    "2019 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic Inscription (4x4)": "1999 cc",
    "2019 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic Momentum (4x4)": "1999 cc",
    "2019 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic R-Design (4x4)": "1999 cc",
    "2020 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic Inscription (4x4)": "1999 cc",
    "2020 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic Momentum (4x4)": "1999 cc",
    "2020 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic R-Design (4x4)": "1999 cc",
    "2020 Volvo XC90 B6 Mild Hibrit 2.0 300 HP Geartronic Inscription (4x4)": "1999 cc",
    "2020 Volvo XC90 B6 Mild Hibrit 2.0 300 HP Geartronic R-Design (4x4)": "1999 cc",
    "2017 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "1999 cc",
    "2017 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "1999 cc",
    "2017 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "1999 cc",
    "2018 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "1999 cc",
    "2018 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "1999 cc",
    "2018 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "1999 cc",
    "2019 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Excellence (4x4)": "1999 cc",
    "2019 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "1999 cc",
    "2019 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "1999 cc",
    "2019 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "1999 cc",
    "2020 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "1999 cc",
    "2020 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "1999 cc",
    "2015 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "1999 cc",
    "2016 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "1999 cc",
    "2016 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "1999 cc",
    "2016 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "1999 cc",
    "2020 Volvo XC40 B4 Mild Hibrit 2.0 197 HP AWD Geartronic Inscription (4x4)": "1999 cc",
    "2020 Volvo XC40 B4 Mild Hibrit 2.0 197 HP AWD Geartronic Momentum (4x4)": "1999 cc",
    "2020 Volvo XC40 B4 Mild Hibrit 2.0 197 HP AWD Geartronic R-Design (4x4)": "1999 cc",
    "2018 Mercedes GLC 350 e 2.0 320 BG 4MATIC 9G-Tronic AMG (4x4)": "1999 cc",
}

# read file & detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096)
    f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    sys.exit(0)

header = rows[0]
# find BASLIK column (case-insensitive)
def find_col(name):
    for i, h in enumerate(header):
        if h.strip().lower() == name.lower():
            return i
    for i, h in enumerate(header):
        if name.lower() in h.strip().lower():
            return i
    return None

bi = find_col(BASLIK_COL)
if bi is None:
    sys.exit("BASLIK column not found")

ti = find_col(TARGET_COL)
if ti is None:
    header.append(TARGET_COL)
    ti = len(header) - 1

out = [header]
for r in rows[1:]:
    if len(r) <= ti:
        r = r + [""] * (ti + 1 - len(r))
    baslik = r[bi].strip()
    for key, val in MAP.items():
        if baslik.startswith(key):
            r[ti] = val
            break
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)

os.replace(TMP, IN)
print("Done.")

############################################################################

############################################################################

#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

MARKA = "MARKA"
SERI = "TEMEL OZELLIKLER - Seri"
MODEL = "MODEL"
PUSK = "MOTOR (Icten Yanmali) - Yakit Puskurtme"

# detect delimiter and read
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Empty input, exiting."); sys.exit(0)

header = rows[0]
def find(name):
    for i,h in enumerate(header):
        if h.strip().lower() == name.lower(): return i
    for i,h in enumerate(header):
        if name.lower() in h.strip().lower(): return i
    return None

mi = find(MARKA)
si = find(SERI)
mo = find(MODEL)
pi = find(PUSK)

if mi is None:
    print("MARKA column not found. Exiting."); sys.exit(1)
if pi is None:
    header.append(PUSK); pi = len(header)-1

# build lookup: (marka, seri) and (marka, model) -> pusk value
by_seri = {}
by_model = {}
for r in rows[1:]:
    # pad
    if len(r) <= max(mi, si or 0, mo or 0, pi):
        r += [""] * (max(mi, si or 0, mo or 0, pi) + 1 - len(r))
    marka = r[mi].strip().lower()
    seri = r[si].strip().lower() if si is not None else ""
    model = r[mo].strip().lower() if mo is not None else ""
    p = r[pi].strip()
    if not marka: continue
    if p:
        if seri: by_seri.setdefault((marka, seri), p)
        if model: by_model.setdefault((marka, model), p)

# fill empty puskurtme using seri -> model priority
filled = 0
out = [header]
for r in rows[1:]:
    if len(r) <= pi:
        r += [""] * (pi + 1 - len(r))
    if not r[pi].strip():
        marka = r[mi].strip().lower()
        seri = r[si].strip().lower() if si is not None else ""
        model = r[mo].strip().lower() if mo is not None else ""
        val = None
        if seri and (marka, seri) in by_seri:
            val = by_seri[(marka, seri)]
        elif model and (marka, model) in by_model:
            val = by_model[(marka, model)]
        if val:
            r[pi] = val
            filled += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — filled {filled} puskurtme cells.")


############################################################################

############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

SRC = "MOTOR (Icten Yanmali) - Besleme Tipi"
TARGET1 = "MOTOR (Icten Yanmali) - Silindir Hacmi"
TARGET2 = "MOTOR (Icten Yanmali) - Yakit Puskurtme"
MATCH = "Elektrik"

# detect delimiter and read all rows
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input is empty. Exiting."); sys.exit(0)

header = rows[0]

def find(col):
    for i,h in enumerate(header):
        if h.strip() == col: return i
    for i,h in enumerate(header):
        if col.lower() in h.strip().lower(): return i
    return None

si = find(SRC)
if si is None:
    print(f"Source column '{SRC}' not found. Exiting."); sys.exit(1)

t1 = find(TARGET1)
t2 = find(TARGET2)
# append targets if missing
if t1 is None:
    header.append(TARGET1); t1 = len(header)-1
if t2 is None:
    header.append(TARGET2); t2 = len(header)-1

out = [header]
count = 0
for r in rows[1:]:
    if len(r) <= max(si, t1, t2):
        r += [""] * (max(si, t1, t2) + 1 - len(r))
    if r[si].strip() == MATCH:
        r[t1] = MATCH
        r[t2] = MATCH
        count += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — set {count} rows to '{MATCH}'.")



############################################################################
#MPV
############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"
COL_NAME = "TEMEL OZELLIKLER - Govde Tipi"

# detect delimiter and read all rows
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input file empty. Exiting.")
    sys.exit(0)

header = rows[0]
# find column index (case-insensitive or partial match)
def find_col(name):
    name_low = name.lower()
    for i,h in enumerate(header):
        if h.strip().lower() == name_low:
            return i
    for i,h in enumerate(header):
        if name_low in h.strip().lower():
            return i
    return None

ci = find_col(COL_NAME)
if ci is None:
    print(f"Column '{COL_NAME}' not found. Exiting.")
    sys.exit(1)

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= ci:
        r = r + [""] * (ci + 1 - len(r))
    val = r[ci].strip()
    if val:
        vlow = val.lower()
        # if value explicitly MPV/SUV or contains both mpv and suv -> set to MPV
        if "mpv/suv" == vlow or ("mpv" in vlow and "suv" in vlow):
            r[ci] = "MPV"
            changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)

os.replace(TMP, IN)
print(f"Done — updated {changed} rows in column '{COL_NAME}'.")


############################################################################
#sportback
############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"
COL = "TEMEL OZELLIKLER - Govde Tipi"
FROM = "sportback"
TO = "Sedan"

# read & detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]
def find_col(name):
    name_low = name.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == name_low:
            return i
    for i,h in enumerate(header):
        if name_low in h.strip().lower():
            return i
    return None

ci = find_col(COL)
if ci is None:
    print(f"Column '{COL}' not found. Exiting."); sys.exit(1)

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= ci:
        r = r + [""] * (ci + 1 - len(r))
    if r[ci].strip().lower() == FROM:
        r[ci] = TO
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — replaced {changed} occurrences of '{FROM}' with '{TO}'.")



############################################################################
#coupetosedan
############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

# Exact BASLIK values to change
TARGETS = {
"2015 Volkswagen CC 1.4 TSI BMT 160 PS DSG",
"2015 Volkswagen CC 2.0 TDI BMT 140 PS DSG",
"2015 Volkswagen CC 2.0 TDI BMT 177 PS DSG",
"2015 Volkswagen CC 2.0 TSI 211 PS DSG",
"2015 Volkswagen CC 1.4 TSI BMT 150 PS DSG Exclusive",
"2015 Volkswagen CC 1.4 TSI BMT 150 PS DSG Sportline",
"2015 Volkswagen CC 2.0 TDI BMT 150 PS DSG Sportline",
"2015 Volkswagen CC 2.0 TDI BMT 184 PS DSG Exclusive",
"2015 Volkswagen CC 2.0 TDI BMT 184 PS DSG Sportline",
"2016 Volkswagen CC 1.4 TSI BMT 150 PS DSG Exclusive",
"2016 Volkswagen CC 1.4 TSI BMT 150 PS DSG Sportline",
"2016 Volkswagen CC 2.0 TDI BMT 150 PS DSG Sportline",
"2016 Volkswagen CC 2.0 TDI BMT 184 PS DSG Exclusive",
"2016 Volkswagen CC 2.0 TDI BMT 184 PS DSG Sportline",
"2018 Mercedes CLA 180d 1.5 109 PS 7G-DCT AMG",
"2018 Mercedes CLA 180d 1.5 109 PS 7G-DCT Comfort",
"2018 Mercedes CLA 180d 1.5 109 PS 7G-DCT Urban",
"2016 Mercedes CLA 180d 1.5 109 PS 7G-DCT AMG",
"2016 Mercedes CLA 180d 1.5 109 PS 7G-DCT Comfort",
"2016 Mercedes CLA 180d 1.5 109 PS 7G-DCT Urban",
"2017 Mercedes CLA 180d 1.5 109 PS 7G-DCT AMG",
"2017 Mercedes CLA 180d 1.5 109 PS 7G-DCT Comfort",
"2017 Mercedes CLA 180d 1.5 109 PS 7G-DCT Urban",
"2018 Mercedes CLA 200 1.6 156 PS 7G-DCT AMG",
"2018 Mercedes CLA 200 1.6 156 PS 7G-DCT Comfort",
"2018 Mercedes CLA 200 1.6 156 PS 7G-DCT Urban",
"2016 Mercedes CLA 200 1.6 156 PS 7G-DCT AMG",
"2016 Mercedes CLA 200 1.6 156 PS 7G-DCT Comfort",
"2016 Mercedes CLA 200 1.6 156 PS 7G-DCT Urban",
"2017 Mercedes CLA 200 1.6 156 PS 7G-DCT AMG",
"2017 Mercedes CLA 200 1.6 156 PS 7G-DCT Comfort",
"2017 Mercedes CLA 200 1.6 156 PS 7G-DCT Urban",
}

COL_NAME = "TEMEL OZELLIKLER - Govde Tipi"
FROM = "Coupe"
TO = "Sedan"

# read file & detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]

def find_col(name):
    nl = name.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == nl: return i
    for i,h in enumerate(header):
        if nl in h.strip().lower(): return i
    return None

bi = find_col("BASLIK")
ci = find_col(COL_NAME)
if bi is None:
    print("BASLIK column not found. Exiting."); sys.exit(1)
if ci is None:
    # create column if missing
    header.append(COL_NAME)
    ci = len(header)-1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= max(bi, ci):
        r = r + [""] * (max(bi, ci) + 1 - len(r))
    baslik = r[bi].strip()
    if baslik in TARGETS:
        if r[ci].strip().lower() == FROM.lower():
            r[ci] = TO
            changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — changed {changed} rows from '{FROM}' to '{TO}'.")



############################################################################

############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

# Put the exact BASLIK strings you provided here
TARGETS = {
"2018 Fiat Doblo Panorama 1.6 MultiJet 120 HP Easy",
"2018 Fiat Doblo Panorama 1.6 MultiJet 120 HP Premio Plus",
"2018 Fiat Doblo Panorama 1.6 MultiJet 120 HP Safeline",
"2019 Fiat Doblo Panorama 1.6 MultiJet 120 HP Easy",
"2019 Fiat Doblo Panorama 1.6 MultiJet 120 HP Lounge (5 Koltuk)",
"2019 Fiat Doblo Panorama 1.6 MultiJet 120 HP Lounge (7 Koltuk)",
"2020 Fiat Doblo Panorama 1.6 MultiJet 120 HP Easy",
"2020 Fiat Doblo Panorama 1.6 MultiJet 120 HP Lounge (5K)",
"2020 Fiat Doblo Panorama 1.6 MultiJet 120 HP Lounge (7K)",
"2015 Fiat Doblo Panorama 1.6 MultiJet 105 HP Easy",
"2015 Fiat Doblo Panorama 1.6 MultiJet 105 HP Premio Plus",
"2015 Fiat Doblo Panorama 1.6 MultiJet 105 HP Premio",
"2016 Fiat Doblo Panorama 1.6 MultiJet 105 HP Easy",
"2016 Fiat Doblo Panorama 1.6 MultiJet 105 HP Safeline",
"2017 Fiat Doblo Panorama 1.6 MultiJet 105 HP Easy",
"2017 Fiat Doblo Panorama 1.6 MultiJet 105 HP Safeline",
"2018 Fiat Doblo Panorama Maxi 1.6 MultiJet 120 HP Easy",
"2015 Fiat Doblo Panorama Maxi 1.6 MultiJet 105 HP Easy",
"2016 Fiat Doblo Panorama Maxi 1.6 MultiJet 105 HP Easy",
"2017 Fiat Doblo Panorama Maxi 1.6 MultiJet 105 HP Easy",
"2018 Peugeot Partner Tepee Binek 1.6 BlueHDi 120 HP Active",
"2019 Fiat Fiorino Combi 1.3 Mjet 95 Pop",
"2019 Fiat Fiorino Combi 1.3 Mjet 95 Premio",
"2019 Fiat Fiorino Combi 1.3 Mjet 95 Safeline",
"2019 Fiat Fiorino Combi 1.4 EKO 77 HP Pop",
"2019 Fiat Fiorino Combi 1.4 EKO 77 HP Premio",
"2019 Fiat Fiorino Combi 1.4 EKO 77 HP Safeline",
"2019 Fiat Fiorino Combi 1.4 Fire 77 HP Pop",
"2019 Fiat Fiorino Combi 1.4 Fire 77 HP Premio",
"2019 Fiat Fiorino Combi 1.4 Fire 77 HP Safeline",
"2020 Fiat Fiorino Combi 1.3 Mjet 95 Pop",
"2020 Fiat Fiorino Combi 1.3 Mjet 95 Premio",
"2020 Fiat Fiorino Combi 1.3 Mjet 95 Safeline",
"2020 Fiat Fiorino Combi 1.3 Mjet 95 Urban",
"2020 Fiat Fiorino Combi 1.4 EKO 77 HP Pop",
"2020 Fiat Fiorino Combi 1.4 EKO 77 HP Premio",
"2020 Fiat Fiorino Combi 1.4 EKO 77 HP Safeline",
"2020 Fiat Fiorino Combi 1.4 Fire 77 HP Pop",
"2020 Fiat Fiorino Combi 1.4 Fire 77 HP Premio",
"2020 Fiat Fiorino Combi 1.4 Fire 77 HP Safeline",
"2021 Fiat Fiorino Combi 1.3 Mjet 95 Pop",
"2021 Fiat Fiorino Combi 1.3 Mjet 95 Premio",
"2021 Fiat Fiorino Combi 1.3 Mjet 95 Safeline",
"2021 Fiat Fiorino Combi 1.3 Mjet 95 Urban",
"2021 Fiat Fiorino Combi 1.4 EKO 77 HP Pop",
"2021 Fiat Fiorino Combi 1.4 EKO 77 HP Premio",
"2021 Fiat Fiorino Combi 1.4 EKO 77 HP Safeline",
"2021 Fiat Fiorino Combi 1.4 Fire 77 HP Pop",
"2021 Fiat Fiorino Combi 1.4 Fire 77 HP Premio",
"2021 Fiat Fiorino Combi 1.4 Fire 77 HP Safeline",
"2022 Fiat Fiorino Combi 1.3 Mjet 95 Pop",
"2022 Fiat Fiorino Combi 1.3 Mjet 95 Premio",
"2022 Fiat Fiorino Combi 1.3 Mjet 95 Safeline",
"2022 Fiat Fiorino Combi 1.4 EKO 77 HP Pop",
"2022 Fiat Fiorino Combi 1.4 EKO 77 HP Premio",
"2022 Fiat Fiorino Combi 1.4 EKO 77 HP Safeline",
"2022 Fiat Fiorino Combi 1.4 Fire 77 HP Pop",
"2022 Fiat Fiorino Combi 1.4 Fire 77 HP Premio",
"2022 Fiat Fiorino Combi 1.4 Fire 77 HP Safeline",
"2023 Fiat Fiorino Combi 1.3 Mjet 95 Pop",
"2023 Fiat Fiorino Combi 1.3 Mjet 95 Premio",
"2023 Fiat Fiorino Combi 1.3 Mjet 95 Safeline",
"2023 Fiat Fiorino Combi 1.4 EKO 77 HP Pop",
"2023 Fiat Fiorino Combi 1.4 EKO 77 HP Premio",
"2023 Fiat Fiorino Combi 1.4 EKO 77 HP Safeline",
"2023 Fiat Fiorino Combi 1.4 Fire 77 HP Pop",
"2023 Fiat Fiorino Combi 1.4 Fire 77 HP Premio",
"2023 Fiat Fiorino Combi 1.4 Fire 77 HP Safeline",
"2018 Fiat Fiorino Panorama 1.3 Mjet 80 HP Otomatik Premio",
"2018 Fiat Fiorino Panorama 1.3 Mjet 95 HP Pop",
"2018 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio",
"2018 Fiat Fiorino Panorama 1.3 Mjet 95 HP Safeline",
"2019 Fiat Fiorino Panorama 1.3 Mjet 80 HP Otomatik Premio",
"2019 Fiat Fiorino Panorama 1.3 Mjet 95 HP Pop",
"2019 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio",
"2020 Fiat Fiorino Panorama 1.3 Mjet 95 HP Pop",
"2020 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio",
"2016 Fiat Fiorino Panorama 1.3 Mjet 75 HP Emotion",
"2016 Fiat Fiorino Panorama 1.3 Mjet 75 HP Pop",
"2016 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio",
"2017 Fiat Fiorino Panorama 1.3 Mjet 75 HP Emotion",
"2017 Fiat Fiorino Panorama 1.3 Mjet 75 HP Pop",
"2017 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio",
"Opel Combo Elektrik 136 HP Edition",
"2018 Ford Tourneo Connect 1.5 TDCI 100 PS Deluxe",
"2018 Ford Tourneo Connect 1.5 TDCI 120 PS Powershift Titanium",
"2018 Ford Tourneo Connect 1.5 TDCI 120 PS Titanium",
"2020 Ford Tourneo Connect 1.5 EcoBlue 120 PS Otomatik Titanium",
"2020 Ford Tourneo Connect 1.5 EcoBlue 120 PS Titanium",
"2021 Ford Tourneo Connect 1.5 EcoBlue 100 PS Deluxe",
"2021 Ford Tourneo Connect 1.5 EcoBlue 120 PS Otomatik Titanium",
"2021 Ford Tourneo Connect 1.5 EcoBlue 120 PS Titanium",
"2022 Ford Tourneo Connect 1.0 EcoBoost 100 PS Active",
"2022 Ford Tourneo Connect 1.5 EcoBlue 100 PS Deluxe",
"2022 Ford Tourneo Connect 1.5 EcoBlue 120 PS Otomatik Titanium",
"2022 Ford Tourneo Connect 1.5 EcoBlue 120 PS Titanium",
"2023 Ford Tourneo Connect 2.0 EcoBlue 122 PS Active (4x4)",
"2023 Ford Tourneo Connect 2.0 EcoBlue 122 PS Otomatik Active",
"2023 Ford Tourneo Connect 2.0 EcoBlue 122 PS Otomatik Titanium",
"2020 Ford Tourneo Connect 1.5 EcoBlue 100 PS Deluxe",
"2015 Ford Tourneo Connect 1.5 TDCI 120 PS Powershift Titanium",
"2015 Ford Tourneo Connect 1.6 L TDCI 115 PS Titanium",
"2015 Ford Tourneo Connect 1.6 L TDCI 95 PS Deluxe",
"2016 Ford Tourneo Connect 1.5 TDCI 120 PS Powershift Titanium",
"2016 Ford Tourneo Connect 1.6 TDCI 115 PS Titanium",
"2016 Ford Tourneo Connect 1.6 TDCI 95 PS Deluxe",
"2017 Ford Tourneo Connect 1.5 TDCI 120 PS Powershift Titanium",
"2017 Ford Tourneo Connect 1.6 TDCI 115 PS Titanium",
"2017 Ford Tourneo Connect 1.6 TDCI 95 PS Deluxe",
"2014 Opel Zafira Tourer 1.4 140 HP Enjoy Active Prestij",
"2014 Opel Zafira Tourer 1.4 140 HP Otomatik Enjoy Active Prestij",
"2014 Opel Zafira Tourer 1.6 DTH 136 HP Enjoy Active Prestij",
"2014 Opel Zafira Tourer 1.6 DTH 136 HP Enjoy",
"2014 Opel Zafira Tourer 2.0 165 HP Otomatik Enjoy Active Prestij",
"2015 Opel Zafira Tourer 1.4 140 HP Enjoy Active Prestij",
"2015 Opel Zafira Tourer 1.4 140 HP Otomatik Enjoy Active Prestij",
"2015 Opel Zafira Tourer 1.6 DTH 136 HP Enjoy Active Prestij",
"2015 Opel Zafira Tourer 1.6 DTH 136 HP Enjoy",
"2016 Opel Zafira Tourer 1.4 140 HP Otomatik Enjoy Active Prestij",
"2016 Opel Zafira Tourer 1.6 Dizel 136 HP Enjoy Active Prestij"
}

# columns to set and their values
COL_ARAC_TURU = "TEMEL OZELLIKLER - Arac Turu"
COL_SEGMENT = "TEMEL OZELLIKLER - Segment"
VAL_ARAC_TURU = "Ticari"
VAL_SEGMENT = "Hafif Ticari"

# read & detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(8192); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]
def find_col(name):
    target = name.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == target:
            return i
    for i,h in enumerate(header):
        if target in h.strip().lower():
            return i
    return None

bi = find_col("BASLIK")
ai = find_col(COL_ARAC_TURU)
si = find_col(COL_SEGMENT)

# if target cols missing, append them
if ai is None:
    header.append(COL_ARAC_TURU); ai = len(header)-1
if si is None:
    header.append(COL_SEGMENT); si = len(header)-1
if bi is None:
    print("BASLIK column not found. Exiting."); sys.exit(1)

out = [header]
changed = 0
for r in rows[1:]:
    # pad row
    if len(r) <= max(bi, ai, si):
        r = r + [""] * (max(bi, ai, si) + 1 - len(r))
    baslik = r[bi].strip()
    if baslik in TARGETS:
        r[ai] = VAL_ARAC_TURU
        r[si] = VAL_SEGMENT
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows.")


############################################################################
#miniticari
############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

SERIS = {"fiorino","bipper tepee","bipper van","nemo","tourneo courier"}
SEG_COL_NAME = "TEMEL OZELLIKLER - Segment"
SERI_COL_NAME = "TEMEL OZELLIKLER - Seri"
NEW_VAL = "Mini Ticari"

with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]
def find(name):
    nl = name.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == nl: return i
    for i,h in enumerate(header):
        if nl in h.strip().lower(): return i
    return None

si = find(SERI_COL_NAME)
if si is None:
    print(f"Column '{SERI_COL_NAME}' not found. Exiting."); sys.exit(1)
ti = find(SEG_COL_NAME)
if ti is None:
    header.append(SEG_COL_NAME); ti = len(header)-1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= max(si, ti):
        r += [""] * (max(si, ti) + 1 - len(r))
    if r[si].strip().lower() in SERIS:
        r[ti] = NEW_VAL
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows to '{NEW_VAL}'.")


############################################################################
#tıcarıpıcupchange
############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

SERIS = {"x-class","l200","navara","cybertruck","hilux","amarok"}
SERI_COL = "TEMEL OZELLIKLER - Seri"
SEG_COL = "TEMEL OZELLIKLER - Segment"
NEW_VAL = "Pick-Up"

# read & detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]
def find(col):
    nl = col.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == nl: return i
    for i,h in enumerate(header):
        if nl in h.strip().lower(): return i
    return None

si = find(SERI_COL)
if si is None:
    print(f"Column '{SERI_COL}' not found. Exiting."); sys.exit(1)
ti = find(SEG_COL)
if ti is None:
    header.append(SEG_COL); ti = len(header)-1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= max(si, ti):
        r += [""] * (max(si, ti) + 1 - len(r))
    if r[si].strip().lower() in SERIS:
        r[ti] = NEW_VAL
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows to '{NEW_VAL}'.")



############################################################################

############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

GOVDE_COL = "TEMEL OZELLIKLER - Govde Tipi"
ARAC_TURU_COL = "TEMEL OZELLIKLER - Arac Turu"
MATCH = "mpv"
NEW = "SUV / PICK-UP"

# read & detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]
def find(col):
    nl = col.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == nl: return i
    for i,h in enumerate(header):
        if nl in h.strip().lower(): return i
    return None

gi = find(GOVDE_COL)
if gi is None:
    print(f"Column '{GOVDE_COL}' not found. Exiting."); sys.exit(1)
ai = find(ARAC_TURU_COL)
if ai is None:
    header.append(ARAC_TURU_COL); ai = len(header)-1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= max(gi, ai):
        r += [""] * (max(gi, ai) + 1 - len(r))
    if r[gi].strip().lower() == MATCH:
        r[ai] = NEW
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows.")



############################################################################

############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

MODEL_COL = "MODEL"
GOVDE_COL = "TEMEL OZELLIKLER - Govde Tipi"
TARGET_MODELS = {"tourneo connect", "zafira tourer"}
NEW_VALUE = "Kombi Van"

# read & detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]

def find(colname):
    key = colname.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == key:
            return i
    for i,h in enumerate(header):
        if key in h.strip().lower():
            return i
    return None

mi = find(MODEL_COL)
if mi is None:
    print("MODEL column not found. Exiting."); sys.exit(1)

gi = find(GOVDE_COL)
if gi is None:
    header.append(GOVDE_COL)
    gi = len(header) - 1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= max(mi, gi):
        r += [""] * (max(mi, gi) + 1 - len(r))
    model = r[mi].strip().lower()
    if model in TARGET_MODELS:
        r[gi] = NEW_VALUE
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows to '{NEW_VALUE}'.")



############################################################################

############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

MODEL_COL = "MODEL"
ARAC_TURU_COL = "TEMEL OZELLIKLER - Arac Turu"
GOVDE_COL = "TEMEL OZELLIKLER - Govde Tipi"
SEG_COL = "TEMEL OZELLIKLER - Segment"

TARGET_MODEL = "logan mcv"
VAL_ARAC_TURU = "SUV / PICK-UP"
VAL_GOVDE = "MPV"
VAL_SEGMENT = "M"

# read & detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]
def find(colname):
    key = colname.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == key: return i
    for i,h in enumerate(header):
        if key in h.strip().lower(): return i
    return None

mi = find(MODEL_COL)
if mi is None:
    print("MODEL column not found. Exiting."); sys.exit(1)

ai = find(ARAC_TURU_COL)
gi = find(GOVDE_COL)
si = find(SEG_COL)
# append missing target columns
if ai is None:
    header.append(ARAC_TURU_COL); ai = len(header)-1
if gi is None:
    header.append(GOVDE_COL); gi = len(header)-1
if si is None:
    header.append(SEG_COL); si = len(header)-1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= max(mi, ai, gi, si):
        r += [""] * (max(mi, ai, gi, si) + 1 - len(r))
    model = r[mi].strip().lower()
    if model == TARGET_MODEL:
        r[ai] = VAL_ARAC_TURU
        r[gi] = VAL_GOVDE
        r[si] = VAL_SEGMENT
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows for MODEL='{TARGET_MODEL}'.")



############################################################################

############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

MAP = {
    "2024 Tesla Model 3 283 HP (4x2)": "419 Nm",
    "2024 Tesla Model 3 Long Range AWD 498 HP (4x4)": "510 Nm",
    "2023 Tesla Model S 670 HP (4x4)": "842 Nm",
    "2023 Tesla Model S Plaid 1020 HP (4x4)": "1420 Nm",
    "2024 Tesla Cybertruck 600 HP (4x4)": "706 Nm",
    "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": "1396 Nm",
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "493 Nm",
    "2023 Tesla Model Y Performance 534 HP (4x4)": "660 Nm",
    "2023 Tesla Model Y Standart 299 HP (4x2)": "420 Nm",
    "2023 Tesla Model X 670 HP (4x4)": "1000 Nm",
    "2023 Tesla Model X Plaid 1020 HP (4x4)": "1450 Nm",
}

BASLIK_COL = "BASLIK"
TARGET_COL = "MOTOR (Elektrikli) - Azami Tork"

# detect delimiter & read
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]
# find indices
def find(col):
    key = col.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == key: return i
    for i,h in enumerate(header):
        if key in h.strip().lower(): return i
    return None

bi = find(BASLIK_COL)
ti = find(TARGET_COL)
if bi is None:
    print("BASLIK column not found. Exiting."); sys.exit(1)
if ti is None:
    header.append(TARGET_COL)
    ti = len(header) - 1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= ti:
        r = r + [""] * (ti + 1 - len(r))
    baslik = r[bi].strip()
    if baslik in MAP:
        r[ti] = MAP[baslik]
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows.")



############################################################################

############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

MAP = {
    "Fiat Topolino 8.2 HP (4x2)": "5.5 kWh",
    "Fiat Topolino Plus 8.2 HP (4x2)": "5.5 kWh",
    "BYD Han 510 HP (4x4)": "85.4 kWh",
    "2024 Tesla Cybertruck 600 HP (4x4)": "123 kWh",
    "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": "123 kWh",
    "2024 MG ZS EV Luxury 156 HP (4x2)": "50.3 kWh",
    "2024 Volvo C40 Recharge Ultimate 252 HP (4x2)": "82 kWh",
    "2024 Volvo C40 Recharge Ultimate 408 HP (4x4)": "78 kWh",
    "2024 Volvo XC40 Recharge P8 252 HP Ultimate (4x2)": "82.0 kWh",
    "2024 Volvo XC40 Recharge P8 408 HP Ultimate (4x4)": "79.0 kWh",
    "2024 Volvo EX90 408 HP (4x4)": "111 kWh",
}

BASLIK_COL = "BASLIK"
TARGET_COL = "MOTOR (Elektrikli) - Batarya Kapasitesi"

# detect delimiter & read
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]
# find column indices
def find(col):
    key = col.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == key: return i
    for i,h in enumerate(header):
        if key in h.strip().lower(): return i
    return None

bi = find(BASLIK_COL)
ti = find(TARGET_COL)

if bi is None:
    print("BASLIK column not found. Exiting."); sys.exit(1)
if ti is None:
    header.append(TARGET_COL)
    ti = len(header) - 1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= ti:
        r = r + [""] * (ti + 1 - len(r))
    baslik = r[bi].strip()
    if baslik in MAP:
        r[ti] = MAP[baslik]
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows.")



############################################################################

############################################################################


#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_8.csv"
TMP = IN + ".tmp"

MAP = {
    "Citroen Ami One Electric 8 HP (4x2)": "Lityum Iyon",
    "2024 Opel Corsa Elektrik 136 HP GS (4x2)": "Lityum Iyon",
    "2024 Citroen e-C4 136 HP Shine Bold (4x2)": "Lityum Iyon",
    "2024 Citroen e-C4 156 HP Shine Bold (4x2)": "Lityum Iyon",
    "2024 Citroen e-C4 X 136 HP Shine Bold (4x2)": "Lityum Iyon",
    "2024 Citroen e-C4 X 156 HP Shine Bold (4x2)": "Lityum Iyon",
    "2024 MG MG4 167 HP Comfort (4x2)": "Lityum Iyon (LFP)",
    "2024 MG MG4 204 HP Luxury (4x2)": "Lityum Iyon (NMC)",
    "2024 MG MG4 435 HP XPOWER (4x4)": "Lityum Iyon (NMC)",
    "2024 Opel Astra Elektrik 156 HP Ultimate": "Lityum Iyon",
    "Opel Combo Elektrik 136 HP Edition": "Lityum Iyon",
    "2024 Hyundai IONIQ 6 151 BG Progressive (4x2)": "Lityum Iyon",
    "2024 Hyundai IONIQ 6 325 BG Progressive (4x4)": "Lityum Iyon",
    "2024 Kia EV3 204 PS Otomatik Elegance St.Menzil (4x2)": "Lityum Iyon",
    "2024 Kia EV3 204 PS Otomatik Elegance Uz.Menzil (4x2)": "Lityum Iyon",
    "2024 Kia EV3 204 PS Otomatik GT-Line Uz.Menzil (4x2)": "Lityum Iyon",
    "2024 Kia EV3 204 PS Otomatik Prestige Uz.Menzil (4x2)": "Lityum Iyon",
    "2024 MG ZS EV Luxury 156 HP (4x2)": "Lityum Iyon (LFP)",
    "2024 Opel Mokka Elektrik 136 BG Ultimate (4x2)": "Lityum Iyon",
    "2024 Volvo EX30 272 HP (4x2)": "Lityum Iyon (LFP)",
    "2024 Kia Niro EV 204 PS Elegance (4x2)": "Lityum Iyon",
    "2024 Mercedes EQA 250+ 190 BG AMG+ (4x2)": "Lityum Iyon",
    "2024 Mercedes EQA 350 4MATIC 292 BG AMG+ (4x4)": "Lityum Iyon",
    "2024 Opel Grandland Elektrik 210 HP GS (4x2)": "Lityum Iyon",
    "2025 Tesla Model Y Long Range 340 HP (4x4)": "Lityum Iyon (NMC)",
    "2025 Tesla Model Y Long Range 514 HP (4x4)": "Lityum Iyon (NMC)",
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "Lityum Iyon (NMC)",
    "2023 Tesla Model Y Performance 534 HP (4x4)": "Lityum Iyon (NMC)",
    "2023 Tesla Model Y Standart 299 HP (4x2)": "Lityum Iyon (LFP)",
    "2024 Volvo C40 Recharge Ultimate 252 HP (4x2)": "Lityum Iyon",
    "2024 Volvo C40 Recharge Ultimate 408 HP (4x4)": "Lityum Iyon",
    "2024 Volvo XC40 Recharge P8 252 HP Ultimate (4x2)": "Lityum Iyon",
    "2024 Volvo XC40 Recharge P8 408 HP Ultimate (4x4)": "Lityum Iyon",
}

BASLIK_COL = "BASLIK"
TARGET_COL = "MOTOR (Elektrikli) - Batarya Tipi"

# read input
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

header = rows[0]

def find(col):
    key = col.strip().lower()
    for i,h in enumerate(header):
        if h.strip().lower() == key: return i
    for i,h in enumerate(header):
        if key in h.strip().lower(): return i
    return None

bi = find(BASLIK_COL)
ti = find(TARGET_COL)

if bi is None:
    print("BASLIK column not found. Exiting."); sys.exit(1)
if ti is None:
    header.append(TARGET_COL)
    ti = len(header) - 1

out = [header]
changed = 0
for r in rows[1:]:
    if len(r) <= ti:
        r = r + [""] * (ti + 1 - len(r))
    baslik = r[bi].strip()
    if baslik in MAP:
        r[ti] = MAP[baslik]
        changed += 1
    out.append(r)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    csv.writer(f, dialect).writerows(out)
os.replace(TMP, IN)
print(f"Done — updated {changed} rows.")



############################################################################

############################################################################


#!/usr/bin/env python3
import pandas as pd

IN = "car_data_missing_data_fix_8.csv"

df = pd.read_csv(IN, low_memory=False)

col_to_remove = "MOTOR (Elektrikli) - Menzil"

if col_to_remove in df.columns:
    df = df.drop(columns=[col_to_remove])
    df.to_csv(IN, index=False)
    print(f"Column removed and file saved as: {IN}")
else:
    print(f"Column '{col_to_remove}' not found in file.")



############################################################################
#FIX IF NEEDED ?????????????????????????????????????????
############################################################################


#!/usr/bin/env python3
import pandas as pd

IN = "car_data_missing_data_fix_8.csv"
OUT = "car_data_missing_data_fix_9.csv"

# Mapping of BASLIK -> Menzil
menzil_map = {
    "Citroen Ami One Electric 8 HP (4x2)": "75 km",
    "2024 Volvo C40 Recharge Ultimate 252 HP (4x2)": "580 km",
    "2024 Volvo C40 Recharge Ultimate 408 HP (4x4)": "551 km",
}

df = pd.read_csv(IN, low_memory=False)

col = "MOTOR (Elektrikli) - Menzil (WLTP - Birlesik)"

# Ensure column exists
if col not in df.columns:
    df[col] = None

# Update values
for baslik, menzil in menzil_map.items():
    df.loc[df["BASLIK"] == baslik, col] = menzil

df.to_csv(OUT, index=False)
print(f"Updated values added and file saved as: {OUT}")





############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################


#!/usr/bin/env python3
import pandas as pd

IN = "car_data_missing_data_fix_9.csv"
OUT = "car_data_missing_data_fix_10.csv"

# Your provided mapping
menzil_map = {
    "Fiat Topolino 8.2 HP (4x2)": "75 km",
    "Fiat Topolino Plus 8.2 HP (4x2)": "75 km",
    "2024 Fiat 600e 118 HP La Prima (4x2)": "400 km",
    "2024 Renault 5 E-Tech 150 HP (4x2)": "400 km",
    "2017 Renault ZOE 92 BG ZEN": "400 km",
    "2018 Renault ZOE 92 BG ZEN": "400 km",
    "2019 Renault ZOE 92 BG Life": "395 km",
    "2015 Renault ZOE 88 BG ZEN": "240 km",
    "2024 Renault ZOE E-Tech 135 BG Intense (4x2)": "395 km",
    "2024 MG MG4 167 HP Comfort (4x2)": "450 km",
    "2024 MG MG4 204 HP Luxury (4x2)": "435 km",
    "2024 MG MG4 435 HP XPOWER (4x4)": "385 km",
    "2024 Nissan Leaf 147 BG Otomatik": "270 km",
    "2024 Opel Astra Elektrik 156 HP Ultimate (4x2)": "418 km",
    "2024 Hyundai IONIQ 6 151 BG Progressive (4x2)": "614 km",
    "2024 Hyundai IONIQ 6 325 BG Progressive (4x4)": "583 km",
    "2024 BYD Seal 888 PS (4x4)": "480 km",
    "2015 BMW i3 170 BG Otomatik": "190 km",
    "2016 BMW i3 170 BG Otomatik": "190 km",
    "2017 BMW i3 170 BG Otomatik": "290 km",
    "2024 MINI Cooper SE 184 HP (4x2)": "402 km",
    "2024 BYD Seal 530 HP (4x4)": "520 km",
    "2024 Tesla Model 3 283 HP (4x2)": "513 km",
    "2024 Tesla Model 3 Long Range AWD 498 HP (4x4)": "629 km",
    "2024 Audi Q4 e-tron GT Quattro 530 BG (4x4)": "499 km",
    "2024 Audi Q4 e-tron 50 Quattro 299 BG (4x4)": "520 km",
    "2024 Mercedes EQB 250+ 190 BG AMG+ (4x2)": "536 km",
    "2024 Mercedes EQB 350 4MATIC 292 BG AMG+ (4x4)": "468 km",
    "2023 Tesla Model S 670 HP (4x4)": "634 km",
    "2023 Tesla Model S Plaid 1020 HP (4x4)": "600 km",
    "2024 Kia EV6 229 PS Prestige Long Range (4x2)": "528 km",
    "2024 Kia EV6 325 PS GT-Line Long Range (4x4)": "484 km",
    "2024 Kia EV9 384 PS GT-Line Long Range (4x4)": "505 km",
    "2024 Renault Megane E-Tech 130 HP Equilibre (4x2)": "300 km",
    "2024 Renault Megane E-Tech 220 HP Techno (4x4)": "470 km",
    "2024 Tesla Cybertruck 600 HP (4x4)": "547 km",
    "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": "515 km",
    "2024 Citroen e-C3 113 BG (4x2)": "320 km",
    "2024 MG ZS EV Luxury 156 HP (4x2)": "320 km",
    "2024 Opel Frontera Elektrik 113 HP Edition (4x2)": "300 km",
    "2024 Peugeot e-2008 156 HP GT Prime (4x2)": "406 km",
    "2024 Peugeot e-2008 156 HP Allure (4x2)": "406 km",
    "2024 Peugeot e-2008 156 HP GT (4x2)": "406 km",
    "2024 Volvo EX30 272 HP (4x2)": "480 km",
    "2024 Kia Niro EV 204 PS Elegance (4x2)": "460 km",
    "2024 Mercedes EQA 250+ 190 BG AMG+ (4x2)": "560 km",
    "2024 Mercedes EQA 350 4MATIC 292 BG AMG+ (4x4)": "497 km",
    "2024 Opel Grandland Elektrik 210 HP GS (4x2)": "700 km",
    "2025 Peugeot E-3008 210 HP (4x2)": "525 km",
    "2025 Peugeot E-3008 Allure 210 HP (4x2)": "525 km",
    "2025 Tesla Model Y Long Range 340 HP (4x4)": "600 km",
    "2025 Tesla Model Y Long Range 514 HP (4x4)": "565 km",
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "533 km",
    "2023 Tesla Model Y Performance 534 HP (4x4)": "514 km",
    "2023 Tesla Model Y Standart 299 HP (4x2)": "455 km",
    "2024 Volvo C40 Recharge Ultimate 252 HP (4x2)": "580 km",
    "2024 Volvo C40 Recharge Ultimate 408 HP (4x4)": "551 km",
    "2024 Tesla Model X 670 HP (4x4)": "576 km",
    "2023 Tesla Model X Plaid 1020 HP (4x4)": "543 km",
}

df = pd.read_csv(IN, low_memory=False)

col = "MOTOR (Elektrikli) - Menzil (WLTP - Sehir ici)"
if col not in df.columns:
    df[col] = None

for baslik, menzil in menzil_map.items():
    df.loc[df["BASLIK"] == baslik, col] = menzil

df.to_csv(OUT, index=False)
print(f"Values added. File saved as: {OUT}")



############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################



import csv
import os

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

data = {
    "2017 Renault ZOE 92 BG ZEN": "68 kW",
    "2018 Renault ZOE 92 BG ZEN": "68 kW",
    "2019 Renault ZOE 92 BG Life": "68 kW",
    "2015 Renault ZOE 88 BG ZEN": "65 kW",
    "2018 Nissan Leaf 147 BG Otomatik": "110 kW",
    "2018 BMW i3 170 BG Otomatik": "127 kW",
    "2015 BMW i3 170 BG Otomatik": "127 kW",
    "2016 BMW i3 170 BG Otomatik": "127 kW",
    "2017 BMW i3 170 BG Otomatik": "127 kW",
    "2024 Tesla Model 3 283 HP (4x2)": "211 kW",
    "2023 Tesla Model S 670 HP (4x4)": "499 kW",
    "2023 Tesla Model S Plaid 1020 HP (4x4)": "760 kW",
    "2024 MG ZS EV Luxury 156 HP (4x2)": "115 kW",
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "257 kW",
    "2023 Tesla Model Y Performance 534 HP (4x4)": "398 kW",
    "2023 Tesla Model Y Standart 299 HP (4x2)": "223 kW",
    "2023 Tesla Model X 670 HP (4x4)": "499 kW",
    "2023 Tesla Model X Plaid 1020 HP (4x4)": "760 kW",
}

with open(IN, newline='', encoding="utf-8") as f, open(TMP, "w", newline='', encoding="utf-8") as o:
    reader = csv.DictReader(f)
    # Create the writer with an extra column if it does not exist
    fieldnames = reader.fieldnames.copy()
    if "MOTOR (Elektrikli) - Motor Gucu (kW)" not in fieldnames:
        fieldnames.append("MOTOR (Elektrikli) - Motor Gucu (kW)")

    writer = csv.DictWriter(o, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        key = row["BASLIK"]
        if key in data:
            row["MOTOR (Elektrikli) - Motor Gucu"] = data[key]
        writer.writerow(row)

os.replace(TMP, IN)
print("Electric motor power updated successfully!")



############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################



import csv
import os

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

data = {
    "Citroen Ami One Electric 8 HP (4x2)": "10.0 kWh/100km",
    "2017 Renault ZOE 92 BG ZEN": "14.3 kWh/100km",
    "2018 Renault ZOE 92 BG ZEN": "17.2 kWh/100km",
    "2019 Renault ZOE 92 BG Life": "17.2 kWh/100km",
    "2015 Renault ZOE 88 BG ZEN": "14.6 kWh/100km",
    "2018 Nissan Leaf 147 BG Otomatik": "20.6 kWh/100km",
    "2024 Opel Astra Elektrik 156 HP Ultimate (4x2)": "14.9 kWh/100km",
    "2018 BMW i3 170 BG Otomatik": "13.1 kWh/100km",
    "2015 BMW i3 170 BG Otomatik": "12.9 kWh/100km",
    "2016 BMW i3 170 BG Otomatik": "12.6 kWh/100km",
    "2017 BMW i3 170 BG Otomatik": "13.1 kWh/100km",
    "2024 BYD Seal 530 HP (4x4)": "18.2 kWh/100km",
    "2024 Tesla Model 3 283 HP (4x2)": "13.2 kWh/100km",
    "2024 Tesla Model 3 Long Range AWD 498 HP (4x4)": "14.0 kWh/100km",
    "BYD Han 510 HP (4x4)": "18.5 kWh/100km",
    "2023 Tesla Model S 670 HP (4x4)": "18.7 kWh/100km",
    "2023 Tesla Model S Plaid 1020 HP (4x4)": "18.7 kWh/100km",
    "2024 Renault Megane E-Tech 130 HP Iconic (4x2)": "15.5 kWh/100km",
    "2024 Renault Megane E-Tech 220 HP Techno (4x2)": "16.1 kWh/100km",
    "2024 Tesla Cybertruck 600 HP (4x4)": "26.5 kWh/100km",
    "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": "27.7 kWh/100km",
    "2024 MG ZS EV Luxury 156 HP (4x2)": "17.3 kWh/100km",
    "2024 Peugeot E-2008 156 HP Active Prime (4x2)": "15.3 kWh/100km",
    "2024 Peugeot E-2008 156 HP Allure (4x2)": "15.3 kWh/100km",
    "2024 Peugeot E-2008 156 HP GT (4x2)": "15.3 kWh/100km",
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "16.9 kWh/100km",
    "2023 Tesla Model Y Performance 534 HP (4x4)": "17.3 kWh/100km",
    "2023 Tesla Model Y Standart 299 HP (4x2)": "15.7 kWh/100km",
    "2023 Tesla Model X 670 HP (4x4)": "20.9 kWh/100km",
    "2023 Tesla Model X Plaid 1020 HP (4x4)": "20.9 kWh/100km",
    "2024 Renault Megane E-Tech 220 HP Iconic (4x2)": "15.8 kWh/100km"

}

with open(IN, newline='', encoding="utf-8") as f, open(TMP, "w", newline='', encoding="utf-8") as o:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames.copy()
    if "MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)" not in fieldnames:
        fieldnames.append("MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)")

    writer = csv.DictWriter(o, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        key = row["BASLIK"]
        if key in data:
            row["MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)"] = data[key]
        writer.writerow(row)

os.replace(TMP, IN)
print("Updated MOTOR (Elektrikli) - Ortalama Tuketim (Elk.) successfully!")



############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################



import csv
import os

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

data = {
    "2018 Nissan Leaf 147 BG Otomatik": "144 km/s"
}

with open(IN, newline="", encoding="utf-8") as f, open(TMP, "w", newline="", encoding="utf-8") as o:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames.copy()
    if "PERFORMANS - Azami Hiz" not in fieldnames:
        fieldnames.append("PERFORMANS - Azami Hiz")

    writer = csv.DictWriter(o, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        key = row["BASLIK"]
        if key in data:
            row["PERFORMANS - Azami Hiz"] = data[key]
        writer.writerow(row)

os.replace(TMP, IN)
print("Updated PERFORMANS - Azami Hiz successfully!")


############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################



import csv

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

# Torque data to add
data = {
    "2018 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "570 Nm",
    "2024 Audi e-tron GT Quattro 530 BG (4x4)": "630 Nm",
    "2015 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "570 Nm",
    "2016 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "570 Nm",
    "2017 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "570 Nm",
    "Fiat Topolino 8.2 HP (4x2)": "45 Nm",
    "Fiat Topolino Plus 8.2 HP (4x2)": "45 Nm",
    "Citroen Ami One Electric 8 HP (4x2)": "40 Nm",
    "2025 BYD Dolphin 204 HP Comfort (4x2)": "310 Nm",
    "2025 BYD Dolphin 204 HP Design (4x2)": "310 Nm",
    "2024 Fiat 500e HB 118 HP La Prima (4x2)": "220 Nm",
    "2021 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Crosstar Executive": "253 Nm",
    "2021 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Executive": "253 Nm",
    "2022 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Crosstar Executive": "253 Nm",
    "2022 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Executive": "253 Nm",
    "2023 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Crosstar Executive": "253 Nm",
    "2023 Honda Jazz 1.5 i-MMD Hybrid 98 PS Otomatik Executive": "253 Nm",
    "2020 Hyundai i20 1.0 T-GDI 48V MHEV 100 PS DCT Style Plus": "172 Nm",
    "2014 Mitsubishi Space Star 1.2 CVT Invite": "106 Nm",
    "2014 Mitsubishi Space Star 1.2 MT Invite": "106 Nm",
    "2015 Mitsubishi Space Star 1.2 80 PS CVT Intense": "106 Nm",
    "2015 Mitsubishi Space Star 1.2 80 PS CVT Invite": "106 Nm",
    "2015 Mitsubishi Space Star 1.2 80 PS Invite": "106 Nm",
    "2016 Mitsubishi Space Star 1.2 80 PS CVT Intense": "106 Nm",
    "2016 Mitsubishi Space Star 1.2 80 PS CVT Intense": "106 Nm",
    "2024 Opel Corsa Elektrik 136 HP GS (4x2)": "260 Nm",
    "2024 Renault 5 E-Tech 150 HP (4x2)": "225 Nm",
    "2024 Renault Clio 1.6 E-Tech Full Hybrid 145 BG Techno Esprit Alpine": "205 Nm",
    "2017 Renault ZOE 92 BG ZEN": "220 Nm",
    "2018 Renault ZOE 92 BG ZEN": "225 Nm",
    "2019 Renault ZOE 92 BG Life": "225 Nm",
    "2015 Renault ZOE 88 BG ZEN": "220 Nm",
    "2024 Renault ZOE E-Tech 135 BG Intense (4x2)": "245 Nm",
    "2017 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Cool": "280 Nm",
    "2017 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Spirit": "280 Nm",
    "2017 Toyota Yaris 1.5 Hybrid 100 PS e-CVT X-Trend": "280 Nm",
    "2018 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Cool": "280 Nm",
    "2018 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Spirit": "280 Nm",
    "2018 Toyota Yaris 1.5 Hybrid 100 PS e-CVT X-Trend": "280 Nm",
    "2019 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Cool": "280 Nm",
    "2019 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Spirit X-Trend": "280 Nm",
    "2020 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Cool": "280 Nm",
    "2020 Toyota Yaris 1.5 Hybrid 100 PS e-CVT Spirit X-Trend": "280 Nm",
    "2020 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Dream": "261 Nm",
    "2020 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Flame": "261 Nm",
    "2020 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Passion": "261 Nm",
    "2021 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Dream": "261 Nm",
    "2021 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Flame": "261 Nm",
    "2021 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Passion": "261 Nm",
    "2022 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Dream": "261 Nm",
    "2022 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Flame": "261 Nm",
    "2022 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Passion": "261 Nm",
    "2023 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Dream": "261 Nm",
    "2023 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Flame": "261 Nm",
    "2023 Toyota Yaris 1.5 Hybrid 116 PS e-CVT Passion": "261 Nm",
    "2015 Toyota Yaris 1.5 Hybrid 100 PS Cool": "280 Nm",
    "2015 Toyota Yaris 1.5 Hybrid 100 PS Spirit": "280 Nm",
    "2016 Toyota Yaris 1.5 Hybrid 100 PS Cool": "280 Nm",
    "2016 Toyota Yaris 1.5 Hybrid 100 PS Spirit": "280 Nm",
    "2024 Citroen e-C4 136 HP Shine Bold (4x2)": "260 Nm",
    "2024 Citroen e-C4 156 HP Shine Bold (4x2)": "270 Nm",
    "2024 Citroen e-C4 X 136 HP Shine Bold (4x2)": "260 Nm",
    "2024 Citroen e-C4 X 156 HP Shine Bold (4x2)": "270 Nm",
    "2022 Fiat Egea HB 1.5 T4 Hibrit 130 HP Otomatik Urban": "240 Nm",
    "2022 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik Active": "210 Nm",
    "2022 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik ST-Line": "210 Nm",
    "2022 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik Titanium": "210 Nm",
    "2023 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik Active": "210 Nm",
    "2023 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik ST-Line": "210 Nm",
    "2023 Ford Focus HB 1.0 mHEV EcoBoost 125 PS Otomatik Titanium": "210 Nm",
    "2024 MG MG4 167 HP Comfort (4x2)": "250 Nm",
    "2024 MG MG4 204 HP Luxury (4x2)": "250 Nm",
    "2024 MG MG4 435 HP XPOWER (4x4)": "600 Nm",
    "2018 Nissan Leaf 147 BG Otomatik": "320 Nm",
    "2024 Opel Astra Elektrik 156 HP Ultimate (4x2)": "270 Nm",
    "2024 Peugeot E-308 156 HP GT (4x2)": "270 Nm",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Active Skypack": "349 Nm",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Active": "349 Nm",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Advance Skypack": "349 Nm",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Advance": "349 Nm",
    "2017 Toyota Auris 1.8 Hybrid 136 PS e-CVT Premium": "349 Nm",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Active Skypack": "349 Nm",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Active": "349 Nm",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Advance Skypack": "349 Nm",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Advance": "349 Nm",
    "2018 Toyota Auris 1.8 Hybrid 136 PS e-CVT Premium": "349 Nm",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Dream X-Pack": "305 Nm",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Dream": "305 Nm",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "305 Nm",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Flame": "305 Nm",
    "2020 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "305 Nm",
    "2022 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Dream X-Pack": "305 Nm",
    "2022 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Dream": "305 Nm",
    "2022 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "305 Nm",
    "2022 Toyota Corolla HB 1.8 Hybrid 122 PS e-CVT Flame": "305 Nm",
    "2021 Volkswagen Golf 1.0 eTSI 110 PS DSG Life": "200 Nm",
    "2021 Volkswagen Golf 1.0 eTSI 110 PS DSG R-Line": "200 Nm",
    "2021 Volkswagen Golf 1.0 eTSI 110 PS DSG Style": "200 Nm",
    "2021 Volkswagen Golf 1.0 eTSI 150 PS DSG R-Line": "250 Nm",
    "2021 Volkswagen Golf 1.0 eTSI 150 PS DSG Style": "250 Nm",
    "2022 Volkswagen Golf 1.0 eTSI 110 PS DSG Life": "200 Nm",
    "2022 Volkswagen Golf 1.0 eTSI 110 PS DSG R-Line": "200 Nm",
    "2022 Volkswagen Golf 1.0 eTSI 110 PS DSG Style": "200 Nm",
    "2022 Volkswagen Golf 1.5 eTSI 150 PS DSG R-Line": "250 Nm",
    "2022 Volkswagen Golf 1.5 eTSI 150 PS DSG Style": "250 Nm",
    "2023 Volkswagen Golf 1.0 eTSI 110 PS DSG Life": "200 Nm",
    "2023 Volkswagen Golf 1.0 eTSI 110 PS DSG R-Line": "200 Nm",
    "2023 Volkswagen Golf 1.0 eTSI 110 PS DSG Style": "200 Nm",
    "2023 Volkswagen Golf 1.5 eTSI 150 PS DSG R-Line": "250 Nm",
    "2023 Volkswagen Golf 1.5 eTSI 150 PS DSG Style": "250 Nm",
    "2024 Hyundai IONIQ 5 170 PS Progressive (4x2)": "350 Nm",
    "2024 Hyundai IONIQ 5 325 PS Progressive (4x4)": "605 Nm",
    "2024 MG Marvel R 288 PS (4x4)": "665 Nm",
    "2020 Volvo XC40 B4 Mild Hibrit 2.0 197 HP AWD Geartronic Inscription (4x4)": "300 Nm",
    "2020 Volvo XC40 B4 Mild Hibrit 2.0 197 HP AWD Geartronic Momentum (4x4)": "300 Nm",
    "2020 Volvo XC40 B4 Mild Hibrit 2.0 197 HP AWD Geartronic R-Design (4x4)": "300 Nm",
    "2018 BMW i3 170 BG Otomatik": "250 Nm",
    "2015 BMW i3 170 BG Otomatik": "250 Nm",
    "2016 BMW i3 170 BG Otomatik": "250 Nm",
    "2017 BMW i3 170 BG Otomatik": "250 Nm",
    "2024 Mini Cooper SE 184 PS (4x2)": "270 Nm",
    "Opel Combo Elektrik 136 HP Edition": "260 Nm",
    "2016 Porsche 918 Spyder Hibrit 4.6 887 HP PDK (4x4)": "1280 Nm",
    "2014 Mitsubishi Attrage 1.2 CVT Intense": "106 Nm",
    "2014 Mitsubishi Attrage 1.2 MT Intense": "106 Nm",
    "2015 Mitsubishi Attrage 1.2 80 PS CVT Intense Plus (Navigasyonlu)": "106 Nm",
    "2015 Mitsubishi Attrage 1.2 80 PS CVT Intense Plus": "106 Nm",
    "2015 Mitsubishi Attrage 1.2 80 PS Intense Plus (Navigasyonlu)": "106 Nm",
    "2015 Mitsubishi Attrage 1.2 80 PS Intense Plus": "106 Nm",
    "2016 Mitsubishi Attrage 1.2 80 PS CVT Intense Plus (Navigasyonlu)": "106 Nm",
    "2016 Mitsubishi Attrage 1.2 80 PS Intense Plus (Navigasyonlu)": "106 Nm",
    "2022 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Easy": "240 Nm",
    "2022 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Lounge": "240 Nm",
    "2022 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Urban": "240 Nm",
    "2023 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Easy": "240 Nm",
    "2023 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Lounge": "240 Nm",
    "2023 Fiat Egea 1.5 T4 Hibrit 130 HP Otomatik Urban": "240 Nm",
    "2018 Hyundai Ioniq Hybrid 1.6 GDI 141 PS DCT Elite Plus": "265 Nm",
    "2017 Hyundai Ioniq Hybrid 1.6 GDI 141 PS DCT Elite Plus": "265 Nm",
    "2021 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Elite": "200 Nm",
    "2021 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Premium": "200 Nm",
    "2021 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Elite": "250 Nm",
    "2021 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Premium": "250 Nm",
    "2022 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Elite": "200 Nm",
    "2022 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Premium": "200 Nm",
    "2022 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Elite": "250 Nm",
    "2022 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Premium": "250 Nm",
    "2023 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Elite": "200 Nm",
    "2023 Skoda Octavia 1.0 TSI E-Tec 110 PS DSG Premium": "200 Nm",
    "2023 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Elite": "250 Nm",
    "2023 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Premium": "250 Nm",
    "2023 Skoda Octavia 1.5 TSI E-Tec 150 PS ACT DSG Sportline": "250 Nm",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "305 Nm",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "305 Nm",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame": "305 Nm",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "305 Nm",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion": "305 Nm",
    "2019 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Vision": "305 Nm",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "305 Nm",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "305 Nm",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame": "305 Nm",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "305 Nm",
    "2020 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion": "305 Nm",
    "2021 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "305 Nm",
    "2021 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "305 Nm",
    "2021 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame": "305 Nm",
    "2021 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "305 Nm",
    "2022 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "305 Nm",
    "2022 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "305 Nm",
    "2022 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame": "305 Nm",
    "2022 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "305 Nm",
    "2023 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream X-Pack": "305 Nm",
    "2023 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Dream": "305 Nm",
    "2023 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Flame X-Pack": "305 Nm",
    "2023 Toyota Corolla 1.8 Hybrid 122 PS e-CVT Passion X-Pack": "305 Nm",
    "2024 BYD Seal 530 HP (4x4)": "670 Nm",
    "2024 Hyundai IONIQ 6 151 BG Progressive (4x2)": "350 Nm",
    "2024 Hyundai IONIQ 6 325 BG Progressive (4x4)": "605 Nm",
    "2018 Mazda 6 2.0 SKY-G 165 PS Otomatik Power Sense": "213 Nm",
    "2024 Tesla Model 3 283 HP (4x2)": "419 Nm",
    "2024 Tesla Model 3 Long Range AWD 498 HP (4x4)": "510 Nm",
    "2019 Toyota Camry Hibrit 2.5 218 HP e-CVT Passion": "423 Nm",
    "2024 Audi Q4 e-tron GT Quattro 530 BG (4x4)": "630 Nm",
    "2024 Audi RS e-tron GT Quattro 530 BG (4x4)": "830 Nm",
    "2020 BMW 530i xDrive 2.0 252 BG Otomatik S.Ed.Luxury Line (4x4)": "350 Nm",
    "2021 BMW 530i xDrive 2.0 252 BG Otomatik S.Ed.Luxury Line (4x4)": "350 Nm",
    "2022 BMW 530i xDrive 2.0 252 BG Otomatik S.Ed.Luxury Line (4x4)": "350 Nm",
    "2023 BMW 530i xDrive 2.0 252 BG Otomatik Luxury Line (4x4)": "350 Nm",
    "2023 BMW 530i xDrive 2.0 252 BG Otomatik M Sport (4x4)": "350 Nm",
    "BYD Han 510 HP (4x4)": "700 Nm",
    "2020 Volvo S90 B6 Mild Hibrit 2.0 300 HP AWD Geartronic Inscription (4x4)": "420 Nm",
    "2020 Volvo S90 B6 Mild Hibrit 2.0 300 HP AWD Geartronic R-Design (4x4)": "420 Nm",
    "2019 Volvo S90 T8 Plug-in Hibrit 2.0 407 HP EAWD Geartronic Inscription (4x4)": "640 Nm",
    "2019 Volvo S90 T8 Plug-in Hibrit 2.0 407 HP EAWD Geartronic R-Design (4x4)": "640 Nm",
    "2020 Volvo S90 T8 Plug-in Hibrit 2.0 407 HP EAWD Geartronic Inscription (4x4)": "640 Nm",
    "2020 Volvo S90 T8 Plug-in Hibrit 2.0 407 HP EAWD Geartronic R-Design (4x4)": "640 Nm",
    "2015 Mercedes S 400 Hybrid 3.5 306 PS 7G-Ttronic": "620 Nm",
    "2024 Mercedes EQB 250+ 190 BG AMG+ (4x2)": "385 Nm",
    "2024 Mercedes EQB 350 4MATIC 292 BG AMG+ (4x4)": "520 Nm",
    "2023 Tesla Model S 670 HP (4x4)": "842 Nm",
    "2023 Tesla Model S Plaid 1020 HP (4x4)": "1420 Nm",
    "2024 Cupra Formentor VZ 1.4 e-Hybrid 245 HP DSG 4Drive (4x4)": "400 Nm",
    "2024 Kia EV6 229 PS Prestige Long Range (4x2)": "350 Nm",
    "2024 Kia EV6 325 PS GT-Line Long Range (4x4)": "605 Nm",
    "2024 Kia EV6 585 PS GT Long Range (4x4)": "740 Nm",
    "2024 Renault Megane E-Tech 220 HP Iconic (4x2)": "300 Nm",
    "2024 Renault Megane E-Tech 220 HP Techno (4x2)": "300 Nm",
    "2024 Tesla Cybertruck 600 HP (4x4)": "706 Nm",
    "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": "1396 Nm",
    "2024 Dacia Spring 65 BG Extreme (4x2)": "113 Nm",
    "2025 Hyundai INSTER Advance 115 BG (4X2)": "147 Nm",
    "2024 Citroen e-C3 113 BG (4x2)": "120 Nm",
    "2020 Ford Puma 1.0 EcoBoost 125 PS Otomatik ST-Line (4x2)": "170 Nm",
    "2020 Ford Puma 1.0 EcoBoost 125 PS Otomatik Style (4x2)": "170 Nm",
    "2020 Ford Puma 1.0 EcoBoost 95 PS Style (4x2)": "170 Nm",
    "2020 Ford Puma Hibrit 1.0 EcoBoost 155 PS ST-Line (4x2)": "220 Nm",
    "2021 Ford Puma Hibrit 1.0 EcoBoost 155 PS ST-Line (4x2)": "220 Nm",
    "2022 Ford Puma Hibrit 1.0 EcoBoost 155 PS Otomatik ST-Line (4x2)": "220 Nm",
    "2021 Hyundai Kona 1.6 CRDI 48V MHEV 136 PS DCT Style (4x2)": "320 Nm",
    "2024 Kia EV3 204 PS Otomatik Elegance St.Menzil (4x2)": "283 Nm",
    "2024 Kia EV3 204 PS Otomatik Elegance Uz.Menzil (4x2)": "283 Nm",
    "2024 Kia EV3 204 PS Otomatik GT-Line Uz.Menzil (4x2)": "283 Nm",
    "2024 Kia EV3 204 PS Otomatik Prestige Uz.Menzil (4x2)": "283 Nm",
    "2024 MG ZS EV Luxury 156 HP (4x2)": "280 Nm",
    "2025 Opel Frontera Hybrid 1.2 136 HP Edition (4x2)": "230 Nm",
    "2025 Opel Frontera Hybrid 1.2 136 HP GS (4x2)": "230 Nm",
    "2025 Opel Frontera Elektrik 111 HP Edition (4x2)": "270 Nm",
    "2024 Opel Mokka Elektrik 136 BG Ultimate (4x2)": "260 Nm",
    "2024 Peugeot E-2008 156 HP Active Prime (4x2)": "260 Nm",
    "2024 Peugeot E-2008 156 HP Allure (4x2)": "260 Nm",
    "2024 Peugeot E-2008 156 HP GT (4x2)": "260 Nm",
    "2023 Renault Captur 1.3 Mild Hybrid 140 BG EDC Icon (4x2)": "260 Nm",
    "2023 Renault Captur 1.3 Mild Hybrid 140 BG EDC Touch Plus (4x2)": "260 Nm",
    "2023 Renault Captur 1.3 Mild Hybrid 155 BG EDC R.S.Line (4x2)": "270 Nm",
    "2017 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Advance (4x2)": "305 Nm",
    "2017 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Diamond (4x2)": "305 Nm",
    "2017 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Dynamic (4x2)": "305 Nm",
    "2017 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Advance (4x2)": "305 Nm",
    "2017 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Diamond (4x2)": "305 Nm",
    "2017 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Dynamic (4x2)": "305 Nm",
    "2018 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Advance (4x2)": "305 Nm",
    "2018 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Diamond (4x2)": "305 Nm",
    "2018 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Dynamic (4x2)": "305 Nm",
    "2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Advance (4x2)": "305 Nm",
    "2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Diamond (4x2)": "305 Nm",
    "2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Dynamic (4x2)": "305 Nm",
    "2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "305 Nm",
    "2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "305 Nm",
    "2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "305 Nm",
    "2020 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "305 Nm",
    "2020 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "305 Nm",
    "2020 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "305 Nm",
    "2021 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "305 Nm",
    "2021 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "305 Nm",
    "2021 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "305 Nm",
    "2022 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "305 Nm",
    "2022 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "305 Nm",
    "2022 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "305 Nm",
    "2023 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "305 Nm",
    "2023 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "305 Nm",
    "2023 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "305 Nm",
    "2016 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Advance (4x2)": "305 Nm",
    "2016 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Diamond (4x2)": "305 Nm",
    "2016 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Dynamic (4x2)": "305 Nm",
    "2022 Toyota Yaris Cross Hybrid 1.5 92 PS e-CVT Dream (4x2)": "261 Nm",
    "2022 Toyota Yaris Cross Hybrid 1.5 92 PS e-CVT Dream X-Pack (4x2)": "261 Nm",
    "2022 Toyota Yaris Cross Hybrid 1.5 92 PS e-CVT Flame X-Pack (4x2)": "261 Nm",
    "2022 Toyota Yaris Cross Hybrid 1.5 92 PS e-CVT Passion X-Pack (4x2)": "261 Nm",
    "2024 Volvo EX30 272 HP (4x2)": "343 Nm",
    "2024 BYD Atto 3 Design 201 HP (4x2)": "310 Nm",
    "2022 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Lounge": "240 Nm",
    "2022 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Street": "240 Nm",
    "2022 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Urban": "240 Nm",
    "2023 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Lounge": "240 Nm",
    "2023 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Street": "240 Nm",
    "2023 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Urban": "240 Nm",
    "2020 Ford Kuga Plug-in Hibrit 2.5 225 PS CVT ST-Line (4x2)": "200 Nm (engine base)",
    "2021 Ford Kuga Plug-in Hibrit 2.5 225 PS CVT ST-Line (4x2)": "200 Nm (engine base)",
    "2022 Ford Kuga Plug-in Hibrit 2.5 225 PS CVT ST-Line (4x2)": "200 Nm (engine base)",
    "2019 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "315 Nm",
    "2020 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "315 Nm",
    "2021 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "315 Nm",
    "2022 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "315 Nm",
    "2023 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "315 Nm",
    "2023 Hyundai Tucson 1.6 T-GDI HEV 230 PS Otomatik Elite Plus (4X4)": "350 Nm",
    "2018 Kia Niro Hibrit 1.6 141 PS DCT Cool (4x2)": "265 Nm",
    "2018 Kia Niro Hibrit 1.6 141 PS DCT Elegance (4x2)": "265 Nm",
    "2018 Kia Niro Hibrit 1.6 141 PS DCT Prestige (4x2)": "265 Nm",
    "2017 Kia Niro Hibrit 1.6 141 PS DCT Concept Plus (4x2)": "265 Nm",
    "2017 Kia Niro Hibrit 1.6 141 PS DCT Exclusive (4x2)": "265 Nm",
    "2017 Kia Niro Hibrit 1.6 141 PS DCT Premium (4x2)": "265 Nm",
    "2024 Kia Niro EV 204 PS Elegance (4x2)": "255 Nm",
    "2023 Kia Sportage 1.6 CRDI Mild Hybrid 136 HP DCT Cool (4x2)": "320 Nm",
    "2023 Kia Sportage 1.6 CRDI Mild Hybrid 136 HP DCT Elegance Konfor (4x2)": "320 Nm",
    "2023 Kia Sportage 1.6 CRDI Mild Hybrid 136 HP DCT Prestige (4x2)": "320 Nm",
    "2023 Kia Sportage 1.6 TGDI Mild Hybrid 150 HP DCT Cool (4x2)": "265 Nm",
    "2023 Kia Sportage 1.6 TGDI Mild Hybrid 150 HP DCT Elegance Konfor (4x2)": "265 Nm",
    "2023 Kia Sportage 1.6 TGDI Mild Hybrid 150 HP DCT Prestige (4x2)": "265 Nm",
    "2023 Kia Sportage 1.6 TGDI Mild Hybrid 230 HP Otomatik Prestige Smart (4x4)": "350 Nm",
    "2024 Mercedes EQA 250+ 190 BG AMG+ (4x2)": "385 Nm",
    "2024 Mercedes EQA 350 4MATIC 292 BG AMG+ (4x4)": "520 Nm",
    "MG E-HS Plug-in Hybrid Comfort 258 PS (4x2)": "600 Nm",
    "MG E-HS Plug-in Hybrid Luxury 258 PS (4x2)": "600 Nm",
    "2022 Nissan Qashqai 1.3 DIG-T 158 PS Tekna (4x2)": "270 Nm",
    "2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Designpack (4x2)": "270 Nm",
    "2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Platinum Premium (4x2)": "270 Nm",
    "2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Platinum Premium (4x4)": "270 Nm",
    "2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Skypack (4x2)": "270 Nm",
    "2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Skypack (4x4)": "270 Nm",
    "2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Tekna (4x2)": "270 Nm",
    "2025 Opel Grandland Elektrik 210 HP GS (4x2)": "340 Nm",
    "2025 Peugeot E-3008 GT 210 HP (4x2)": "343 Nm",
    "2025 Peugeot E-3008 Allure 210 HP (4x2)": "343 Nm",
    "2024 Renault Austral 1.2 E-Tech Full Hybrid 200 HP Techno Esprit Alpine (4x2)": "410 Nm",
    "2024 Renault Austral 1.3 Mild Hybrid 160 HP Techno (4x2)": "270 Nm",
    "2024 Renault Austral 1.3 Mild Hybrid 160 HP Techno Esprit Alpine (4x2)": "270 Nm",
    "2024 Renault Duster 1.2 Mild Hybrid 130 HP Advanced (4x4)": "230 Nm",
    "2024 Renault Duster 1.2 Mild Hybrid 130 HP Techno (4x4)": "230 Nm",
    "2024 Renault Duster 1.6 E-Tech Full Hybrid 145 HP Evolution (4x2)": "205 Nm (combined)",
    "2024 Renault Duster 1.6 E-Tech Full Hybrid 145 HP Techno (4x2)": "205 Nm (combined)",
    "2025 Tesla Model Y Long Range 340 HP (4x2)": "420 Nm",
    "2025 Tesla Model Y Long Range 514 HP (4x4)": "493 Nm",
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "493 Nm",
    "2023 Tesla Model Y Performance 534 HP (4x4)": "660 Nm",
    "2023 Tesla Model Y Standart 299 HP (4x2)": "420 Nm",
    "2024 Toyota Corolla Cross Hybrid 1.8 140 BG e-CVT Flame (4X2)": "327 Nm",
    "2024 Toyota Corolla Cross Hybrid 1.8 140 BG e-CVT Flame X-Pack (4X2)": "327 Nm",
    "2024 Toyota Corolla Cross Hybrid 1.8 140 BG e-CVT Passion (4X2)": "327 Nm",
    "2024 Toyota Corolla Cross Hybrid 1.8 140 BG e-CVT Passion X-Pack (4X2)": "327 Nm",
    "2019 Toyota RAV4 Hybrid 2.5 222 HP e-CVT Flame (4x4)": "397 Nm",
    "2019 Toyota RAV4 Hybrid 2.5 222 HP e-CVT Passion (4x4)": "397 Nm",
    "2019 Toyota RAV4 Hybrid 2.5 222 HP e-CVT Passion X-Pack (4x4)": "397 Nm",
    "2016 Toyota RAV4 2.5 Hybrid 197 PS Premium Plus (4x4)": "615 Nm",
    "2024 Volvo C40 Recharge Ultimate 252 HP (4x2)": "420 Nm",
    "2024 Volvo C40 Recharge Ultimate 408 HP (4x4)": "670 Nm",
    "2024 Volvo XC40 Recharge P8 252 HP Ultimate (4x2)": "420 Nm",
    "2024 Volvo XC40 Recharge P8 408 HP Ultimate (4x4)": "670 Nm",
    "2025 BYD Seal U DM-i PHEV 1.5 Design 218 HP (4x2)": "655 Nm",
    "2025 BYD Seal U EV Design 218 HP (4x2)": "310 Nm",
    "2023 Nissan X-Trail 1.5 DIG-T 163 BG X-Tronic CVT Platinum Premium (4x2)": "300 Nm",
    "2023 Nissan X-Trail 1.5 DIG-T 163 BG X-Tronic CVT Skypack (4x2)": "300 Nm",
    "2018 Audi Q8 50 3.0 TDI 286 HP Quattro Tiptronic (4x4)": "600 Nm",
    "2017 BMW X5 xDrive40e iPerformance 2.0 313 BG Otomatik (4x4)": "450 Nm",
    "2024 Volvo EX90 408 HP (4x4)": "770 Nm",
    "2019 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic Inscription (4x4)": "480 Nm",
    "2019 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic Momentum (4x4)": "480 Nm",
    "2019 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic R-Design (4x4)": "480 Nm",
    "2020 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic Inscription (4x4)": "480 Nm",
    "2020 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic Momentum (4x4)": "480 Nm",
    "2020 Volvo XC90 B5 Mild Hibrit 2.0 235 HP Geartronic R-Design (4x4)": "480 Nm",
    "2020 Volvo XC90 B6 Mild Hibrit 2.0 300 HP Geartronic Inscription (4x4)": "420 Nm",
    "2020 Volvo XC90 B6 Mild Hibrit 2.0 300 HP Geartronic R-Design (4x4)": "420 Nm",
    "2017 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "640 Nm",
    "2017 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "640 Nm",
    "2017 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "640 Nm",
    "2018 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "640 Nm",
    "2018 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "640 Nm",
    "2018 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "640 Nm",
    "2019 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Excellence (4x4)": "640 Nm",
    "2019 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "640 Nm",
    "2019 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "640 Nm",
    "2019 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "640 Nm",
    "2020 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "640 Nm",
    "2020 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "640 Nm",
    "2015 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "640 Nm",
    "2016 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Inscription (4x4)": "640 Nm",
    "2016 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic Momentum (4x4)": "640 Nm",
    "2016 Volvo XC90 T8 Plug-in Hibrit 2.0 407 HP Geartronic R-Design (4x4)": "640 Nm",
    "2023 Tesla Model X 670 HP (4x4)": "750 Nm",
    "2023 Tesla Model X Plaid 1020 HP (4x4)": "1020 Nm",
    "2018 Mercedes GLC 350 e 2.0 320 BG 4MATIC 9G-Tronic AMG (4x4)": "560 Nm"

}

with open(IN, newline="", encoding="utf-8") as f, open(TMP, "w", newline="", encoding="utf-8") as o:
    r = csv.DictReader(f)
    w = csv.DictWriter(o, fieldnames=r.fieldnames)
    w.writeheader()
    for row in r:
        if row["BASLIK"] in data:
            row["PERFORMANS - Azami Tork (Toplam)"] = data[row["BASLIK"]]
        w.writerow(row)


import os
os.replace(TMP, IN)

############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################



import csv

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

# Your new data as a dictionary: BASLIK -> Silindir Hacmi
data = {
"2018 Renault Clio 1.2 75 HP Joy": "1149 cc",
"2018 Renault Clio 1.2 75 HP Touch": "1149 cc",
"2019 Renault Clio 1.2 75 HP Joy": "1149 cc",
"2016 Renault Clio Sport Tourer 1.2 75 HP Joy": "1149 cc",
"2024 Cupra Formentor VZ 1.4 e-Hybrid 245 HP DSG 4Drive (4x4)": "1395 cc",
"2025 Opel Frontera Hybrid 1.2 136 HP Edition (4x2)": "1199 cc",
"2025 Opel Frontera Hybrid 1.2 136 HP GS (4x2)": "1199 cc",
"2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Advance (4x2)": "1798 cc",
"2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Diamond (4x2)": "1798 cc",
"2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Dynamic (4x2)": "1798 cc",
"2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "1798 cc",
"2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "1798 cc",
"2019 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "1798 cc",
"2020 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "1798 cc",
"2020 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "1798 cc",
"2020 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "1798 cc",
"2021 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "1798 cc",
"2021 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "1798 cc",
"2021 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "1798 cc",
"2022 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "1798 cc",
"2022 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "1798 cc",
"2022 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "1798 cc",
"2023 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Flame (4x2)": "1798 cc",
"2023 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion (4x2)": "1798 cc",
"2023 Toyota C-HR 1.8 Hybrid 122 PS e-CVT Passion X-Pack (4x2)": "1798 cc",
"2022 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Lounge": "1469 cc",
"2022 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Street": "1469 cc",
"2022 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Urban": "1469 cc",
"2023 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Lounge": "1469 cc",
"2023 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Street": "1469 cc",
"2023 Fiat Egea Cross 1.5 T4 Hibrit 130 HP Otomatik Urban": "1469 cc",
"2020 Ford Kuga Plug-in Hibrit 2.5 225 PS CVT ST-Line (4x2)": "2488 cc",
"2021 Ford Kuga Plug-in Hibrit 2.5 225 PS CVT ST-Line (4x2)": "2488 cc",
"2022 Ford Kuga Plug-in Hibrit 2.5 225 PS CVT ST-Line (4x2)": "2488 cc",
"2019 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "1993 cc",
"2020 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "1993 cc",
"2021 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "1993 cc",
"2022 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "1993 cc",
"2023 Honda CR-V 2.0 i-MMD Hybrid 184 PS E-CVT Executive+ (4x4)": "1993 cc",
"2023 Hyundai Tucson 1.6 T-GDI HEV 230 PS Otomatik Elite Plus (4X4)": "1598 cc",
"2023 Kia Sportage 1.6 CRDI Mild Hybrid 136 HP DCT Cool (4x2)": "1598 cc",
"2023 Kia Sportage 1.6 CRDI Mild Hybrid 136 HP DCT Elegance Konfor (4x2)": "1598 cc",
"2023 Kia Sportage 1.6 CRDI Mild Hybrid 136 HP DCT Prestige (4x2)": "1598 cc",
"2023 Kia Sportage 1.6 TGDI Mild Hybrid 150 HP DCT Cool (4x2)": "1598 cc",
"2023 Kia Sportage 1.6 TGDI Mild Hybrid 150 HP DCT Elegance Konfor (4x2)": "1598 cc",
"2023 Kia Sportage 1.6 TGDI Mild Hybrid 150 HP DCT Prestige (4x2)": "1598 cc",
"2023 Kia Sportage 1.6 TGDI Mild Hybrid 230 HP Otomatik Prestige Smart (4x4)": "1598 cc",
"2022 Nissan Qashqai 1.3 DIG-T 158 PS Tekna (4x2)": "1332 cc",
"2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Designpack (4x2)": "1332 cc",
"2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Platinum Premium (4x2)": "1332 cc",
"2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Platinum Premium (4x4)": "1332 cc",
"2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Skypack (4x2)": "1332 cc",
"2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Skypack (4x4)": "1332 cc",
"2022 Nissan Qashqai 1.3 DIG-T 158 PS X-Tronic CVT Tekna (4x2)": "1332 cc",
"2024 Renault Austral 1.2 E-Tech Full Hybrid 200 HP Techno Esprit Alpine (4x2)": "1199 cc",
"2024 Toyota Corolla Cross Hybrid 1.8 140 BG e-CVT Flame (4X2)": "1798 cc",
"2024 Toyota Corolla Cross Hybrid 1.8 140 BG e-CVT Flame X-Pack (4X2)": "1798 cc",
"2024 Toyota Corolla Cross Hybrid 1.8 140 BG e-CVT Passion (4X2)": "1798 cc",
"2024 Toyota Corolla Cross Hybrid 1.8 140 BG e-CVT Passion X-Pack (4X2)": "1798 cc",
"2025 BYD Seal U DM-i PHEV 1.5 Design 218 HP (4x2)": "1498 cc",
"2016 Dacia Logan MCV 1.2 75 BG Ambiance": "1149 cc",
"2015 Dacia Logan MCV 1.2 75 BG Ambiance": "1149 cc"
}

column_to_update = "MOTOR (Icten Yanmali) - Silindir Hacmi"
key_column = "BASLIK"

with open(IN, newline="", encoding="utf-8") as infile, \
     open(TMP, "w", newline="", encoding="utf-8") as outfile:
    
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()
    
    for row in reader:
        car_name = row[key_column].strip()
        if car_name in data:
            row[column_to_update] = data[car_name]
        writer.writerow(row)

print(f"Updated CSV saved to: {TMP}")


import os
os.replace(TMP, IN)



############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################




import csv

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

electric_columns = [
    "MOTOR (Elektrikli) - Azami Tork",
    "MOTOR (Elektrikli) - Batarya Kapasitesi",
    "MOTOR (Elektrikli) - Batarya Tipi",
    "MOTOR (Elektrikli) - Menzil (WLTP - Birlesik)",
    "MOTOR (Elektrikli) - Menzil (WLTP - Sehir Ici)",
    "MOTOR (Elektrikli) - Motor Gucu",
    "MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)",
    "MOTOR (Elektrikli) - Sarj Suresi"
]

with open(IN, newline="", encoding="utf-8") as infile, \
     open(TMP, "w", newline="", encoding="utf-8") as outfile:

    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()

    for row in reader:
        motor_type = row.get("TEMEL OZELLIKLER - Motor Tipi", "").strip()
        if motor_type in ["HEV (Benzinli & Elektrikli)", "MHEV (Yari Hibrit Sistem)", "PHEV (Prizden Sarjli HEV)"]:
            for col in electric_columns:
                row[col] = ""  # clear the cell
        writer.writerow(row)

print(f"Electric columns cleared for HEV/MHEV/PHEV cars. Temp CSV: {TMP}")

import os
os.replace(TMP, IN)


############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################



import csv

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

battery_data = {
    "2024 Opel Astra Elektrik 156 HP Ultimate (4x2)": "Lityum Iyon",
    "2025 Opel Grandland Elektrik 210 HP GS (4x2)": "Lityum Iyon",
    "2025 Tesla Model Y Long Range 340 HP (4x2)": "Lityum Iyon (NMC)"
}

with open(IN, newline="", encoding="utf-8") as infile, \
     open(TMP, "w", newline="", encoding="utf-8") as outfile:

    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()

    for row in reader:
        if row["BASLIK"] in battery_data:
            row["MOTOR (Elektrikli) - Batarya Tipi"] = battery_data[row["BASLIK"]]
        writer.writerow(row)


import os
os.replace(TMP, IN)

############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################





import csv

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

data = {
    "2024 Renault 5 E-Tech 150 HP (4x2)": "AC (11 kW) (%0 - %100) 4 sa 30 dk. | DC (100 kW) (%15 - %80) 30 dk.",
    "2017 Renault ZOE 92 BG ZEN": "AC (22 kW) (%0 - %100) 2 sa 40 dk. | DC (50 kW) (%0 - %80) 65 dk.",
    "2018 Renault ZOE 92 BG ZEN": "AC (22 kW) (%0 - %100) 3 sa 10 dk. | DC (50 kW) (%0 - %80) 65 dk.",
    "2019 Renault ZOE 92 BG Life": "AC (22 kW) (%0 - %100) 3 sa 10 dk. | DC (50 kW) (%0 - %80) 65 dk.",
    "2015 Renault ZOE 88 BG ZEN": "AC (22 kW) (%0 - %100) 2 sa",
    "2024 Citroen e-C4 136 HP Shine Bold (4x2)": "AC (7.4 kW) (%0 - %100) 7sa 30dk. | DC (100 kW) (%0 - %80) 30dk. | DC (50 kW) (%0 - %80) 55dk.",
    "2024 Citroen e-C4 156 HP Shine Bold (4x2)": "AC (7.4 kW) (%0 - %100) 7sa 30dk. | DC (100 kW) (%0 - %80) 30dk. | DC (50 kW) (%0 - %80) 55dk.",
    "2024 Citroen e-C4 X 136 HP Shine Bold (4x2)": "AC (7.4 kW) (%0 - %100) 7sa 30dk. | DC (100 kW) (%0 - %80) 30dk. | DC (50 kW) (%0 - %80) 55dk.",
    "2024 Citroen e-C4 X 156 HP Shine Bold (4x2)": "AC (7.4 kW) (%0 - %100) 7sa 30dk. | DC (100 kW) (%0 - %80) 30dk. | DC (50 kW) (%0 - %80) 55dk.",
    "2018 Nissan Leaf 147 BG Otomatik": "AC (6.6 kW) (%0 - %100) 7 sa | DC (50 kW) (%20 - %80) 40 - 60 dk.",
    "2015 BMW i3 170 BG Otomatik": "AC (7.4 kW) (%0 - %100) 4 sa | DC (50 kW) (%0 - %80) 30 dk.",
    "2016 BMW i3 170 BG Otomatik": "AC (7.4 kW) (%0 - %100) 4 sa | DC (50 kW) (%0 - %80) 30 dk.",
    "2017 BMW i3 170 BG Otomatik": "AC (7.4 kW) (%0 - %100) 4 sa 30 dk | DC (50 kW) (%0 - %80) 40 dk.",
    "2024 MINI Cooper SE 184 PS (4x2)": "AC (11.2 kW) (%0 - %100) 2sa 30dk.",
    "2024 Tesla Model 3 283 HP (4x2)": "AC (11 kW) (%0 - %100) 6 sa | DC (250 kW) (%10 - %80) 25 dk.",
    "2024 Tesla Model 3 Long Range AWD 498 HP (4x4)": "AC (11 kW) (%0 - %100) 8 sa | DC (250 kW) (%10 - %80) 27 dk.",
    "2023 Tesla Model S 670 HP (4x4)": "AC (11 kW) (%0 - %100) 10 sa 30 dk | DC (250 kW) (%10 - %80) 30 dk.",
    "2023 Tesla Model S Plaid 1020 HP (4x4)": "AC (11 kW) (%0 - %100) 10 sa 30 dk | DC (250 kW) (%10 - %80) 30 dk.",
    "2024 Tesla Cybertruck 600 HP (4x4)": "AC (11.5 kW) (%0 - %100) 12 sa | DC (250 kW) (%10 - %80) 30 dk.",
    "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": "AC (11.5 kW) (%0 - %100) 12 sa | DC (250 kW) (%10 - %80) 30 dk.",
    "2024 MG ZS EV Luxury 156 HP (4x2)": "DC (%0S - %80) 40dk. | DC (%30 - %80) 30dk.",
    "2024 Peugeot E-2008 156 HP Active Prime (4x2)": "AC (7.4 kW) (%0 - %100) 7.4sa. | AC 7.4 kW (%20 - %80) 4.4sa. | DC (%20 - %80) 30dk.",
    "2024 Peugeot E-2008 156 HP Allure (4x2)": "AC (7.4 kW) (%0 - %100) 7.4sa. | AC 7.4 kW (%20 - %80) 4.4sa. | DC (%20 - %80) 30dk.",
    "2024 Peugeot E-2008 156 HP GT (4x2)": "AC (7.4 kW) (%0 - %100) 7.4sa. | AC 7.4 kW (%20 - %80) 4.4sa. | DC (%20 - %80) 30dk.",
    "2025 Opel Grandland Elektrik 210 HP GS (4x2)": "DC (150 kW) %20-80 29dk.",
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "AC (11 kW) (%0 - %100) 8 sa | DC (250 kW) (%10 - %80) 27 dk.",
    "2023 Tesla Model Y Performance 534 HP (4x4)": "AC (11 kW) (%0 - %100) 8 sa | DC (250 kW) (%10 - %80) 27 dk.",
    "2023 Tesla Model Y Standart 299 HP (4x2)": "AC (11 kW) (%0 - %100) 6 sa | DC (250 kW) (%10 - %80) 25 dk.",
    "2023 Tesla Model X 670 HP (4x4)": "AC (11 kW) (%0 - %100) 10 sa 30 dk | DC (250 kW) (%10 - %80) 30 dk.",
    "2023 Tesla Model X Plaid 1020 HP (4x4)": "AC (11 kW) (%0 - %100) 10 sa 30 dk | DC (250 kW) (%10 - %80) 30 dk.",
}

with open(IN, newline='', encoding="utf-8") as f, open(TMP, "w", newline='', encoding="utf-8") as o:
    reader = csv.DictReader(f)
    writer = csv.DictWriter(o, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        if row["BASLIK"] in data:
            row["MOTOR (Elektrikli) - Sarj Suresi"] = data[row["BASLIK"]]
        writer.writerow(row)

import os
os.replace(TMP, IN)



############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################



import csv
import os

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

TESLA_DATA = {
    "2024 Tesla Model 3 283 HP (4x2)":        ("420 Nm", "60 kW/sa", "Lityum Iyon"),
    "2024 Tesla Model 3 Long Range AWD 498 HP (4x4)": ("493 Nm", "75 kW/sa", "Lityum Iyon"),
    "2023 Tesla Model S 670 HP (4x4)":        ("650 Nm", "100 kW/sa", "Lityum Iyon"),
    "2023 Tesla Model S Plaid 1020 HP (4x4)": ("1420 Nm", "100 kW/sa", "Lityum Iyon"),
    "2024 Tesla Cybertruck 600 HP (4x4)":     ("1000 Nm", "120 kW/sa", "Lityum Iyon"),
    "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": ("1396 Nm", "120 kW/sa", "Lityum Iyon"),
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": ("493 Nm", "75 kW/sa", "Lityum Iyon"),
    "2023 Tesla Model Y Performance 534 HP (4x4)":    ("660 Nm", "75 kW/sa", "Lityum Iyon"),
    "2023 Tesla Model Y Standart 299 HP (4x2)":       ("420 Nm", "57.5 kW/sa", "Lityum Iyon"),
    "2023 Tesla Model X 670 HP (4x4)":        ("750 Nm", "100 kW/sa", "Lityum Iyon"),
    "2023 Tesla Model X Plaid 1020 HP (4x4)": ("1020 Nm", "100 kW/sa", "Lityum Iyon"),
}

with open(IN, newline='', encoding="utf-8") as f, open(TMP, "w", newline='', encoding="utf-8") as o:
    reader = csv.DictReader(f)  # default delimiter is comma
    writer = csv.DictWriter(o, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        baslik = row.get("BASLIK")  # safer than row["BASLIK"]
        if baslik in TESLA_DATA:
            tork, kapasite, tipi = TESLA_DATA[baslik]
            row["MOTOR (Elektrikli) - Azami Tork"] = tork
            row["MOTOR (Elektrikli) - Batarya Kapasitesi"] = kapasite
            row["MOTOR (Elektrikli) - Batarya Tipi"] = tipi
        writer.writerow(row)

os.replace(TMP, IN)
print("Tesla missing data updated ✅")




############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################



#!/usr/bin/env python3
import csv, os, sys

IN = "car_data_missing_data_fix_10.csv"
TMP = IN + ".tmp"

DESIRED = [

    # Basic info
    "BASLIK", "MARKA", "MODEL", "TEMEL OZELLIKLER - Seri", "TEMEL OZELLIKLER - Donanim Paketi",
    "TEMEL OZELLIKLER - Model Yili", "TEMEL OZELLIKLER - Ait Oldugu Ulke",
    
    # Vehicle type
    "TEMEL OZELLIKLER - Arac Turu","TEMEL OZELLIKLER - Govde Tipi","TEMEL OZELLIKLER - Segment",
    "TEMEL OZELLIKLER - Motor Tipi","TEMEL OZELLIKLER - Motorlu Tasit Vergisi","TEMEL OZELLIKLER - Yakit Tipi",
    
    # Combustion engine
    "MOTOR (Icten Yanmali) - Besleme Tipi","MOTOR (Icten Yanmali) - Silindir Adedi",
    "MOTOR (Icten Yanmali) - Silindir Hacmi","MOTOR (Icten Yanmali) - Yakit Puskurtme",
    
    # Electric engine
    "MOTOR (Elektrikli) - Azami Tork","MOTOR (Elektrikli) - Batarya Garantisi",
    "MOTOR (Elektrikli) - Batarya Kapasitesi","MOTOR (Elektrikli) - Batarya Tipi",
    "MOTOR (Elektrikli) - Menzil","MOTOR (Elektrikli) - Menzil (WLTP - Birlesik)",
    "MOTOR (Elektrikli) - Menzil (WLTP - Sehir Ici)","MOTOR (Elektrikli) - Motor Gucu",
    "MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)","MOTOR (Elektrikli) - Sarj Suresi",
    
    # Performance
    "PERFORMANS - Azami Hiz","PERFORMANS - Azami Tork (Toplam)","PERFORMANS - Beygir Gucu (Toplam)",
    "PERFORMANS - 0 - 100 Km Hizlanma",
    
    # Weight & dimensions
    "AGIRLIK & OLCULER - Agirlik","AGIRLIK & OLCULER - Genislik",
    "AGIRLIK & OLCULER - Uzunluk","AGIRLIK & OLCULER - Yukseklik",
    
    # Trunk / cargo
    "BAGAJ OZELLIKLERI - Bagaj Hacmi (2 Koltuk)","BAGAJ OZELLIKLERI - Bagaj Hacmi (5 Koltuk)",
    
    # Body / doors
    "DIS GOVDE - Kapi Sayisi",
    
    # Tires & rims
    "LASTIK & JANT - Kesit Orani","LASTIK & JANT - Lastik Ebatlari","LASTIK & JANT - Taban Genisligi",
    "LASTIK & JANT - Jant Capi","LASTIK & JANT - Jant Tipi",
    
    # Brakes / suspension
    "FRENLER & SUSPANSIYON - Park Freni Tipi",
    
    # Transmission / drive system
    "SANZIMAN & CEKIS SISTEMI - Cekis","SANZIMAN & CEKIS SISTEMI - Cekis Kontrol Sistemi",
    "SANZIMAN & CEKIS SISTEMI - Sanziman Kademesi","SANZIMAN & CEKIS SISTEMI - Sanziman Ozellikleri",
    "SANZIMAN & CEKIS SISTEMI - Sanziman Turu",
    
    # Driver assistance / safety
    "SURUS DESTEK SISTEMLERI - Denge Kontrol Sistemi","SURUS DESTEK SISTEMLERI - Diferansiyel Kilidi",
    "SURUS DESTEK SISTEMLERI - Dur & Kalk (Stop & Start)","SURUS DESTEK SISTEMLERI - Hiz Sabitleme & Sinirlama",
    "SURUS DESTEK SISTEMLERI - Serit Takip Sistemi","SURUS DESTEK SISTEMLERI - Yokus Kalkis Destegi",
    
    # Fuel / emissions
    "YAKIT TUKETIMI & EMISYON - Cevre Standardi (Emisyon)","YAKIT TUKETIMI & EMISYON - Ortalama Emisyon",
    "YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km)","YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km/WLTP)",
    "YAKIT TUKETIMI & EMISYON - Sehir Disi Tuketim (100 km)","YAKIT TUKETIMI & EMISYON - Sehir Ici Tuketim (100 km)",
    "YAKIT TUKETIMI & EMISYON - Yakit Kapasitesi",
    
    # Passenger safety
    "YOLCU EMNIYETI - Anahtarsiz Sistem","YOLCU EMNIYETI - Hava Yastigi Adedi","YOLCU EMNIYETI - NCAP/ANCAP Puani",
    
    # Indicators / sensors
    "GOSTERGELER & SENSORLER - Far Sensoru","GOSTERGELER & SENSORLER - Lastik Basinc Sensoru",
    "GOSTERGELER & SENSORLER - Park Sensoru & Yardimi","GOSTERGELER & SENSORLER - Yagmur Sensoru",
    
    # Heating / cooling
    "ISITMA & SOGUTMA - Klima",
    
    # Seats / interior
    "KOLTUKLAR & IC DOSEME - Koltuk Dosemesi Tipi","KOLTUKLAR & IC DOSEME - Koltuk Sayisi",
    "KOLTUKLAR & IC DOSEME - On Yolcu Koltugu Ayarlari","KOLTUKLAR & IC DOSEME - Surucu Koltugu Ayarlari",
    
    # Lighting
    "LAMBALAR & AYDINLATMA - Far Tipi","LAMBALAR & AYDINLATMA - Sis Farlari"
]


# read input, detect delimiter
with open(IN, "r", encoding="utf-8", newline="") as f:
    sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    rows = list(csv.reader(f, dialect))

if not rows:
    print("Input empty. Exiting."); sys.exit(0)

input_header = rows[0]
# build map from header name -> first index
idx_map = {}
for i, h in enumerate(input_header):
    key = h.strip()
    if key not in idx_map:
        idx_map[key] = i

out_rows = []
# create new header exactly as DESIRED
out_rows.append(DESIRED)

for r in rows[1:]:
    # pad row to avoid index errors
    if len(r) < len(input_header):
        r = r + [""] * (len(input_header) - len(r))
    new_row = []
    for col in DESIRED:
        if col in idx_map:
            val = r[idx_map[col]] if idx_map[col] < len(r) else ""
        else:
            val = ""
        new_row.append(val)
    out_rows.append(new_row)

with open(TMP, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, dialect)
    writer.writerows(out_rows)

os.replace(TMP, IN)
print("Columns reordered. Wrote", len(out_rows)-1, "rows.")




############################################################################
#✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅❌❌✅✅
############################################################################


#!/usr/bin/env python3
import csv, sys

# File to check
CSV_FILE = "car_data_missing_data_fix_10.csv"

# Desired column order
DESIRED = [
    "BASLIK", "MARKA", "MODEL", "TEMEL OZELLIKLER - Seri", "TEMEL OZELLIKLER - Donanim Paketi",
    "TEMEL OZELLIKLER - Model Yili", "TEMEL OZELLIKLER - Ait Oldugu Ulke",
    "TEMEL OZELLIKLER - Arac Turu","TEMEL OZELLIKLER - Govde Tipi","TEMEL OZELLIKLER - Segment",
    "TEMEL OZELLIKLER - Motor Tipi","TEMEL OZELLIKLER - Motorlu Tasit Vergisi","TEMEL OZELLIKLER - Yakit Tipi",
    "MOTOR (Icten Yanmali) - Besleme Tipi","MOTOR (Icten Yanmali) - Silindir Adedi",
    "MOTOR (Icten Yanmali) - Silindir Hacmi","MOTOR (Icten Yanmali) - Yakit Puskurtme",
    "MOTOR (Elektrikli) - Azami Tork","MOTOR (Elektrikli) - Batarya Garantisi",
    "MOTOR (Elektrikli) - Batarya Kapasitesi","MOTOR (Elektrikli) - Batarya Tipi",
    "MOTOR (Elektrikli) - Menzil","MOTOR (Elektrikli) - Menzil (WLTP - Birlesik)",
    "MOTOR (Elektrikli) - Menzil (WLTP - Sehir Ici)","MOTOR (Elektrikli) - Motor Gucu",
    "MOTOR (Elektrikli) - Ortalama Tuketim (Elk.)","MOTOR (Elektrikli) - Sarj Suresi",
    "PERFORMANS - Azami Hiz","PERFORMANS - Azami Tork (Toplam)","PERFORMANS - Beygir Gucu (Toplam)",
    "PERFORMANS - 0 - 100 Km Hizlanma",
    "AGIRLIK & OLCULER - Agirlik","AGIRLIK & OLCULER - Genislik",
    "AGIRLIK & OLCULER - Uzunluk","AGIRLIK & OLCULER - Yukseklik",
    "BAGAJ OZELLIKLERI - Bagaj Hacmi (2 Koltuk)","BAGAJ OZELLIKLERI - Bagaj Hacmi (5 Koltuk)",
    "DIS GOVDE - Kapi Sayisi",
    "LASTIK & JANT - Kesit Orani","LASTIK & JANT - Lastik Ebatlari","LASTIK & JANT - Taban Genisligi",
    "LASTIK & JANT - Jant Capi","LASTIK & JANT - Jant Tipi",
    "FRENLER & SUSPANSIYON - Park Freni Tipi",
    "SANZIMAN & CEKIS SISTEMI - Cekis","SANZIMAN & CEKIS SISTEMI - Cekis Kontrol Sistemi",
    "SANZIMAN & CEKIS SISTEMI - Sanziman Kademesi","SANZIMAN & CEKIS SISTEMI - Sanziman Ozellikleri",
    "SANZIMAN & CEKIS SISTEMI - Sanziman Turu",
    "SURUS DESTEK SISTEMLERI - Denge Kontrol Sistemi","SURUS DESTEK SISTEMLERI - Diferansiyel Kilidi",
    "SURUS DESTEK SISTEMLERI - Dur & Kalk (Stop & Start)","SURUS DESTEK SISTEMLERI - Hiz Sabitleme & Sinirlama",
    "SURUS DESTEK SISTEMLERI - Serit Takip Sistemi","SURUS DESTEK SISTEMLERI - Yokus Kalkis Destegi",
    "YAKIT TUKETIMI & EMISYON - Cevre Standardi (Emisyon)","YAKIT TUKETIMI & EMISYON - Ortalama Emisyon",
    "YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km)","YAKIT TUKETIMI & EMISYON - Ortalama Y.Tuketimi (100 km/WLTP)",
    "YAKIT TUKETIMI & EMISYON - Sehir Disi Tuketim (100 km)","YAKIT TUKETIMI & EMISYON - Sehir Ici Tuketim (100 km)",
    "YAKIT TUKETIMI & EMISYON - Yakit Kapasitesi",
    "YOLCU EMNIYETI - Anahtarsiz Sistem","YOLCU EMNIYETI - Hava Yastigi Adedi","YOLCU EMNIYETI - NCAP/ANCAP Puani",
    "GOSTERGELER & SENSORLER - Far Sensoru","GOSTERGELER & SENSORLER - Lastik Basinc Sensoru",
    "GOSTERGELER & SENSORLER - Park Sensoru & Yardimi","GOSTERGELER & SENSORLER - Yagmur Sensoru",
    "ISITMA & SOGUTMA - Klima",
    "KOLTUKLAR & IC DOSEME - Koltuk Dosemesi Tipi","KOLTUKLAR & IC DOSEME - Koltuk Sayisi",
    "KOLTUKLAR & IC DOSEME - On Yolcu Koltugu Ayarlari","KOLTUKLAR & IC DOSEME - Surucu Koltugu Ayarlari",
    "LAMBALAR & AYDINLATMA - Far Tipi","LAMBALAR & AYDINLATMA - Sis Farlari"
]

# read header from file
with open(CSV_FILE, "r", encoding="utf-8", newline="") as f:
    reader = csv.reader(f)
    actual_header = next(reader)

# compare
mismatches = []
for i, col in enumerate(DESIRED):
    if i >= len(actual_header):
        mismatches.append(f"Missing column in file: '{col}'")
    elif actual_header[i].strip() != col.strip():
        mismatches.append(f"Column {i+1} mismatch: expected '{col}' but found '{actual_header[i]}'")

if mismatches:
    print("Column order check FAILED. Issues found:")
    for msg in mismatches:
        print("-", msg)
    input("Press Enter after reviewing issues...")
else:
    print("Column order check PASSED. Everything matches DESIRED order.")



############################################################################

############################################################################



import pandas as pd

# Input & output file paths
IN = "car_data_missing_data_fix_10.csv"
OUT = "car_data_missing_data_fix_11.csv"

# Read CSV
df = pd.read_csv(IN)

# Remove the columns if they exist
cols_to_remove = ["MOTOR (Elektrikli) - Batarya Garantisi", "MOTOR (Elektrikli) - Menzil"]
existing_cols = [c for c in cols_to_remove if c in df.columns]
if existing_cols:
    df = df.drop(columns=existing_cols)

# Save updated CSV
df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("Columns removed and file saved as:", OUT)

