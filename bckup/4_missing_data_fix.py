##################################################################################
#TEMEL OZELLIKLER - Ait Oldugu Ulke
##################################################################################

import pandas as pd

INPUT = "car_data_filled.csv"
OUTPUT = "car_data_missing_data_fix_1.csv"
BRAND_COL = "MARKA"
COUNTRY_COL = "TEMEL OZELLIKLER - Ait Oldugu Ulke"

# Read
df = pd.read_csv(INPUT, dtype=str, low_memory=False)

# Normalize strings and treat empty strings as missing
df[BRAND_COL] = df[BRAND_COL].astype(str).str.strip()
df[COUNTRY_COL] = df[COUNTRY_COL].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA})

# Build brand -> most common country mapping (using available non-empty values)
non_empty = df[df[COUNTRY_COL].notna()]
mapping = (
    non_empty.groupby(BRAND_COL)[COUNTRY_COL]
    .agg(lambda x: x.mode().iat[0] if not x.mode().empty else pd.NA)
    .to_dict()
)

# Fill missing country values using the brand mapping
df[COUNTRY_COL] = df[COUNTRY_COL].fillna(df[BRAND_COL].map(mapping))

# Write output
df.to_csv(OUTPUT, index=False)

print("Finished — output saved to", OUTPUT)


##################################################################################
#TEMEL OZELLIKLER - Motorlu Tasit Vergisi
##################################################################################

import pandas as pd
import re
import math

INPUT = "car_data_missing_data_fix_1.csv"
OUTPUT = "car_data_missing_data_fix_2.csv"
MOTOR_TYPE_COL = "TEMEL OZELLIKLER - Motor Tipi"
MTV_COL = "TEMEL OZELLIKLER - Motorlu Tasit Vergisi"
MODEL_YEAR_COL = "TEMEL OZELLIKLER - Model Yili"
CURRENT_YEAR = 2025

# Common possible electric motor power column names (will pick first match present)
CAND_PWR_COLS = [
    "MOTOR (Elektrikli) - Motor Gucu",
    "MOTOR (Elektrikli) - Motor Gucu ",
    "MOTOR (Elektrikli) - Motor Gucu(kW)",
    "MOTOR (Elektrikli) - Motor Gucu (kW)",
    "MOTOR (Elektrikli) - Motor Gucu(kW)",
    "MOTOR (Elektrikli) - Motor Gucu ",
    "MOTOR (Elektrikli) - Motor Gucu"
]

# 2025 electric car MTV table (I Sayılı Tarife) keyed by kW-band -> dict of age-bucket -> TL
# Age buckets: "1-3","4-6","7-11","12-15","16+"
EV_MTV_TABLE = {
    "<=70":    {"1-3":1208,  "4-6":843,   "7-11":470,   "12-15":355,  "16+":125},
    "70-85":   {"1-3":2105,  "4-6":1578,  "7-11":915,   "12-15":647,  "16+":248},
    "85-105":  {"1-3":3721,  "4-6":2906,  "7-11":1712,  "12-15":1042, "16+":403},
    "105-120": {"1-3":5864,  "4-6":4514,  "7-11":2653,  "12-15":1578, "16+":622},
    "120-150": {"1-3":8794,  "4-6":6384,  "7-11":3988,  "12-15":2382, "16+":942},
    "150-180": {"1-3":12263, "4-6":10667, "7-11":6664,  "12-15":3582, "16+":1315},
    "180-210": {"1-3":18676, "4-6":16804, "7-11":10122, "12-15":5051, "16+":1852},
    "210-240": {"1-3":29366, "4-6":25357, "7-11":14932, "12-15":6664, "16+":2653},
    ">=240":   {"1-3":48062, "4-6":36042, "7-11":21344, "12-15":9591, "16+":3721},
}

def find_power_col(cols):
    # try to find existing column among candidates, else try any column that contains 'motor' and 'kw' or 'guc'
    for c in CAND_PWR_COLS:
        if c in cols:
            return c
    for c in cols:
        lc = c.lower()
        if "motor" in lc and ("kw" in lc or "guc" in lc or "güç" in lc):
            return c
    # fallback: any column containing "elektr" and "guc"
    for c in cols:
        lc = c.lower()
        if "elektr" in lc and "guc" in lc:
            return c
    return None

def is_electric(motor_type):
    if pd.isna(motor_type):
        return False
    s = str(motor_type).lower()
    return ("elektr" in s) or ("bev" in s) or ("100% elektrik" in s)

def parse_kW(s):
    """Try to parse kW from a string. If HP/BG/hp present, convert to kW.
       Returns float kW or None."""
    if pd.isna(s):
        return None
    raw = str(s).strip()
    # remove spaces around slash or parentheses
    raw = raw.replace("\xa0"," ").strip()
    # look for kW explicitly
    m = re.search(r"(-?\d+[.,]?\d*)\s*[kK]\s*W", raw)
    if not m:
        m = re.search(r"(-?\d+[.,]?\d*)\s*kW", raw, flags=re.IGNORECASE)
    if m:
        num = m.group(1).replace(",", ".")
        try:
            return float(num)
        except:
            pass
    # look for "BG" (beygir) or "hp"
    m2 = re.search(r"(-?\d+[.,]?\d*)\s*(?:BG|bg|hp|HP)\b", raw)
    if m2:
        num = m2.group(1).replace(",", ".")
        try:
            hp = float(num)
            # convert metric hp (beygir) to kW: 1 kW = 1.35962 HP -> kW = hp / 1.35962
            return hp / 1.35962
        except:
            pass
    # otherwise try first numeric token and assume it's kW if reasonable (<5000)
    m3 = re.search(r"(-?\d+[.,]?\d*)", raw)
    if m3:
        num = m3.group(1).replace(",", ".")
        try:
            val = float(num)
            if val > 5000:  # unlikely kW, maybe Watt; bail out
                return None
            # if value looks like hp (>200), convert as hp -> kW
            if val > 300:  # extremely high kW unlikely; treat as hp
                return val / 1.35962
            return val
        except:
            return None
    return None

