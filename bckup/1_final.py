# reformat_and_prepend_fixed.py
import csv
import re
from pathlib import Path
from typing import Tuple, Optional

INPUT_FILE = Path("/workspaces/otokritik.com/csvformatted.csv")
OUTPUT_FILE = Path("car_data.csv")

# horsepower unit tokens
_HP_UNITS = {"BG", "PS", "HP"}

# gearbox / trims / global tokens that indicate end of model collection
_GEARBOX_TRIMS = {
    "OTOMATİK", "OTOMATIK", "MANUEL", "MANÜEL", "MANUAL",
    "TIPTRONIC", "DUALOGIC", "DCT", "S-TRONIC", "AUTOMATIC",
    "POWERSHIFT", "AMG", "QUATTRO", "XDRIVE", "POWER", "RS", "GT", "E-TRON"
}

# engine-related tokens that should NOT be included in model (common strings)
_ENGINE_WORDS = {
    "TDI", "CDI", "PURETECH", "MULTIJET", "MULTIAIR", "DIESEL", "BENZIN",
    "HDI", "BLUEHDI", "ETORQ", "E-TORQ", "FIRE", "GDI", "CRDI", "COMMON",
    "RAIL", "TURBO", "HYBRID", "HİBRİT", "HIBRIT"
}

# whitelist of brands (kept as in previous code)
WHITELIST = [
    "Alfa Romeo","Aston Martin","Audi","Bentley","BMW","BYD","Cadillac","Chery","Chevrolet",
    "Chrysler","Citroen","Cupra","Dacia","Daewoo","Daihatsu","Dodge","DS","Ferrari","Fiat",
    "Ford","Geely","Honda","Hyundai","Jaguar","Kia","Kuba","Lada","Lamborghini","Lancia",
    "Lexus","Maserati","Mazda","McLaren","Mercedes-Benz","MG","Mini","Mitsubishi","Nissan",
    "Opel","Peugeot","Porsche","Proton","Renault","Rolls-Royce","Rover","Saab","Seat","Skoda",
    "Smart","Subaru","Suzuki","Tata","Tesla","Tofaş","Toyota","Volkswagen","Volvo"
]

_TURK_MAP = str.maketrans({
    "ç":"c","Ç":"C",
    "ğ":"g","Ğ":"G",
    "ı":"i","İ":"I",
    "ö":"o","Ö":"O",
    "ü":"u","Ü":"U",
    "ş":"s","Ş":"S"
})

def transliterate(s: str) -> str:
    if s is None:
        return ""
    return s.translate(_TURK_MAP)

