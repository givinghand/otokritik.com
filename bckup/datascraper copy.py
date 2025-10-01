# datascraper.py
import csv
from playwright.sync_api import sync_playwright

CSV_INPUT = "cars.csv"
CSV_OUTPUT = "car_details"  # dosya prefix olacak
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/117.0 Safari/537.36"
)

BATCH_SIZE = 500  # her 500 linkte bir yeni csv

def scrape_car_details():
    # Girdi CSV'den linkleri oku
    with open(CSV_INPUT, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        car_links = [row["car_page_url"] for row in reader]

    all_data = []
    batch_index = 1

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox"]
        )
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9"
        })
        page.set_default_timeout(5000)  # Varsayılan 5 sn

        for idx, url in enumerate(car_links, start=1):
            print(f"🔎 ({idx}/{len(car_links)}) {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=5000)
            except Exception as e:
                print(f"  ❌ Sayfa yüklenemedi ({e}), atlanıyor...")
                continue

            # Başlık
            try:
                title = page.locator("h1").inner_text().strip()
            except Exception:
                title = "Bilinmiyor"

            car_data = {"URL": url, "Başlık": title}

            # Özellik grupları
            groups = page.locator("div#bilgiler > div.masonry-brick").all()
            print(f"  ✅ {len(groups)} kategori bulundu")

            for grp in groups:
                try:
                    category = grp.locator("h3 span").inner_text().strip()
                except Exception:
                    category = ""

                rows = grp.locator("ul.grup > li").all()
                for row in rows:
                    try:
                        cells = row.locator("xpath=./*").all_inner_texts()
                        if len(cells) >= 2:
                            key, value = cells[0].strip(), cells[1].strip()
                            full_key = f"{category} - {key}" if category else key
                            car_data[full_key] = value
                    except Exception:
                        continue

            all_data.append(car_data)

            # Her 500 kayıtta bir yazdır
            if idx % BATCH_SIZE == 0:
                save_batch(all_data, batch_index)
                batch_index += 1
                all_data = []  # belleği temizle

        # Son kalanları yazdır
        if all_data:
            save_batch(all_data, batch_index)

        browser.close()

def save_batch(data, batch_index):
    filename = f"{CSV_OUTPUT}_part{batch_index}.csv"
    fieldnames = sorted({k for d in data for k in d.keys()})
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"\n💾 {len(data)} kayıt {filename} dosyasına kaydedildi.\n")

if __name__ == "__main__":
    scrape_car_details()