def age_bucket_from_model_year(model_year):
    try:
        y = int(float(model_year))
    except:
        return None
    age = CURRENT_YEAR - y + 1
    if age <= 0:
        age = 1
    if 1 <= age <= 3:
        return "1-3"
    if 4 <= age <= 6:
        return "4-6"
    if 7 <= age <= 11:
        return "7-11"
    if 12 <= age <= 15:
        return "12-15"
    return "16+"

def kW_band(k):
    if k is None:
        return None
    k = float(k)
    if k <= 70:
        return "<=70"
    if k <= 85:
        return "70-85"
    if k <= 105:
        return "85-105"
    if k <= 120:
        return "105-120"
    if k <= 150:
        return "120-150"
    if k <= 180:
        return "150-180"
    if k <= 210:
        return "180-210"
    if k <= 240:
        return "210-240"
    return ">=240"

# --- main ---
df = pd.read_csv(INPUT, dtype=str, low_memory=False)

# find power column
power_col = find_power_col(df.columns)
# if not found, set None (we'll still try to parse from common alt columns)
if power_col is None:
    power_col = None

filled = 0

# ensure columns exist
if MOTOR_TYPE_COL not in df.columns:
    df[MOTOR_TYPE_COL] = pd.NA
if MTV_COL not in df.columns:
    df[MTV_COL] = pd.NA
if MODEL_YEAR_COL not in df.columns:
    df[MODEL_YEAR_COL] = pd.NA

for idx, row in df.iterrows():
    motor_type = row.get(MOTOR_TYPE_COL, None)
    # only handle pure electric vehicles
    if not is_electric(motor_type):
        continue
    # skip if MTV already present (non-empty)
    existing = row.get(MTV_COL, None)
    if existing is not None and str(existing).strip() not in ("", "nan", "None", "NaN"):
        continue

    # try to get kW
    kW = None
    if power_col:
        kW = parse_kW(row.get(power_col))
    # fallback: try some other likely column names
    if kW is None:
        for c in df.columns:
            lc = c.lower()
            if "guc" in lc or "güç" in lc or "kw" in lc:
                kW = parse_kW(row.get(c))
                if kW is not None:
                    break
    if kW is None:
        # cannot determine power -> skip
        continue

    band = kW_band(kW)
    if band is None:
        continue

    age_bucket = age_bucket_from_model_year(row.get(MODEL_YEAR_COL))
    if age_bucket is None:
        # if model year missing, try to infer from other columns (not implemented) -> skip
        continue

    # lookup amount
    amt = EV_MTV_TABLE.get(band, {}).get(age_bucket)
    if amt is None:
        continue

    # write as integer TL (no decimals)
    df.at[idx, MTV_COL] = str(int(math.floor(amt + 0.5)))
    filled += 1

# save
df.to_csv(OUTPUT, index=False)
print("Done. EV MTVs filled:", filled)


##################################################################################
#MOTOR (Icten Yanmali) - Besleme Tipi
##################################################################################

import time
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from collections import Counter, defaultdict

INPUT = "car_data_missing_data_fix_2.csv"
OUTPUT = "car_data_missing_data_fix_3.csv"

COL_BRAND = "MARKA"
COL_MODEL = "MODEL"
COL_YEAR = "TEMEL OZELLIKLER - Model Yili"
COL_MOTOR_TYPE = "TEMEL OZELLIKLER - Motor Tipi"
COL_BESLEME = "MOTOR (Icten Yanmali) - Besleme Tipi"

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36")
TIMEOUT = 10
SLEEP = 0.8
MAX_LINKS = 6
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

# keywords -> normalized Turkish labels (expanded)
KEYWORDS_MAP = {
    # Turkish
    "direkt enjeksiyon": "Direkt Enjeksiyon",
    "direkt enjeksiyonlu": "Direkt Enjeksiyon",
    "direk enjeksiyon": "Direkt Enjeksiyon",
    "common rail": "Common Rail",
    "çok noktalı enjeksiyon": "Multi Point Injection",
    "multi point injection": "Multi Point Injection",
    "multipoint injection": "Multi Point Injection",
    "port enjeksiyon": "Multi Point Injection",
    "mpi": "Multi Point Injection",
    "gdi": "Direkt Enjeksiyon",
    "tsi": "Direkt Enjeksiyon",
    "tdi": "Common Rail",
    "tci": "Direkt Enjeksiyon",
    "pd": "Direkt Enjeksiyon",
    "twinport": "Multi Point Injection",
    "karbüratör": "Karburatör",
    "karburator": "Karburatör",
    "turbo besleme": "Turbo",
    "turbo": "Turbo",
    "kompressor": "Kompressor",
    "kompresör": "Kompressor",
    "pompa enjeksiyon": "Pompa Enjeksiyon",
    "pompa-enjeksiyon": "Pompa Enjeksiyon",
    "efi": "Enjeksiyon",
    "injektor": "Enjeksiyon",
    # english variants
    "direct injection": "Direkt Enjeksiyon",
    "port fuel injection": "Multi Point Injection",
    "fuel injection": "Enjeksiyon",
    "carburetor": "Karburatör",
    "turbocharged": "Turbo",
    "supercharger": "Kompressor",
    "common-rail": "Common Rail",
}

