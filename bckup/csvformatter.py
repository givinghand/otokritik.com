# merge_and_format_ordered_fixed.py
import csv
import glob
import re
from collections import OrderedDict

INPUT_GLOB = "car_details/car_details_part*.csv"
OUTPUT_FILE = "car_details_formatted.csv"

POSSIBLE_TITLE_KEYS = {"Başlık", "Baslik", "Title", "title", "başlık", "baslik"}
POSSIBLE_URL_KEYS = {"URL", "Url", "url", "car_page_url", "car_pageurl", "link"}

def clean_text(v: str) -> str:
    if v is None:
        return ""
    v = v.replace("\r", "\n")
    parts = [p.strip() for p in v.splitlines() if p.strip()]
    if not parts:
        return ""
    joined = " | ".join(parts)
    joined = re.sub(r"\s{2,}", " ", joined)
    return joined.strip()

def normalize_key(k: str) -> str:
    if k is None:
        return ""
    return k.strip()

def find_key_in_row(row_keys, candidates):
    for c in candidates:
        if c in row_keys:
            return c
    lower_map = {rk.lower(): rk for rk in row_keys}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None

def transliterate(s: str) -> str:
    if s is None:
        return ""
    mapping = {
        "ç": "c", "Ç": "C",
        "ğ": "g", "Ğ": "G",
        "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O",
        "ş": "s", "Ş": "S",
        "ü": "u", "Ü": "U",
    }
    return "".join(mapping.get(ch, ch) for ch in s)

def ascii_norm(s: str) -> str:
    """Lowercase, transliterate and collapse whitespace for comparisons."""
    if s is None:
        return ""
    t = transliterate(s)
    t = t.lower()
    t = re.sub(r"\s+", " ", t).strip()
    return t

# --- Desired category order and within-category feature order ---
# Kept in Turkish (kullanıcının verdiği sıra). Eşleştirmede transliterate/normalized kullanacağız.
DESIRED_ORDER = [
    ("TEMEL ÖZELLİKLER", [
        "Model Yılı",
        "Araç Türü",
        "Segment",
        "Gövde Tipi",
        "Motor Tipi",
        "Yakıt Tipi",
        "Seri",
        "Donanım Paketi",
    ]),
    ("MOTOR (İçten Yanmalı)", [
        "Silindir Hacmi",
        "Silindir Adedi",
        "Yakıt Püskürtme",
        "Besleme Tipi",
    ]),
    ("PERFORMANS", [
        "Beygir Gücü (Toplam)",
        "Azami Tork (Toplam)",
        "Azami Hız",
        "0-100 Km Hızlanma",
    ]),
    ("ŞANZIMAN & ÇEKİŞ SİSTEMİ", [
        "Şanzıman Türü",
        "Şanzıman Kademesi",
        "Çekiş",
        "Çekiş Kontrol Sistemi",
        "Çekiş Kontrol Özellikleri",
    ]),
    ("YAKIT TÜKETİMİ & EMİSYON", [
        "Yakıt Kapasitesi",
        "Şehir İçi Tüketim (100 km)",
        "Şehir Dışı Tüketim (100 km)",
        "Ortalama Y.Tüketimi (100 km)",
        "Ortalama Emisyon",
    ]),
    ("BAGAJ ÖZELLİKLERİ", [
        "Bagaj Hacmi (5 Koltuk)",
        "Bagaj Hacmi (2 Koltuk)",
        "Bagaj Diğer Özellikler",
    ]),
    ("AĞIRLIK & ÖLÇÜLER", [
        "Uzunluk",
        "Genişlik",
        "Yükseklik",
        "Ağırlık",
        "Dönüş Çapı",
    ]),
    ("LASTİK & JANT", [
        "Taban Genişliği",
        "Kesit Oranı",
        "Jant Çapı",
        "Lastik Ebatları",
        "Jant Tipi",
        "Yedek Lastik Özellikleri",
    ]),
    ("MÜZİK & EĞLENCE", [
        "Radyo",
        "LCD Multimedya Ekran",
        "Harici Giriş-Çıkış",
        "Harici Giriş-Çıkış Özellikleri",
    ]),
    ("NAVİGASYON & BLUETOOTH", [
        "Bluetooth Telefon",
        "Bluetooth Bağlantı Özellikleri",
        "SMS Okuyucu",
    ]),
    ("KOLTUKLAR & İÇ DÖŞEME", [
        "Koltuk Sayısı",
        "Koltuk Döşemesi Tipi",
        "Sürücü Koltuğu Ayarları",
        "Sürücü Koltuğu Özellikleri",
        "Ön Yolcu Koltuğu Ayarları",
        "Arka Koltuk Özellikleri",
        "Kol Dayama",
        "Kol Dayama Özellikleri",
        "İç Mekan Özellikleri",
    ]),
    ("CAMLAR & AYNALAR", [
        "Ön Yan Cam Ayarları",
        "Ön Yan Cam Özellikleri",
        "Arka Yan Cam Ayarları",
        "Arka Yan Cam Özellikleri",
        "Yan Dikiz Aynaları",
        "Yan Dikiz Ayna Özellikleri",
        "İç Dikiz Aynası",
        "Panoramik Cam Tavan",
        "Açılır Tavan",
        "Gövde Rengi",
    ]),
    ("ISITMA & SOĞUTMA", [
        "Klima",
        "Isıtma & Soğutma Özellikleri",
        "Polen Filtresi",
    ]),
    ("LAMBALAR & AYDINLATMA", [
        "Far Tipi",
        "Far Özellikleri",
        "Sis Farları",
        "Sis Farı Özellikleri",
        "Diğer Aydınlatma Özellikleri",
    ]),
    ("DİREKSİYON ÖZELLİKLERİ", [
        "Direksiyon Sistemi",
        "Direksiyon Özellikleri",
    ]),
    ("GÖSTERGELER & SENSÖRLER", [
        "Park Sensörü & Yardımı",
        "Park Yardımı Özellikleri",
        "Far Sensörü",
        "Yağmur Sensörü",
        "Lastik Basınç Sensörü",
        "Göstergeler & Bildirimler",
    ]),
    ("SÜRÜŞ DESTEK SİSTEMLERİ", [
        "Hız Sabitleme & Sınırlama",
        "Dur & Kalk (Stop & Start)",
        "Yokuş Kalkış Desteği",
        "Yokuş Kalkış Özellikleri",
        "Denge Kontrol Sistemi",
        "Denge Kontrol Özellikleri",
        "Diferansiyel Özellikleri",
    ]),
    ("YOLCU EMNİYETİ", [
        "Hava Yastığı",
        "Hava Yastığı Adedi",
        "Hava Yastığı Çeşitleri",
        "Hava Yastığı Özellikleri",
        "Kumanda & Kilit Sistemleri",
        "Çarpışma Testi (NCAP/ANCAP)",
        "NCAP/ANCAP Puanı",
        "NCAP/ANCAP Yılı",
        "NCAP/ANCAP Web Sayfası",
    ]),
    ("FRENLER & SÜSPANSİYON", [
        "ABS Fren Sistemi",
        "Fren Destek Sistemleri",
        "Park Freni Tipi",
        "Ön Süspansiyonlar",
        "Ayarlanır Süspansiyon",
    ]),
    ("DIŞ GÖVDE", [
        "Kapı Sayısı",
        "Dış Gövde Özellikleri",
    ]),
    ("GARANTİ & YOL YARDIM", [
        "Garanti",
        "Yol Yardım Bilgileri",
    ]),
    ("DOKÜMAN", [
        "Test Sürüşü Talep Sayfası",
        "Ürün Kataloğu",
    ]),
]

