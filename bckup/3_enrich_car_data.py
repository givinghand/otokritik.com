#!/usr/bin/env python3
"""
fill_car_data_from_web.py

- INPUT_CSV: varsayılan /workspaces/otokritik.com/car_data_improved.csv
- OUTPUT_CSV: varsayılan /workspaces/otokritik.com/car_data_filled.csv

Çalıştırma örnekleri:
python fill_car_data_from_web.py           # tüm dosya (yavaş)
python fill_car_data_from_web.py --limit 10  # sadece ilk 10 satırı dene (test)
python fill_car_data_from_web.py --start 50 --limit 50
"""

import argparse
import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from pathlib import Path
from tqdm import tqdm

# ---------- CONFIG ----------
INPUT_CSV = Path("/workspaces/otokritik.com/car_data_improved.csv")
OUTPUT_CSV = Path("/workspaces/otokritik.com/car_data_filled.csv")
SAMPLE_OUTPUT = Path("/workspaces/otokritik.com/car_data_filled_sample10.csv")
USER_AGENT = "CarDataFiller/1.0 (+https://your-project.example) Mozilla/5.0"
DELAY_BETWEEN_REQUESTS = 1.0  # saniye
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
# ----------------------------

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def normalize_text(s):
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def make_search_query(brand, model, year):
    parts = [p for p in (brand, model, str(year) if year else "") if p]
    q = " ".join(parts) + " specifications"
    return q