# lowercased keys for search
KEYWORDS = {k.lower(): v for k, v in KEYWORDS_MAP.items()}


def is_electric(motor_type):
    if pd.isna(motor_type):
        return False
    s = str(motor_type).lower()
    return ("elektr" in s) or ("bev" in s) or ("electric" in s)


def build_search_queries(brand, model, year, motor_type):
    """Return list of query strings with different suffixes/keywords to try."""
    base_parts = []
    for p in (brand, model, year, motor_type):
        if pd.isna(p):
            continue
        s = str(p).strip()
        if s:
            base_parts.append(s)
    base = " ".join(base_parts).strip()
    q_suffixes = ["besleme tipi", "besleme", "enjeksiyon", "fuel injection", "besleme sistemi", "injection", "besleme tipi motor"]
    queries = []
    if base:
        for suff in q_suffixes:
            queries.append(f"{base} {suff}")
        # also try without motor_type/year (less specific)
        parts2 = " ".join([x for x in [brand, model] if pd.notna(x) and str(x).strip()])
        if parts2 and parts2 != base:
            for suff in q_suffixes:
                queries.append(f"{parts2} {suff}")
    else:
        # fallback tiny query
        if brand and model:
            for suff in q_suffixes:
                queries.append(f"{brand} {model} {suff}")
    # remove duplicates preserve order
    seen = set()
    out = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def duckduckgo_search_links(query, max_links=6):
    """Get links from DuckDuckGo HTML search page."""
    url = "https://duckduckgo.com/html/?q=" + quote_plus(query)
    try:
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
    except Exception:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    # try result anchors first
    # ddg uses a tags with class result__a; fallback to any href
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            links.append(href)
        if len(links) >= max_links:
            break
    return links[:max_links]


def fetch_text(url):
    try:
        r = session.get(url, timeout=TIMEOUT)
    except Exception:
        return ""
    if r.status_code != 200 or not r.text:
        return ""
    soup = BeautifulSoup(r.text, "html.parser")
    # collect title and meta description too (these often contain the spec)
    parts = []
    title = soup.title.string if soup.title and soup.title.string else ""
    if title:
        parts.append(title)
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        parts.append(meta.get("content"))
    # remove scripts/styles and get visible text
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    parts.append(text)
    combined = " ".join(parts)
    combined = re.sub(r"\s+", " ", combined)
    return combined.lower()


def detect_from_text(text):
    """Return best normalized label found from text (or None)."""
    if not text:
        return None
    counts = Counter()
    for k, label in KEYWORDS.items():
        if k in text:
            counts[label] += text.count(k)
    if not counts:
        return None
    # prefer the label with highest count
    return counts.most_common(1)[0][0]


def impute_from_dataset(df, brand, model, year):
    """Try to infer from existing non-missing rows in df.
       Priority: exact brand+model+year -> brand+model(any year) -> brand(any)"""
    col = COL_BESLEME
    # exact match year
    if pd.notna(year):
        mask = (df[COL_BRAND].fillna("").str.strip().str.lower() == str(brand).strip().lower()) & \
               (df[COL_MODEL].fillna("").str.strip().str.lower() == str(model).strip().lower()) & \
               (df[COL_YEAR].fillna("").str.strip() == str(year).strip()) & \
               (df[col].fillna("").str.strip() != "")
        vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
        if vals:
            return Counter(vals).most_common(1)[0][0]
    # brand+model any year
    mask = (df[COL_BRAND].fillna("").str.strip().str.lower() == str(brand).strip().lower()) & \
           (df[COL_MODEL].fillna("").str.strip().str.lower() == str(model).strip().lower()) & \
           (df[col].fillna("").str.strip() != "")
    vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
    if vals:
        return Counter(vals).most_common(1)[0][0]
    # brand any
    mask = (df[COL_BRAND].fillna("").str.strip().str.lower() == str(brand).strip().lower()) & \
           (df[col].fillna("").str.strip() != "")
    vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
    if vals:
        return Counter(vals).most_common(1)[0][0]
    return None