def main():
    files = sorted(glob.glob(INPUT_GLOB))
    if not files:
        print(f"⚠️ No files found: {INPUT_GLOB}")
        return

    print(f"✅ Found files: {len(files)}")

    combined = OrderedDict()
    all_keys = set()

    for fp in files:
        print(f"⤷ Processing: {fp}")
        with open(fp, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            file_keys = [normalize_key(k) for k in (reader.fieldnames or [])]

            title_key = find_key_in_row(file_keys, POSSIBLE_TITLE_KEYS)
            url_key = find_key_in_row(file_keys, POSSIBLE_URL_KEYS)

            for row in reader:
                url = ""
                title = ""
                if url_key:
                    url = clean_text(row.get(url_key, ""))
                else:
                    for v in row.values():
                        if isinstance(v, str) and v.strip().startswith("http"):
                            url = clean_text(v)
                            break

                if title_key:
                    title = clean_text(row.get(title_key, ""))
                else:
                    for k in row.keys():
                        if k and any(pk.lower() == k.strip().lower() for pk in POSSIBLE_TITLE_KEYS):
                            title = clean_text(row.get(k, ""))
                            break

                if not url:
                    pseudo_key = "__NO_URL__" + title
                    url = pseudo_key

                if url not in combined:
                    combined[url] = {"Başlık": title, "URL": url}

                dest = combined[url]

                for raw_k, raw_v in row.items():
                    if raw_k is None:
                        continue
                    k = normalize_key(raw_k)
                    v = clean_text(raw_v or "")
                    if not v:
                        continue
                    # skip original title/url fields to avoid duplicates
                    if url_key and k == url_key:
                        continue
                    if title_key and k == title_key:
                        continue

                    new_key = re.sub(r"\s*-\s*", " - ", k).strip()
                    if new_key not in dest or not dest[new_key]:
                        dest[new_key] = v
                    all_keys.add(new_key)

    # Build ordered list of keys according to DESIRED_ORDER
    used = set()
    ordered_other_keys = []

    all_keys_list = sorted(all_keys)  # deterministic

    # --- IMPORTANT: match using transliterated / normalized strings ---
    for category, features in DESIRED_ORDER:
        cat_ascii = transliterate(category)
        for feat in features:
            feat_ascii = transliterate(feat)
            candidate_ascii = f"{cat_ascii} - {feat_ascii}"
            cand_norm = ascii_norm(candidate_ascii)
            found = None
            # exact normalized match
            for ak in all_keys_list:
                if ascii_norm(ak) == cand_norm:
                    found = ak
                    break
            # if not exact, try contains both category and feature tokens
            if not found:
                cat_norm = ascii_norm(cat_ascii)
                feat_norm = ascii_norm(feat_ascii)
                for ak in all_keys_list:
                    ak_norm = ascii_norm(ak)
                    if cat_norm in ak_norm and feat_norm in ak_norm:
                        found = ak
                        break
            if found and found not in used:
                ordered_other_keys.append(found)
                used.add(found)

    # append any remaining keys alphabetically
    remaining = [k for k in all_keys_list if k not in used]
    ordered_other_keys.extend(remaining)

    # final fieldnames: Başlık, URL first
    fieldnames = ["Başlık", "URL"] + ordered_other_keys

    # transliterate headers to ASCII for CSV output
    fieldnames_ascii = [transliterate(fn) for fn in fieldnames]

    print(f"📝 Writing {len(combined)} rows to {OUTPUT_FILE} with {len(fieldnames)} columns")

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_ascii)
        writer.writeheader()
        for data in combined.values():
            out_row = {}
            for orig_fn, ascii_fn in zip(fieldnames, fieldnames_ascii):
                val = data.get(orig_fn, "")
                out_row[ascii_fn] = transliterate(val)
            writer.writerow(out_row)

    print("✅ Done. Combined + ordered CSV saved:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
