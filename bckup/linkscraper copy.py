# scraper.py
import csv
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.epey.com/araba/e/YTowOnt9X047=/"
TOTAL_PAGES = 342
CSV_FILE = "cars.csv"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/117.0 Safari/537.36")


def scrape_car_links():
    results = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9"
        })

        page.set_default_navigation_timeout(0)

        for i in range(1, TOTAL_PAGES + 1):
            url = f"{BASE_URL}{i}/"
            print(f"🔎 Sayfa işleniyor: {url}")
            page.goto(url, wait_until="domcontentloaded")

            # Sayfadaki tüm img'leri bul
            imgs = page.locator("img").all()
            for img in imgs:
                href = img.evaluate("el => (el.closest('a') ? el.closest('a').href : null)")
                if href and href.startswith("https://www.epey.com/araba/") and href.endswith(".html"):
                    results.add(href)

        browser.close()

    # CSV yaz
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["car_page_url"])
        for url in sorted(results):
            writer.writerow([url])

    print(f"\nToplam {len(results)} araç linki bulundu. CSV kaydedildi: {CSV_FILE}")


if __name__ == "__main__":
    scrape_car_links()