def main():
    df = pd.read_csv(INPUT, dtype=str, low_memory=False)
    if COL_BESLEME not in df.columns:
        df[COL_BESLEME] = pd.NA

    filled = 0
    total_to_process = 0

    # Pre-clean whitespace in brand/model/year to improve matching
    df[COL_BRAND] = df[COL_BRAND].astype(str).str.strip()
    df[COL_MODEL] = df[COL_MODEL].astype(str).str.strip()
    if COL_YEAR in df.columns:
        df[COL_YEAR] = df[COL_YEAR].astype(str).str.strip()

    for idx, row in df.iterrows():
        curr = row.get(COL_BESLEME, "")
        if curr is not None and str(curr).strip() not in ("", "nan", "None", "NaN"):
            continue  # already filled
        total_to_process += 1

        motor_type = row.get(COL_MOTOR_TYPE, "")
        # EVs:
        if is_electric(motor_type):
            df.at[idx, COL_BESLEME] = "Elektrik"
            filled += 1
            continue

        brand = row.get(COL_BRAND, "")
        model = row.get(COL_MODEL, "")
        year = row.get(COL_YEAR, "")

        # 1) try dataset imputation
        imputed = impute_from_dataset(df, brand, model, year)
        if imputed:
            df.at[idx, COL_BESLEME] = imputed
            filled += 1
            continue

        # 2) web search attempts with several queries
        queries = build_search_queries(brand, model, year, motor_type)
        candidate_counts = Counter()
        for q in queries:
            links = duckduckgo_search_links(q, max_links=MAX_LINKS)
            for link in links:
                txt = fetch_text(link)
                if not txt:
                    continue
                detected = detect_from_text(txt)
                if detected:
                    candidate_counts[detected] += 1
                time.sleep(SLEEP)
            # if we already have a strong candidate, stop early
            if candidate_counts and candidate_counts.most_common(1)[0][1] >= 2:
                break

        if candidate_counts:
            best = candidate_counts.most_common(1)[0][0]
            df.at[idx, COL_BESLEME] = best
            filled += 1
            continue

        # 3) last-ditch: try looser dataset match (brand+similar model ignoring punctuation)
        if pd.notna(model) and model != "":
            model_norm = re.sub(r"[^\w]", "", str(model).lower())
            # search other models that contain similar normalized model token
            mask = df[COL_BRAND].fillna("").str.strip().str.lower() == str(brand).strip().lower()
            candidates = []
            for mval in df.loc[mask, COL_MODEL].dropna().unique():
                if model_norm and model_norm in re.sub(r"[^\w]", "", str(mval).lower()):
                    # collect besleme values for this matching model
                    vals = df.loc[(mask) & (df[COL_MODEL] == mval) & (df[COL_BESLEME].fillna("") != ""), COL_BESLEME].tolist()
                    candidates.extend(vals)
            if candidates:
                df.at[idx, COL_BESLEME] = Counter(candidates).most_common(1)[0][0]
                filled += 1
                continue

        # leave missing if nothing reliable found

    df.to_csv(OUTPUT, index=False)
    print("Done. Processed:", total_to_process, "Filled:", filled)


if __name__ == "__main__":
    main()


##################################################################################
# MOTOR (Icten Yanmali) - Silindir Adedi (FAST VERSION: dataset-only, no web)
##################################################################################

import re
from collections import Counter
import pandas as pd
from tqdm import tqdm

INPUT = "car_data_missing_data_fix_3.csv"
OUTPUT = "car_data_missing_data_fix_4.csv"

COL_BRAND = "MARKA"
COL_MODEL = "MODEL"
COL_MOTOR_TYPE = "TEMEL OZELLIKLER - Motor Tipi"
COL_YEAR = "TEMEL OZELLIKLER - Model Yili"
COL_CYL = "MOTOR (Icten Yanmali) - Silindir Adedi"


def is_electric(motor_type):
    if pd.isna(motor_type):
        return False
    s = str(motor_type).lower()
    return ("elektr" in s) or ("bev" in s) or ("electric" in s)


def normalize_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip()


def impute_from_pool(df, brand, model, motor_type):
    """Try multiple dataset fallbacks to find existing cylinder counts (mode).
       PRIORITY: brand+model+motor_type -> brand+model -> brand+motor_type
    """
    col = COL_CYL
    b = normalize_text(brand).lower()
    m = normalize_text(model).lower()
    mt = normalize_text(motor_type).lower()

    # exact brand+model+motor_type
    mask = (df[COL_BRAND].fillna("").str.strip().str.lower() == b) & \
           (df[COL_MODEL].fillna("").str.strip().str.lower() == m) & \
           (df[COL_MOTOR_TYPE].fillna("").str.strip().str.lower() == mt) & \
           (df[col].fillna("").astype(str).str.strip() != "")
    vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
    if vals:
        ints = [int(re.findall(r'\d+', v)[0]) for v in vals if re.findall(r'\d+', v)]
        if ints:
            return Counter(ints).most_common(1)[0][0]
        return Counter(vals).most_common(1)[0][0]

    # brand+model (any motor type)
    mask = (df[COL_BRAND].fillna("").str.strip().str.lower() == b) & \
           (df[COL_MODEL].fillna("").str.strip().str.lower() == m) & \
           (df[col].fillna("").astype(str).str.strip() != "")
    vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
    if vals:
        ints = [int(re.findall(r'\d+', v)[0]) for v in vals if re.findall(r'\d+', v)]
        if ints:
            return Counter(ints).most_common(1)[0][0]
        return Counter(vals).most_common(1)[0][0]

    # brand+motor_type
    mask = (df[COL_BRAND].fillna("").str.strip().str.lower() == b) & \
           (df[COL_MOTOR_TYPE].fillna("").str.strip().str.lower() == mt) & \
           (df[col].fillna("").astype(str).str.strip() != "")
    vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
    if vals:
        ints = [int(re.findall(r'\d+', v)[0]) for v in vals if re.findall(r'\d+', v)]
        if ints:
            return Counter(ints).most_common(1)[0][0]
        return Counter(vals).most_common(1)[0][0]

    return None


def main():
    df = pd.read_csv(INPUT, dtype=str, low_memory=False)
    if COL_CYL not in df.columns:
        df[COL_CYL] = pd.NA

    # normalize
    df[COL_BRAND] = df[COL_BRAND].astype(str).str.strip()
    df[COL_MODEL] = df[COL_MODEL].astype(str).str.strip()
    if COL_MOTOR_TYPE in df.columns:
        df[COL_MOTOR_TYPE] = df[COL_MOTOR_TYPE].astype(str).str.strip()

    filled = 0
    total = 0

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Filling cylinders"):
        total += 1
        cur = row.get(COL_CYL, "")
        if cur is not None and str(cur).strip() not in ("", "nan", "None", "NaN"):
            continue  # already present

        motor_type = row.get(COL_MOTOR_TYPE, "")
        if is_electric(motor_type):
            df.at[idx, COL_CYL] = "Elektrik"
            filled += 1
            continue

        brand = row.get(COL_BRAND, "")
        model = row.get(COL_MODEL, "")

        imputed = impute_from_pool(df, brand, model, motor_type)
        if imputed:
            df.at[idx, COL_CYL] = str(imputed)
            filled += 1

    df.to_csv(OUTPUT, index=False)
    print("Done. Processed:", total, "Filled:", filled)