def wiki_search_page(title_query):
    """Use Wikipedia opensearch to find candidate page titles (en)."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": title_query,
        "format": "json",
        "srlimit": 5,
    }
    try:
        r = session.get(WIKIPEDIA_API, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        hits = [s["title"] for s in data.get("query", {}).get("search", [])]
        return hits
    except Exception:
        return []


def wiki_get_html(title):
    """Fetch raw HTML content for a Wikipedia title."""
    params = {"action": "parse", "page": title, "prop": "text", "format": "json"}
    r = session.get(WIKIPEDIA_API, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    html = data.get("parse", {}).get("text", {}).get("*")
    return html


def parse_wikipedia_infobox(html):
    """
    Parse an HTML (Wikipedia page) and extract common infobox fields.
    Returns dict of possible keys: displacement_cc, power_bg, power_kw, torque_nm,
    weight_kg, length_mm, width_mm, height_mm, boot_l, 0_100_s, top_speed_kmph, fuel_type, doors
    """
    if not html:
        return {}
    soup = BeautifulSoup(html, "lxml")
    infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
    out = {}
    if not infobox:
        return out
    # Find all rows
    for tr in infobox.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        key = th.get_text(" ", strip=True).lower()
        val = td.get_text(" ", strip=True)
        v = val.strip()
        # heuristics
        if "wheelbase" in key or "length" in key:
            # map dimensions
            if "length" in key:
                m = re.search(r"(\d{3,4})\s*mm", v)
                if m:
                    out["length_mm"] = m.group(1)
            if "width" in key:
                m = re.search(r"(\d{3,4})\s*mm", v)
                if m:
                    out["width_mm"] = m.group(1)
            if "height" in key:
                m = re.search(r"(\d{3,4})\s*mm", v)
                if m:
                    out["height_mm"] = m.group(1)
        # displacement
        if "engine" in key or "displacement" in key or "engines" in key:
            m = re.search(r"(\d{1,4}\.?\d?)\s*l", v, flags=re.I)
            if m:
                # convert liters to cc
                liters = float(m.group(1))
                out["displacement_cc"] = str(int(liters * 1000))
            # also try cc
            m2 = re.search(r"(\d{3,4})\s*cc", v, flags=re.I)
            if m2:
                out["displacement_cc"] = m2.group(1)
        # power
        if "power" in key or "output" in key or ("hp" in v.lower() and "power" in key):
            m = re.search(r"(\d{2,4})\s*(?:bhp|hp|ps|bg)", v, flags=re.I)
            if m:
                out["power_bg"] = m.group(1)
            mkw = re.search(r"(\d{2,4})\s*kW", v, flags=re.I)
            if mkw:
                out["power_kw"] = mkw.group(1)
        # torque
        if "torque" in key:
            m = re.search(r"(\d{2,4})\s*Nm", v, flags=re.I)
            if m:
                out["torque_nm"] = m.group(1)
        # weight
        if "weight" in key:
            m = re.search(r"(\d{3,4})\s*kg", v, flags=re.I)
            if m:
                out["weight_kg"] = m.group(1)
        # boot/boot capacity
        if "boot" in key or "luggage" in key:
            m = re.search(r"(\d{2,4})\s*lit", v, flags=re.I)
            if m:
                out["boot_l"] = m.group(1)
        # 0-100
        if "0–100" in key or "0–100 km/h" in key or "0–100 km/h" in key or "0 - 100" in key or "0–100 km/h" in key:
            m = re.search(r"(\d+(\.\d+)?)\s*s", v, flags=re.I)
            if m:
                out["0_100_s"] = m.group(1)
        # top speed
        if "top speed" in key or "topspeed" in key or "maximum speed" in key:
            m = re.search(r"(\d{2,3})\s*km", v, flags=re.I)
            if m:
                out["top_speed_kmph"] = m.group(1)
    # additional scanning in page for values if infobox not complete
    return out


def search_duckduckgo(query, max_results=6):
    """Simple DuckDuckGo HTML search (no JS) - best-effort fallback."""
    url = "https://duckduckgo.com/html/?q=" + quote_plus(query)
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        links = []
        for a in soup.select("a.result__a, a[data-testid='result-title-a']")[:max_results]:
            href = a.get("href")
            if href:
                links.append(href)
        # fallback selector for different markup
        if not links:
            for a in soup.select("a"):
                href = a.get("href")
                if href and href.startswith("http"):
                    links.append(href)
                if len(links) >= max_results:
                    break
        return links
    except Exception:
        return []


def parse_generic_specs_from_url(url):
    """Fetch page and attempt to extract some numeric specs using regex heuristics."""
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
        text = BeautifulSoup(r.text, "lxml").get_text(" ", strip=True)
        out = {}
        # displacement
        m = re.search(r"(\d{3,4})\s?cc", text, flags=re.I)
        if m:
            out["displacement_cc"] = m.group(1)
        else:
            m2 = re.search(r"(\d\.\d)\s?l", text, flags=re.I)
            if m2:
                out["displacement_cc"] = str(int(float(m2.group(1)) * 1000))
        # power
        m = re.search(r"(\d{2,4})\s*(?:hp|ps|bg|bhp)", text, flags=re.I)
        if m:
            out["power_bg"] = m.group(1)
        # torque
        m = re.search(r"(\d{2,4})\s*(?:Nm|N·m)", text, flags=re.I)
        if m:
            out["torque_nm"] = m.group(1)
        # 0-100
        m = re.search(r"0[\s\-–to]+100(?:\s*km/h)?\D+?(\d+(\.\d+)?)\s*s", text, flags=re.I)
        if m:
            out["0_100_s"] = m.group(1)
        # top speed
        m = re.search(r"top speed\D+?(\d{2,3})\s*km", text, flags=re.I)
        if m:
            out["top_speed_kmph"] = m.group(1)
        # boot
        m = re.search(r"boot(?:\s+capacity|)\D+?(\d{2,4})\s*(?:lit|l)", text, flags=re.I)
        if m:
            out["boot_l"] = m.group(1)
        # weight
        m = re.search(r"\b(\d{3,4})\s*kg\b", text, flags=re.I)
        if m:
            out["weight_kg"] = m.group(1)
        # dimensions
        m = re.search(r"length\D+?(\d{3,4})\s*mm", text, flags=re.I)
        if m:
            out["length_mm"] = m.group(1)
        m = re.search(r"width\D+?(\d{3,4})\s*mm", text, flags=re.I)
        if m:
            out["width_mm"] = m.group(1)
        m = re.search(r"height\D+?(\d{3,4})\s*mm", text, flags=re.I)
        if m:
            out["height_mm"] = m.group(1)
        return out
    except Exception:
        return {}


def merge_into_row(row, found, overwrite=False):
    """Merge found specs into CSV row (fill only empty fields by default)."""
    # mapping from found keys to CSV headers (you can extend mapping as needed)
    mapping = {
        "displacement_cc": ["MOTOR (Icten Yanmali) - Silindir Hacmi", "MOTOR (Icten Yanmali) - Silindir Hacmi"],
        "power_bg": ["PERFORMANS - Beygir Gucu (Toplam)"],
        "torque_nm": ["PERFORMANS - Azami Tork (Toplam)"],
        "0_100_s": ["PERFORMANS - 0 - 100 Km Hizlanma"],
        "top_speed_kmph": ["PERFORMANS - Azami Hiz"],
        "weight_kg": ["AGIRLIK & OLCULER - Agirlik"],
        "length_mm": ["AGIRLIK & OLCULER - Uzunluk"],
        "width_mm": ["AGIRLIK & OLCULER - Genislik"],
        "height_mm": ["AGIRLIK & OLCULER - Yukseklik"],
        "boot_l": ["BAGAJ OZELLIKLERI - Bagaj Hacmi (5 Koltuk)", "BAGAJ OZELLIKLERI - Bagaj Hacmi (2 Koltuk)"],
    }
    notes = []
    for k, v in found.items():
        if not v:
            continue
        targets = mapping.get(k, [])
        for t in targets:
            if not t:
                continue
            cur = row.get(t, "")
            if overwrite or not cur:
                row[t] = v
                notes.append(f"{t} <- {v}")
    return row, notes


def enrich_row(brand, model, year, row, overwrite=False):
    """
    Try:
     1) Wikipedia search and infobox parse
     2) DuckDuckGo search and parse top pages
    Return found dict, notes list
    """
    query = make_search_query(brand, model, year)
    found = {}
    notes = []

    # 1) wikipedia
    titles = wiki_search_page(query)
    time.sleep(DELAY_BETWEEN_REQUESTS)
    for t in titles:
        try:
            html = wiki_get_html(t)
            time.sleep(DELAY_BETWEEN_REQUESTS)
            wfound = parse_wikipedia_infobox(html)
            if wfound:
                # merge
                found.update({k: v for k, v in wfound.items() if v})
                notes.append(f"wikipedia:{t}")
                break
        except Exception:
            continue

    # 2) fallback: duckduckgo search parsed pages
    if not found:
        links = search_duckduckgo(query, max_results=6)
        time.sleep(DELAY_BETWEEN_REQUESTS)
        for link in links:
            parsed = parse_generic_specs_from_url(link)
            if parsed:
                found.update({k: v for k, v in parsed.items() if v})
                notes.append(f"parsed:{link}")
                # keep searching a couple links to increase coverage
                if len(found) >= 4:
                    break
            time.sleep(0.5)
    # merge into row
    new_row, merge_notes = merge_into_row(row, found, overwrite=overwrite)
    notes.extend(merge_notes)
    return new_row, notes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(INPUT_CSV))
    parser.add_argument("--output", default=str(OUTPUT_CSV))
    parser.add_argument("--sample", default=str(SAMPLE_OUTPUT))
    parser.add_argument("--limit", type=int, default=0, help="Limit rows processed (0 = all)")
    parser.add_argument("--start", type=int, default=0, help="Start index (0-based)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing non-empty fields")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.output)
    sample_path = Path(args.sample)

    if not input_path.exists():
        print("Input CSV not found:", input_path)
        return

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=',' if ',' in f.readline() else '\t')
        f.seek(0)
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames

    total = len(rows)
    start = args.start
    limit = args.limit or (total - start)

    processed = 0
    logs = []
    for idx in tqdm(range(start, min(total, start + limit)), desc="Processing rows"):
        row = rows[idx]
        mark = normalize_text(row.get("MARKA") or row.get("Marka") or "")
        model = normalize_text(row.get("MODEL") or row.get("Model") or "")
        year = normalize_text(row.get("TEMEL OZELLIKLER - Model Yili") or row.get("Model Yili") or "")
        if not (mark or model):
            logs.append((idx, "skip:no brand/model"))
            continue

        # only attempt if there are any empty target fields
        # define key targets for completeness
        targets = [
            "MOTOR (Icten Yanmali) - Silindir Hacmi",
            "PERFORMANS - Beygir Gucu (Toplam)",
            "PERFORMANS - Azami Tork (Toplam)",
            "PERFORMANS - 0 - 100 Km Hizlanma",
            "AGIRLIK & OLCULER - Agirlik",
            "AGIRLIK & OLCULER - Uzunluk",
            "AGIRLIK & OLCULER - Genislik",
            "AGIRLIK & OLCULER - Yukseklik",
            "BAGAJ OZELLIKLERI - Bagaj Hacmi (5 Koltuk)",
        ]
        need = False
        for t in targets:
            if not row.get(t):
                need = True
                break
        if not need and not args.overwrite:
            logs.append((idx, "skip:already-complete"))
            continue

        new_row, notes = enrich_row(mark, model, year, row, overwrite=args.overwrite)
        rows[idx] = new_row
        processed += 1
        logs.append((idx, ";".join(notes)))
        # save sample and full output periodically
        time.sleep(0.2)

    # write output CSV
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    # write small sample (first 10 processed rows) for quick inspection
    sample_rows = rows[start:start + min(10, total - start)]
    with sample_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sample_rows)

    print(f"Done. Processed rows: {processed}. Output saved to: {out_path}")
    print(f"Sample saved to: {sample_path}")
    # optional: print last few logs
    for l in logs[-10:]:
        print("log:", l)


if __name__ == "__main__":
    main()