def normalize_text_for_match(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def detect_header_for_title(fieldnames):
    if not fieldnames:
        return None
    possibles = ["başlık", "baslik", "title"]
    for cand in possibles:
        for fn in fieldnames:
            if fn and fn.strip().lower() == cand:
                return fn
    for fn in fieldnames:
        if fn and ("baş" in fn.lower() or "bas" in fn.lower() or "title" in fn.lower()):
            return fn
    return None

def detect_header_for_url(fieldnames):
    if not fieldnames:
        return None
    possibles = ["url", "car_page_url", "link", "sayfa_url"]
    for cand in possibles:
        for fn in fieldnames:
            if fn and fn.strip().lower() == cand:
                return fn
    for fn in fieldnames:
        if fn and ("url" in fn.lower() or "link" in fn.lower() or "sayfa" in fn.lower()):
            return fn
    return None

def find_brand_in_title(title: str) -> Optional[str]:
    if not title:
        return None
    ntitle = normalize_text_for_match(title)
    tokens = ntitle.split()
    # try to match any whitelist brand by looking for first part matches
    for b in WHITELIST:
        nb = normalize_text_for_match(b.replace("Mercedes-Benz", "Mercedes Benz"))
        parts = nb.split()
        for i, t in enumerate(tokens):
            if t == parts[0]:
                return b
    # fallback: first token
    if tokens:
        first = tokens[0]
        for b in WHITELIST:
            if normalize_text_for_match(b).split()[0] == first:
                return b
    return None

def is_decimal_engine_token(tok: str) -> bool:
    # matches 1.2, 2.0, 3.0 etc.
    return bool(re.match(r"^\d+(\.\d+)$", tok))

def is_pure_numeric(tok: str) -> bool:
    return bool(re.fullmatch(r"^\d+$", tok))

def is_cc_token(tok: str) -> bool:
    return bool(re.fullmatch(r"^\d+cc$", tok.lower()))

def is_hp_token(tok: str) -> bool:
    # "122PS" or "122" followed by next token 'PS' handled elsewhere
    return bool(re.fullmatch(r"^\d+(?:bg|ps|hp)$", tok.lower()))

def extract_brand_model(title: str) -> Tuple[str, str]:
    """
    Extract brand and model while excluding motor information.
    Model tokens are collected starting after brand token (the whole brand phrase)
    and stopping when:
      - encountering a decimal engine token (1.6, 3.0, ...),
      - encountering pure numeric horsepower token followed by BG/PS/HP,
      - encountering 'cc' tokens,
      - encountering engine words like TDI/CI/PureTech etc,
      - encountering gearbox/trim tokens (AMG, QUATTRO, etc.)
    Keeps numeric model-codes like '180' if they appear before the decimal engine token.
    """
    if not title:
        return "", ""
    clean = title.replace("—", " ").replace("–", " ").replace("/", " ").strip()
    tokens = [t.strip(",;:()[]\"'") for t in clean.split() if t.strip(",;:()[]\"'")]
    if not tokens:
        return "", ""

    # drop leading year
    if re.fullmatch(r"\d{4}", tokens[0]):
        tokens_for_search = tokens[1:]
    else:
        tokens_for_search = tokens[:]

    # find brand (canonical from whitelist if possible)
    brand = find_brand_in_title(title)
    brand_idx = -1
    brand_token_count = 1

    if brand:
        # try to match the full brand phrase (multi-word) in the title tokens
        brand_parts = normalize_text_for_match(brand).split()
        norm_tokens = [normalize_text_for_match(t) for t in tokens_for_search]
        for i in range(0, max(0, len(norm_tokens) - len(brand_parts) + 1)):
            if norm_tokens[i:i + len(brand_parts)] == brand_parts:
                brand_idx = i
                brand_token_count = len(brand_parts)
                break

    if brand_idx == -1:
        # fallback: try to match first word of brand or use first token as brand
        if brand:
            bfirst = normalize_text_for_match(brand).split()[0]
            for i, tk in enumerate(tokens_for_search):
                if normalize_text_for_match(tk).split()[0] == bfirst:
                    brand_idx = i
                    brand_token_count = 1
                    break

    if brand_idx == -1:
        # final fallback: brand is first token
        brand = tokens_for_search[0]
        brand_idx = 0
        brand_token_count = 1

    # collect model tokens starting after the whole brand phrase
    start_idx = brand_idx + brand_token_count
    model_tokens = []
    i = start_idx
    while i < len(tokens_for_search):
        tok = tokens_for_search[i]
        tok_up = tok.upper()
        tok_low = tok.lower()

        # stop if token is gearbox/trim or explicit trim words
        if tok_up in _GEARBOX_TRIMS:
            break

        # stop if token is engine word (puretech, tdi, cdi, multijet etc.)
        if tok_up in _ENGINE_WORDS:
            break

        # stop if token is decimal engine (1.6, 3.0)
        if is_decimal_engine_token(tok):
            break

        # stop if token is 'xxxcc' (e.g. '1600cc')
        if is_cc_token(tok):
            break

        # stop if token is pure numeric horsepower and next token is HP unit (e.g. '122' followed by 'PS')
        if is_pure_numeric(tok) and (i + 1 < len(tokens_for_search) and tokens_for_search[i + 1].upper() in _HP_UNITS):
            break

        # stop if token itself is hp token (e.g. '122PS')
        if is_hp_token(tok):
            break

        # otherwise include token as model part
        model_tokens.append(tok)
        i += 1

    # fallback: if nothing collected, try single token right after brand
    if not model_tokens and start_idx < len(tokens_for_search):
        model_tokens.append(tokens_for_search[start_idx])

    model = " ".join(model_tokens).strip()

    brand_out = transliterate((brand or "").strip().title()) if brand else ""
    model_out = transliterate(model.title()) if model else ""

    return brand_out, model_out


def main():
    if not INPUT_FILE.exists():
        print(f"Input file not found: {INPUT_FILE}")
        return

    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        input_fieldnames = reader.fieldnames or []

    title_key = detect_header_for_title(input_fieldnames)
    url_key = detect_header_for_url(input_fieldnames)

    leading_cols = [
        "TEMEL OZELLIKLER - Arac Turu",
        "TEMEL OZELLIKLER - Govde Tipi",
        "TEMEL OZELLIKLER - Segment",
        "MARKA",
        "MODEL",
        "TEMEL OZELLIKLER - Model Yili",
        "Başlık",
        "URL"
    ]

    remaining_keys = []
    for k in input_fieldnames:
        if not k:
            continue
        if k in leading_cols:
            continue
        if k not in remaining_keys:
            remaining_keys.append(k)
    remaining_keys = sorted(remaining_keys)

    formatted = []
    dropped = 0
    for row in rows:
        title = ""
        if title_key and title_key in row:
            title = row.get(title_key, "") or ""
        else:
            for alt in ("Başlık", "Baslik", "baslik", "title"):
                if alt in row:
                    title = row.get(alt, "") or ""
                    break

        brand, model = extract_brand_model(title)

        # brand whitelist fuzzy check
        normalized_brand_lower = normalize_text_for_match(brand)
        allowed = False
        canonical_brand = None
        for wb in WHITELIST:
            if normalize_text_for_match(wb).split()[0] == normalized_brand_lower.split()[0]:
                allowed = True
                canonical_brand = wb
                break
        if not allowed:
            found = find_brand_in_title(title)
            if not found:
                dropped += 1
                continue
            else:
                canonical_brand = found

        if canonical_brand:
            brand = canonical_brand

        new_row = {}
        new_row["TEMEL OZELLIKLER - Arac Turu"] = row.get("TEMEL OZELLIKLER - Arac Turu", "") or ""
        new_row["TEMEL OZELLIKLER - Govde Tipi"] = row.get("TEMEL OZELLIKLER - Govde Tipi", "") or ""
        new_row["TEMEL OZELLIKLER - Segment"] = row.get("TEMEL OZELLIKLER - Segment", "") or ""
        new_row["MARKA"] = str(brand)
        new_row["MODEL"] = str(model)
        new_row["TEMEL OZELLIKLER - Model Yili"] = row.get("TEMEL OZELLIKLER - Model Yili", "") or ""

        raw_title = title or row.get("Başlık", "") or row.get("Baslik", "") or row.get(title_key or "", "")
        raw_url = ""
        if url_key and url_key in row:
            raw_url = row.get(url_key, "") or ""
        else:
            for alt in ("URL", "url", "car_page_url", "link"):
                if alt in row:
                    raw_url = row.get(alt, "") or ""
                    break

        new_row["Başlık"] = transliterate(raw_title)
        new_row["URL"] = raw_url

        for k in remaining_keys:
            if k in ("Başlık", "Baslik", "title", url_key):
                continue
            new_row[k] = transliterate(row.get(k, "") or "")

        for lc in leading_cols:
            if lc not in new_row:
                new_row[lc] = ""

        formatted.append(new_row)

    # sort by MARKA then MODEL
    formatted.sort(key=lambda r: ((r.get("MARKA") or "").lower(), (r.get("MODEL") or "").lower()))

    final_remaining = [k for k in remaining_keys if k not in leading_cols and k not in ("Başlık", "URL")]
    fieldnames = leading_cols[:6] + ["Başlık", "URL"] + final_remaining

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in formatted:
            out = {k: r.get(k, "") for k in fieldnames}
            writer.writerow(out)

    print(f"✅ Written {len(formatted)} rows to {OUTPUT_FILE} (dropped {dropped} rows not in whitelist)")

if __name__ == "__main__":
    main()