if __name__ == "__main__":
    main()

##################################################################################
#MOTOR (Icten Yanmali) - Yakit Puskurtme	PERFORMANS - Azami Hiz	PERFORMANS - Azami Tork (Toplam)
##################################################################################

import re
from collections import Counter
import pandas as pd

INPUT = "car_data_missing_data_fix_4.csv"
OUTPUT = "car_data_missing_data_fix_5.csv"

COL_BRAND = "MARKA"
COL_MODEL = "MODEL"
COL_MOTOR_TYPE = "TEMEL OZELLIKLER - Motor Tipi"
COL_FUEL = "TEMEL OZELLIKLER - Yakit Tipi"

COL_SIL_HACIM = "MOTOR (Icten Yanmali) - Silindir Hacmi"
COL_YAKIT_PUSKURTME = "MOTOR (Icten Yanmali) - Yakit Puskurtme"
COL_AZAMI_HIZ = "PERFORMANS - Azami Hiz"
COL_AZAMI_TORK = "PERFORMANS - Azami Tork (Toplam)"

# helper funcs
def is_electric_by_fuel_or_motor(fuel, motor):
    def contains_elektr(s):
        if s is None:
            return False
        s = str(s).lower()
        return "elektr" in s or "bev" in s or "electric" in s
    return contains_elektr(fuel) or contains_elektr(motor)

def normalize_key(x):
    return "" if pd.isna(x) else str(x).strip()

def mode_of_list(lst):
    if not lst:
        return None
    cnt = Counter(lst)
    return cnt.most_common(1)[0][0]

# imputation search order function
def find_in_pool(df, brand, model, motor_type, target_col):
    b = normalize_key(brand).lower()
    m = normalize_key(model).lower()
    mt = normalize_key(motor_type).lower()
    col = target_col

    # exact brand+model+motor_type
    mask = (df[COL_BRAND].fillna("").astype(str).str.strip().str.lower() == b) & \
           (df[COL_MODEL].fillna("").astype(str).str.strip().str.lower() == m) & \
           (df[COL_MOTOR_TYPE].fillna("").astype(str).str.strip().str.lower() == mt) & \
           (df[col].fillna("").astype(str).str.strip() != "")
    vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
    if vals:
        return mode_of_list(vals)

    # brand+model (any motor type)
    mask = (df[COL_BRAND].fillna("").astype(str).str.strip().str.lower() == b) & \
           (df[COL_MODEL].fillna("").astype(str).str.strip().str.lower() == m) & \
           (df[col].fillna("").astype(str).str.strip() != "")
    vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
    if vals:
        return mode_of_list(vals)

    # brand+motor_type
    mask = (df[COL_BRAND].fillna("").astype(str).str.strip().str.lower() == b) & \
           (df[COL_MOTOR_TYPE].fillna("").astype(str).str.strip().str.lower() == mt) & \
           (df[col].fillna("").astype(str).str.strip() != "")
    vals = df.loc[mask, col].dropna().astype(str).str.strip().tolist()
    if vals:
        return mode_of_list(vals)

    return None

# main
df = pd.read_csv(INPUT, dtype=str, low_memory=False)

# ensure columns exist
for c in (COL_SIL_HACIM, COL_YAKIT_PUSKURTME, COL_AZAMI_HIZ, COL_AZAMI_TORK):
    if c not in df.columns:
        df[c] = pd.NA

# Normalize some columns for matching speed (strip)
df[COL_BRAND] = df[COL_BRAND].astype(str).str.strip()
df[COL_MODEL] = df[COL_MODEL].astype(str).str.strip()
if COL_MOTOR_TYPE in df.columns:
    df[COL_MOTOR_TYPE] = df[COL_MOTOR_TYPE].astype(str).str.strip()
if COL_FUEL in df.columns:
    df[COL_FUEL] = df[COL_FUEL].astype(str).str.strip()

# Counters
deleted_sil_hacim = 0
deleted_azami_tork = 0
filled_yakit_puskurtme = 0
filled_azami_hiz = 0
filled_azami_tork = 0

# First pass: delete Silindir Hacmi and Azami Tork for electric cars
for idx, row in df.iterrows():
    fuel = row.get(COL_FUEL, "")
    motor = row.get(COL_MOTOR_TYPE, "")
    if is_electric_by_fuel_or_motor(fuel, motor):
        # delete silindir hacim
        if str(row.get(COL_SIL_HACIM, "")).strip() not in ("", "nan", "None", "NaN"):
            df.at[idx, COL_SIL_HACIM] = ""
            deleted_sil_hacim += 1
        # delete azami tork
        if str(row.get(COL_AZAMI_TORK, "")).strip() not in ("", "nan", "None", "NaN"):
            df.at[idx, COL_AZAMI_TORK] = ""
            deleted_azami_tork += 1

# Second pass: fill missing values using hierarchy for the three target columns
# Use the current dataframe (so earlier non-electric rows with values can be used)
for idx, row in df.iterrows():
    brand = row.get(COL_BRAND, "")
    model = row.get(COL_MODEL, "")
    motor_type = row.get(COL_MOTOR_TYPE, "")
    fuel = row.get(COL_FUEL, "")

    # Skip EVs for imputation of fuel-based columns (we already cleared silindir and tork)
    if is_electric_by_fuel_or_motor(fuel, motor_type):
        continue

    # Yakit Puskurtme
    cur = row.get(COL_YAKIT_PUSKURTME, "")
    if str(cur).strip() in ("", "nan", "None", "NaN"):
        val = find_in_pool(df, brand, model, motor_type, COL_YAKIT_PUSKURTME)
        if val:
            df.at[idx, COL_YAKIT_PUSKURTME] = val
            filled_yakit_puskurtme += 1

    # Azami Hiz
    cur = row.get(COL_AZAMI_HIZ, "")
    if str(cur).strip() in ("", "nan", "None", "NaN"):
        val = find_in_pool(df, brand, model, motor_type, COL_AZAMI_HIZ)
        if val:
            df.at[idx, COL_AZAMI_HIZ] = val
            filled_azami_hiz += 1

    # Azami Tork (for non-electric only)
    cur = row.get(COL_AZAMI_TORK, "")
    if str(cur).strip() in ("", "nan", "None", "NaN"):
        val = find_in_pool(df, brand, model, motor_type, COL_AZAMI_TORK)
        if val:
            df.at[idx, COL_AZAMI_TORK] = val
            filled_azami_tork += 1

# Save
df.to_csv(OUTPUT, index=False)

# Summary
print("Done.")
print("Deleted Silindir Hacim for EVs:", deleted_sil_hacim)
print("Deleted Azami Tork for EVs:", deleted_azami_tork)
print("Filled Yakit Puskurtme:", filled_yakit_puskurtme)
print("Filled Azami Hiz:", filled_azami_hiz)
print("Filled Azami Tork (non-EV):", filled_azami_tork)

##################################################################################
#MARKA MODEL FILTRELEME
##################################################################################

import pandas as pd

# Input / Output paths
INPUT = "car_data_missing_data_fix_5.csv"
FUTURE = "future_car_data.csv"

# --- The reference brand/model list ---
brand_models = {
    "Alfa Romeo": ["Giulia","Giulia Quadrifoglio","Giulietta","Junior Elettrica","Junior Ibrida","Stelvio","Tonale"],
    "Aston Martin": ["DB11","DB9","DBS","Rapide","Vanquish","Vantage","DBX"],
    "Audi": ["A1","A3","A4","A5","A6","A6 E-Tron","A7","A8","E-Tron GT","R8","E-Tron","E-Tron Sportback","Q2","Q3","Q3 Sportback","Q4 E-tron","Q4 Sportback","Q5","Q5 Sportback","Q6 E-tron","Q7","Q8","Q8 E-tron","Q8 E-tron Sportback","RS Q8","SQ7","S Serisi"],
    "Bentley": ["Continental","Flying Spur","Bentayga"],
    "BMW": ["1 Serisi","2 Serisi","3 Serisi","4 Serisi","5 Serisi","6 Serisi","7 Serisi","8 Serisi","i SERİSİ","M SERİSİ","Z SERİSİ","iX SERİSİ","iX1 SERİSİ","iX2 SERİSİ","iX3 SERİSİ","X1 SERİSİ","X2 SERİSİ","X3 SERİSİ","X4 SERİSİ","X5 SERİSİ","X6 SERİSİ","X7 SERİSİ","i ","M ","Z ","iX ","iX1 ","iX2 ","iX3 ","X1 ","X2 ","X3 ","X4 ","X5 ","X6 ","X7 "],
    "BYD": ["Dolphin","Han","Seal","Atto 3","Atto 3 EV","Seal U","Seal U EV","Tang"],
    "Cadillac": ["Escalade"],
    "Chery": ["Omoda 5","Omoda5","Omoda 5 Pro","Tiggo8","Tiggo7","Tiggo 7 Pro","Tiggo 7 Pro Max","Tiggo 8 Pro","Tiggo 8 Pro Max"],
    "Chevrolet": ["Camaro","Corvette","Impala","Silverado","Suburban","Tahoe"],
    "Chrysler": ["Pacifica"],
    "Citroën": ["AMI","C-Elysée","C1","C3","e-C3","C4","C4 Grand Picasso","C4 Picasso","C4 X","e-C4","e-C4 X","C5","C3 AirCross","C3 AirCross Elektrik","C4 Cactus","C5 AirCross","Berlingo","Jumper","Jumpy","Nemo"],
    "Cupra": ["Born","Leon","Ateca","Formentor","Terramar"],
    "Dacia": ["Jogger","Lodgy","Logan","Sandero","Sandero Stepway","Duster","Spring","Dokker"],
    "Dodge": ["Challenger","Charger","Durango","Journey","Ram"],
    "DS Automobiles": ["DS 3","DS 4","DS 5","DS 9","DS 3 Crossback","DS 7 Crossback"],
    "Ferrari": ["296","458","488","California","F8","Portofino","Roma","SF90","Purosangue"],
    "Fiat": ["124 Spider","500 Ailesi","500 X","600","600e","Egea","Egea Cross","Linea","Panda","Punto","Topolino","Freemont","Fullback","Doblo Cargo","Doblo Combi","Doblo Panorama","e-Doblo Panorama","Ducato","Fiorino Cargo","Fiorino Combi","Fiorino Combi Mix","Fiorino Panorama","Scudo","Ulysse","Doblo Combi Mix"],
    "Ford": ["B-Max","C-Max","Fiesta","Focus","Galaxy","Grand C-Max","Mondeo","Mustang","S-Max","EcoSport","Edge","Expedition","Explorer","F","Kuga","Mustang Mach-E","Puma","Puma-E","Ranger","Ranger Raptor","Bronco","Escape","Tourneo Connect","Tourneo Courier","Tourneo Custom","Transit","E-Transit","Transit Connect","Transit Courier","Transit Custom","E-Transit Custom"],
    "GMC": ["Canyon","Hummer","Sierra","Terrain"],
    "Honda": ["Accord","City","Civic","E","Jazz","NSX","CR-V","HR-V","ZR-V"],
    "Hyundai": ["Accent Blue","Elantra","Genesis","i10","i20","i20 Active","i20 N","i20 Troy","i30","Ioniq","Ioniq 6","Bayon","Ioniq 5","Ioniq 5 N","Inster","ix35","Kona","Kona Elektrik","Santa Fe","Tucson","H 100","H 350","Staria"],
    "Isuzu": ["D-Max"],
    "Jaecoo": ["J7"],
    "Jaguar": ["F-Type","XE","XF","XJ","E-Pace","F-Pace","I-Pace"],
    "Jeep": ["Avenger Electric","Avenger Hybrid","Cherokee","Compass","Grand Cherokee","Renegade","Wrangler"],
    "Kia": ["Carens","Ceed","Cerato","Picanto","Rio","Stinger","EV3","EV6","EV9","Niro","Niro EV","Sorento","Soul","Sportage","Stonic","XCeed"],
    "Lamborghini": ["Aventador","Huracan","Revuelto","Urus"],
    "Lexus": ["CT","ES","GS","IS","LM","LS","RC","LBX","NX","RX","RX L","RZ","RZ 450e"],
    "Maserati": ["Ghibli","GranCabrio E","GranTurismo","GranTurismo E","MC20","Quattroporte","Grecale","Levante"],
    "Mazda": ["2","3","6","MX","CX-3","CX-5"],
    "McLaren": ["720S","Artura","GT"],
    "Mercedes-Benz": ["A Serisi","AMG GT","B Serisi","C Serisi","CLA","CLE","CLS","E Serisi","S Serisi","EQE","EQS","EQA","EQB","EQC","EQS SUV","G Serisi","GL","GLA","GLB","GLC","GLC Coupe","GLE","GLE Coupe","GLK","GLS","ML","X","Citan","EQV","Sprinter Panel Van","V-Class","Vito","Vito Mixto/Kombi","Vito Tourer","Vito Tourer Select"],
    "MG": ["MG3","MG4","MG7","ZS","EHS","HS","Marvel R","ZS EV"],
    "Mini": ["Cooper SD","Cooper","Cooper Clubman","Cooper Electric","John Cooper","Cooper S","Countryman","Countryman E","Paceman"],
    "Mitsubishi": ["Attrage","Lancer","Space Star","ASX","Eclipse Cross","L 200","Outlander","Pajero"],
    "Nissan": ["GT-R","Micra","Note","Pulsar","Z","Juke","Navara","Qashqai","X-Trail"],
    "Opel": ["Adam","Astra","Astra-e","Cascada","Corsa","Corsa-e","Insignia","Meriva","Zafira","Crossland","Crossland X","Frontera","Frontera-e","Grandland","Grandland-e","Grandland X","Mokka","Mokka-e","Mokka X","Combo","Combo Cargo","Combo Elektrik","Combo Life","e-Zafira","Movano","Vivaro","Zafira Life"],
    "Peugeot": ["208","e-208","301","308","e-308","405","508","RCZ","408","2008","e-2008","3008","e-3008","5008","e-5008","Bipper","Boxer","Expert","Expert Traveller","Partner","Rifter"],
    "Porsche": ["718","911","Boxster","Cayman","Panamera","Taycan","Cayenne","Cayenne Coupe","Macan","Macan (Elektrikli)"],
    "Renault": ["Clio","Espace","Fluence","Latitude","Megane","Megane E-Tech","Scenic","Symbol","Taliant","Talisman","Austral","Duster","Captur","Kadjar","Koleos","Rafale","Twizy","ZOE","R5 E-Tech","Kangoo","Kangoo E-Tech","Kangoo Express","Kangoo Multix","Master","Trafic","Trafic Multix","Express Combi","Express Van"],
    "Rolls-Royce": ["Ghost","Phantom","Wraith","Spectre","Cullinan"],
    "Seat": ["Alhambra","Altea","Ibiza","Leon","Toledo","Tarraco","Arona","Ateca"],
    "Skoda": ["Fabia","Octavia","Rapid","Roomster","Scala","Superb","Elroq","Enyaq","Enyaq Coupe","Kamiq","Karoq","Kodiaq","Yeti"],
    "Smart": ["Fortwo","Forfour"],
    "Subaru": ["BRZ","Levorg","Crosstrek","Forester","Outback","Solterra","XV"],
    "Suzuki": ["Baleno","Swift","Across","Jimny","S-Cross","Vitara"],
    "Tesla": ["Model 3","Model S","Model X","Model Y"],
    "Toyota": ["Auris","Avensis","Camry","Corolla","Prius","Supra","Verso","Yaris","C-HR","Corolla Cross","Hilux","Land Cruiser","Land Cruiser Prado","RAV4","Yaris Cross"],
    "Volkswagen": ["Arteon","Beetle","Golf","ID.3","ID.4","ID.6","ID.7","Jetta","Passat","Passat Alltrack","Passat Variant","Polo","Scirocco","Sharan","Touran","Up Club","VW CC","Amarok","T-Cross","T-Roc","Taigo","Tayron","Tiguan","Tiguan AllSpace","Touareg","ID. Buzz","Caddy","California","Caravelle","Crafter","Grand California","Multivan","Transporter"],
    "Volvo": ["S60","S80","S90","V40","V40 Cross Country","V60","V60 Cross Country","V70","V90","V90 Cross Country","C40","EX40","XC40","XC60","XC70","XC90"],
    "SsangYong": ["Actyon","Korando","Korando Sports","Musso","Musso Grand","Rexton","Tivoli","Torres","Torres EVX","XLV","Rodius"],
    "Skywell": ["ET5"],
    "TOGG": ["T10X"],
}

# --- Load CSV ---
df = pd.read_csv(INPUT, low_memory=False)

brand_col = "MARKA"
model_col = "MODEL"
seri_col = "TEMEL OZELLIKLER - Seri"

# 1. Filter rows: keep only allowed brand+model OR brand+seri
allowed = {(b, m) for b, models in brand_models.items() for m in models}


# 2. Future models: models in list but missing from df
present = set(zip(df[brand_col], df[model_col])) | set(zip(df[brand_col], df[seri_col]))
missing = allowed - present
future_df = pd.DataFrame(list(missing), columns=[brand_col, model_col])

# Group by brand: combine models
future_grouped = (future_df.groupby(brand_col)[model_col]
                  .apply(lambda x: ", ".join(sorted(x)))
                  .reset_index())

future_grouped.to_csv(FUTURE, index=False)

# Print stats
print(f"Future models listed: {future_grouped.shape[0]}")

##################################################################################
#PERFORMANS - 0 - 100 Km Hizlanma
##################################################################################

import pandas as pd

INPUT = "car_data_missing_data_fix_5.csv"
OUTPUT = "car_data_missing_data_fix_6.csv"

TARGET_COL = "PERFORMANS - 0 - 100 Km Hizlanma"
BRAND_COL = "MARKA"
MODEL_COL = "MODEL"
MOTOR_COL = "TEMEL OZELLIKLER - Motor Tipi"

# Read file
df = pd.read_csv(INPUT, dtype=str, low_memory=False)

# Normalize
for col in [TARGET_COL, BRAND_COL, MODEL_COL, MOTOR_COL]:
    df[col] = df[col].astype(str).str.strip().replace({"nan": pd.NA, "": pd.NA})

def fill_by_hierarchy(df, target, keys):
    """
    Fill missing values in `target` column using hierarchical grouping.
    keys = list of columns to group by (ordered from most specific to least).
    """
    for i in range(len(keys), 0, -1):
        grp = df.dropna(subset=[target]).groupby(keys[:i])[target].agg(lambda x: x.mode().iat[0] if not x.mode().empty else pd.NA).to_dict()
        mask = df[target].isna()
        df.loc[mask, target] = df.loc[mask, keys[:i]].apply(lambda row: grp.get(tuple(row), pd.NA), axis=1)
    return df

# Apply hierarchical filling for acceleration column
df = fill_by_hierarchy(df, TARGET_COL, [BRAND_COL, MODEL_COL, MOTOR_COL])

# Save output
df.to_csv(OUTPUT, index=False)

print(f"Done. Fixed file saved as {OUTPUT}")

##################################################################################
#AGIRLIK & OLCULER - Agirlik AGIRLIK & OLCULER - Genislik AGIRLIK & OLCULER - Uzunluk AGIRLIK & OLCULER - Yukseklik BAGAJ OZELLIKLERI - Bagaj Hacmi (2 Koltuk) BAGAJ OZELLIKLERI - Bagaj Hacmi (5 Koltuk)
##################################################################################

#!/usr/bin/env python3
import pandas as pd

INPUT = "car_data_missing_data_fix_6.csv"
OUTPUT = "car_data_missing_data_fix_7.csv"

# Columns to fix with hierarchy
TARGET_COLS = [
    "AGIRLIK & OLCULER - Agirlik",
    "AGIRLIK & OLCULER - Genislik",
    "AGIRLIK & OLCULER - Uzunluk",
    "AGIRLIK & OLCULER - Yukseklik",
]

BRAND_COL = "MARKA"
MODEL_COL = "MODEL"
MOTOR_COL = "TEMEL OZELLIKLER - Motor Tipi"

# Read file
df = pd.read_csv(INPUT, dtype=str, low_memory=False)

# Normalize strings
for col in TARGET_COLS + [BRAND_COL, MODEL_COL, MOTOR_COL]:
    df[col] = df[col].astype(str).str.strip().replace({"nan": pd.NA, "": pd.NA})

def fill_by_hierarchy(df, target, keys):
    """Fill missing values in `target` column using hierarchical grouping."""
    before_missing = df[target].isna().sum()
    for i in range(len(keys), 0, -1):
        mapping = (
            df.dropna(subset=[target])
              .groupby(keys[:i])[target]
              .agg(lambda x: x.mode().iat[0] if not x.mode().empty else pd.NA)
              .to_dict()
        )
        mask = df[target].isna()
        df.loc[mask, target] = df.loc[mask, keys[:i]].apply(
            lambda row: mapping.get(tuple(row), pd.NA), axis=1
        )
    after_missing = df[target].isna().sum()
    filled = before_missing - after_missing
    print(f"{target}: filled {filled} blanks")
    return df

# Apply filling for all target columns
for col in TARGET_COLS:
    df = fill_by_hierarchy(df, col, [BRAND_COL, MODEL_COL, MOTOR_COL])

# Save output
df.to_csv(OUTPUT, index=False)

print(f"\nDone. Fixed file saved as {OUTPUT}")
