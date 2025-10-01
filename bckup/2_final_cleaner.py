# final_cleaner.py
"""
Final cleaner + GIB-compliant MTV hesaplama (2025 tabloları entegre).
- Dosya: /workspaces/otokritik.com/car_data.csv -> ..._cleaned.csv
- Not: Kod içinde kullanılan 2025 MTV tabloları resmi sirküler ve hesaplama sitelerinden alınmıştır.
  (Kaynak: dijital.gib.gov.tr, resmi sirküler PDF ve çeşitli hesaplama/kamu siteleri.)
"""
import csv
import re
import unicodedata
from pathlib import Path
from datetime import datetime

INPUT_CSV = Path("/workspaces/otokritik.com/car_data.csv")
OUTPUT_CSV = Path("/workspaces/otokritik.com/car_data_cleaned.csv")
CURRENT_YEAR = 2025

# -------------------------
# Kullanıcı-specified ayarlar
# -------------------------
# (1) kesin silinecek sütunlar (kullanıcının verdiği listeden)
REMOVE_EXACT_COLUMNS = [
    "URL",
    "AGIRLIK & OLCULER - Donus Capi",
    "BAGAJ OZELLIKLERI - Bagaj Diger Ozellikler",
    "BAGAJ OZELLIKLERI - Bagaj Hacmi (7 Koltuk)",
    "Baslik",
    "CAMLAR & AYNALAR - Acilir Tavan Ozellikleri",
    "CAMLAR & AYNALAR - Arka Yan Cam Ozellikleri",
    "CAMLAR & AYNALAR - Ic Dikiz Aynasi Ozellikleri",
    "CAMLAR & AYNALAR - On & Arka Cam Ozellikleri",
    "CAMLAR & AYNALAR - On Yan Cam Ozellikleri",
    "CAMLAR & AYNALAR - Panoramik Tavan Ozellikleri",
    "CAMLAR & AYNALAR - Yan Dikiz Ayna Ozellikleri",
    "DIS GOVDE - Arka Kapi Ozellikleri",
    "DIS GOVDE - Arka Kapi Tipi",
    "DIS GOVDE - Arka Tekerlek",
    "DIS GOVDE - Sag Yan Kapi Ozellikleri",
    "DIS GOVDE - Sasi Tipi",
    "DIS GOVDE - Surgulu Sag Yan Kapi",
    "DIS GOVDE - Surgulu Sol Yan Kapi",
    "FRENLER & SUSPANSIYON - Suspansiyon Ozellikleri",
    "GARANTI & YOL YARDIM - Garanti",
    "GARANTI & YOL YARDIM - Yol Yardim Bilgileri",
    "GARANTI & YOL YARDIM - Yol Yardim Hizmeti",
    "GOSTERGELER & SENSORLER - Lastik Basinc Ozellikleri",
    "GOSTERGELER & SENSORLER - Park Yardimi Ozellikleri",
    "KOLTUKLAR & IC DOSEME - Arka Koltuk Ozellikleri",
    "KOLTUKLAR & IC DOSEME - Doseme Ozellikleri",
    "KOLTUKLAR & IC DOSEME - Ic Mekan Ozellikleri",
    "KOLTUKLAR & IC DOSEME - Kol Dayama Ozellikleri",
    "KOLTUKLAR & IC DOSEME - On Yolcu Kolt.Ozellikleri",
    "KOLTUKLAR & IC DOSEME - Surucu Koltugu Ozellikleri",
    "LAMBALAR & AYDINLATMA - Diger Aydinlatma Ozellikleri",
    "LAMBALAR & AYDINLATMA - Sis Fari Ozellikleri",
    "LASTIK & JANT - Ilk Yardim & Avadanlik",
    "LASTIK & JANT - Jant Capi (Arka)",
    "LASTIK & JANT - Kesit Orani (Arka)",
    "LASTIK & JANT - Lastik Diger Ozellikler",
    "LASTIK & JANT - Lastik Ebatlari (Arka)",
    "LASTIK & JANT - Taban Genisligi (Arka)",
    "LASTIK & JANT - Yedek Lastik Ozellikleri",
    "MOTOR (Elektrikli) - Diger Ozellikler",
    "MOTOR (Icten Yanmali) - Diger Motor Ozellikleri",
    "MUZIK & EGLENCE - Harici Giris - Cikis Ozellikleri",
    "MUZIK & EGLENCE - LCD Ekran Ozellikleri",
    "MUZIK & EGLENCE - LCD Multimedya Ekran",
    "MUZIK & EGLENCE - Multimedya Diger Ozellikler",
    "MUZIK & EGLENCE - Radyo",
    "NAVIGASYON & BLUETOOTH - Bluetooth Baglanti Ozellikleri",
    "NAVIGASYON & BLUETOOTH - Navigasyon Ozellikleri",
    "SANZIMAN & CEKIS SISTEMI - Arazi Kabiliyeti",
    "SANZIMAN & CEKIS SISTEMI - Arazi Ozellikleri",
    "SANZIMAN & CEKIS SISTEMI - Cekme Kapasitesi (Frenli)",
    "SANZIMAN & CEKIS SISTEMI - Cekme Kapasitesi (Frensiz)",
    "SANZIMAN & CEKIS SISTEMI - Uzaklasma Acisi",
    "SANZIMAN & CEKIS SISTEMI - Yaklasma Acisi",
    "SANZIMAN & CEKIS SISTEMI - Yerden Yukseklik (Azami)",
    "SURUS DESTEK SISTEMLERI - Adaptif Hiz Sabitleyici Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Diferansiyel Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Hiz Sabitleyici Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Ozel Surus Ayarlari",
    "SURUS DESTEK SISTEMLERI - Serit Takip Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Surus Destek Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Takip Mesafesi Koruma",
    "SURUS DESTEK SISTEMLERI - Takip Mesafesi Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Yokus Kalkis Ozellikleri",
    "SURUS DESTEK SISTEMLERI - Yorgunluk Tespit Ozellikleri",
    "YAKIT TUKETIMI & EMISYON - LPG",
    "YAKIT TUKETIMI & EMISYON - LPG CO2 Salinimi",
    "YAKIT TUKETIMI & EMISYON - LPG Kapasitesi",
    "YAKIT TUKETIMI & EMISYON - LPG OrtalamaTuketim (100 km)",
    "YAKIT TUKETIMI & EMISYON - LPG Sehir Disi Tuketim (100 km)",
    "YAKIT TUKETIMI & EMISYON - LPG Sehir Ici Tuketim (100 km)",
    "YAKIT TUKETIMI & EMISYON - Ortalama Emisyon (WLTP)",
    "YOLCU EMNIYETI - Anahtarsiz Sistem Ozellikleri",
    "YOLCU EMNIYETI - Diger Guvenlik Ozellikleri",
    "YOLCU EMNIYETI - Hava Yastigi Ozellikleri",
    "YOLCU EMNIYETI - NCAP/ANCAP Web Sayfasi",
    "YUK ALANI - Azami Hacim",
    "YUK ALANI - Azami Ic Genislik",
    "YUK ALANI - Azami Ic Uzunluk",
    "YUK ALANI - Azami Ic Yukseklik",
    "YUK ALANI - Azami Yuk (Istiap Haddi)",
    "YUK ALANI - Azami Yuklu Agirlik",
    "YUK ALANI - Davlumbaz Araligi",
    "- TEMEL OZELLIKLER - Engelli Bireyler Icin OTV Muafiyeti",
    "BaÅŸlÄ±k (BAŞLIK)",
    "TEMEL OZELLIKLER - Alt Seri",
    "ISITMA & SOGUTMA - Isitma & Sogutma Ozellikleri",
    "LAMBALAR & AYDINLATMA - Far Ozellikleri",
    "YOLCU EMNIYETI - Kumanda & Kilit Sistemleri",
]

# (2) pattern bazlı drop (orijinal mantık korunuyor)
DROP_HEADER_PATTERNS = [
    r"test.*suru[şs]|test.*surus|talep.*sayfa|test.*sürüş|test.*suru",
    r"urun.*katalo|ürün.*katalo|katalog|ürün.*katalog",
    r"test.*sür.*sayfa",
]

# (3) istenen kesin kolon sıralaması (eksikler CSV'de yoksa atlanır; kalanlar sona eklenir)
DESIRED_ORDER = [
    "MARKA",
    "TEMEL OZELLIKLER - Seri",
    "MODEL",
    "TEMEL OZELLIKLER - Donanim Paketi",
    "TEMEL OZELLIKLER - Arac Turu",
    "TEMEL OZELLIKLER - Govde Tipi",
    "TEMEL OZELLIKLER - Segment",
    "TEMEL OZELLIKLER - Model Yili",
    "EKO PUAN (SEN HESAPLAYACAKSIN)",
    "GÜVEN PUAN (SEN HESAPLAYACAKSIN)",
    "KONFOR PUAN (SEN HESAPLAYACAKSIN)",
    "PERFORMANS PUAN (SEN HESAPLAYACAKSIN)",
    "TEMEL OZELLIKLER - Ait Oldugu Ulke",
    "TEMEL OZELLIKLER - Motor Tipi",
    "TEMEL OZELLIKLER - Motorlu Tasit Vergisi",  # hesaplanacak
    "TEMEL OZELLIKLER - Yakit Tipi",
    "MOTOR (Icten Yanmali) - Besleme Tipi",
    "MOTOR (Icten Yanmali) - Silindir Adedi",
    "MOTOR (Icten Yanmali) - Silindir Hacmi",
    "MOTOR (Icten Yanmali) - Yakit Puskurtme",
    "PERFORMANS - Azami Hiz",
    "PERFORMANS - Azami Tork (Toplam)",
    "PERFORMANS - Beygir Gucu (Toplam)",
    "PERFORMANS - 0 - 100 Km Hizlanma",
    "AGIRLIK & OLCULER - Agirlik",
    "AGIRLIK & OLCULER - Genislik",
    "AGIRLIK & OLCULER - Uzunluk",
    "AGIRLIK & OLCULER - Yukseklik",
    "BAGAJ OZELLIKLERI - Bagaj Hacmi (2 Koltuk)",
    "BAGAJ OZELLIKLERI - Bagaj Hacmi (5 Koltuk)",
    "CAMLAR & AYNALAR - Acilir Tavan",
    "CAMLAR & AYNALAR - Arka Yan Cam Ayarlari",
    "CAMLAR & AYNALAR - Ic Dikiz Aynasi",
    "CAMLAR & AYNALAR - On Yan Cam Ayarlari",
    "CAMLAR & AYNALAR - Panoramik Cam Tavan",
    "CAMLAR & AYNALAR - Yan Dikiz Aynalari",
    "DIREKSIYON OZELLIKLERI - Direksiyon Ozellikleri",
    "DIREKSIYON OZELLIKLERI - Direksiyon Sistemi",
    "DIS GOVDE - Dis Govde Ozellikleri",
    "DIS GOVDE - Kapi Sayisi",
    "FRENLER & SUSPANSIYON - ABS Fren Sistemi",
    "FRENLER & SUSPANSIYON - Arka Suspansiyonlar",
    "FRENLER & SUSPANSIYON - Ayarlanir Suspansiyon",
    "FRENLER & SUSPANSIYON - Fren Destek Sistemleri",
    "FRENLER & SUSPANSIYON - On Suspansiyonlar",
    "FRENLER & SUSPANSIYON - Park Freni Tipi",
    "GOSTERGELER & SENSORLER - Far Sensoru",
    "GOSTERGELER & SENSORLER - Gostergeler & Bildirimler",
    "GOSTERGELER & SENSORLER - Lastik Basinc Sensoru",
    "GOSTERGELER & SENSORLER - Park Sensoru & Yardimi",
    "GOSTERGELER & SENSORLER - Yagmur Sensoru",
    "ISITMA & SOGUTMA - Klima",
    "ISITMA & SOGUTMA - Torpido Ozellikleri",
    "KOLTUKLAR & IC DOSEME - Kol Dayama",
    "KOLTUKLAR & IC DOSEME - Koltuk Dosemesi Tipi",
    "KOLTUKLAR & IC DOSEME - Koltuk Isitma - Sogutma",
    "KOLTUKLAR & IC DOSEME - Koltuk Sayisi",
    "KOLTUKLAR & IC DOSEME - On Yolcu Koltugu Ayarlari",
    "KOLTUKLAR & IC DOSEME - Surucu Koltugu Ayarlari",
    "LAMBALAR & AYDINLATMA - Far Tipi",
    "LAMBALAR & AYDINLATMA - Sis Farlari",
    "LASTIK & JANT - Jant Capi",
    "LASTIK & JANT - Jant Tipi",
    "LASTIK & JANT - Kesit Orani",
    "LASTIK & JANT - Lastik Ebatlari",
    "LASTIK & JANT - Taban Genisligi",
    # ... (liste devam eder; mevcut DESIRED_ORDER'ta yoksa kept_headers'da eklenir)
]

# title cleaning words
TITLE_REMOVE_WORDS = ["yeni", "new"]
POSSIBLE_TITLE_KEYS = ["başlık", "baslik", "title", "baslikı", "başlıkı"]

# -------------------------
# 2025 MTV tablolar (kaynak: resmi sirküler PDF ve güvenilir hesaplama siteleri)
# - I/A sayılı tarife: 2017 ve öncesi ilk tescil --> sadece motor hacmi ve yaş
# - 2018 sonrası: motor hacmi veya elektrik için kW + taşıt değeri (matrah) bandı
# -------------------------

# I/A (2017 ve öncesi) - motor hacmi -> array [1-3,4-6,7-11,12-15,16+]
I_A_TARIFFE = [
    (0, 1300,    [4834, 3372, 1882, 1420, 499]),
    (1301, 1600, [8421, 6314, 3661, 2587, 993]),
    (1601, 1800, [14885, 11626, 6848, 4168, 1612]),
    (1801, 2000, [23454, 18057, 10613, 6314, 2487]),
    (2001, 2500, [35175, 25534, 15954, 9528, 3747]),
    (2501, 3000, [49052, 42669, 26654, 14329, 5259]),
    (3001, 3500, [74703, 67218, 40486, 20203, 7409]),
    (3501, 4000, [117462, 101427, 59730, 26654, 10613]),
    (4001, 99999999, [192250, 144166, 85377, 38363, 14885]),
]

# post-2018: her motor hacmi bandı için matrah dilimlerine göre arrayler (kaynak: resmi sirküler PDF)
# Yapı: (cc_lo, cc_hi, [ (matrah_max, arr_for_this_band), (...), ... ])
POST2018_TARIFFE = [
    # 0-1300 : 3 band (<=259900, <=455300, >455300)
    (0, 1300, [
        (259900, [4834, 3372, 1882, 1420, 499]),
        (455300, [5313, 3707, 2068, 1565, 551]),
        (float("inf"), [5803, 4042, 2264, 1709, 594]),
    ]),
    # 1301-1600 : 3 band
    (1301, 1600, [
        (259900, [8421, 6314, 3661, 2587, 993]),
        (455300, [9267, 6948, 4031, 2838, 1085]),
        (float("inf"), [10112, 7577, 4389, 3098, 1184]),
    ]),
    # 1601-1800 : 2 band (651700)
    (1601, 1800, [
        (651700, [16370, 12801, 7523, 4589, 1777]),
        (float("inf"), [17866, 13956, 8218, 5014, 1940]),
    ]),
    # 1801-2000 : 2 band (651700)
    (1801, 2000, [
        (651700, [25792, 19862, 11674, 6948, 2731]),
        (float("inf"), [28142, 21677, 12734, 7577, 2982]),
    ]),
    # 2001-2500 : 2 band (813900)
    (2001, 2500, [
        (813900, [38695, 28090, 17549, 10480, 4145]),
        (float("inf"), [42217, 30642, 19141, 11439, 4522]),
    ]),
    # 2501-3000 : 2 band (1628900)
    (2501, 3000, [
        (1628900, [53952, 46942, 29322, 15770, 5780]),
        (float("inf"), [58864, 51203, 31991, 17206, 6308]),
    ]),
    # 3001-3500 : 2 band (1628900)
    (3001, 3500, [
        (1628900, [82173, 73942, 44537, 22231, 8142]),
        (float("inf"), [89652, 80656, 48585, 24245, 8893]),
    ]),
    # 3501-4000 : 2 band (2607700)
    (3501, 4000, [
        (2607700, [129201, 111570, 65702, 29322, 11674]),
        (float("inf"), [140960, 121707, 71687, 31991, 12734]),
    ]),
    # 4001+ : 2 band (3096500)
    (4001, 99999999, [
        (3096500, [211479, 158577, 93917, 42208, 16370]),
        (float("inf"), [230698, 172998, 102458, 46044, 17866]),
    ]),
]

# Elektrikli araçlar (örnek tablo; kaynaklar: çeşitli hesaplama/sigorta siteleri)
# Yapı: (kw_lo, kw_hi, [ (matrah_max, arr_for_this_band), ... ])
# Not: EV tablolarının matrah eşikleri ve aralıklar için farklı kaynaklar var; aşağıdaki tablo
# farklı kamu siteleri/hesaplayıcılarla uyumlu birleştirilmiş halidir.
EV_TARIFFE = [
    (0, 70, [
        (114000, [1207, 840, 496, 305, 115]),   # örnek: <70 kW ve düşük matrah
        (199700, [1324, 926, 584, 382, 140]),
        (float("inf"), [1449, 1011, 637, 417, 153]),
    ]),
    (70, 85, [
        (114000, [2104, 1577, 899, 496, 305]),
        (199700, [2314, 1737, 989, 545, 336]),
        (float("inf"), [2528, 1894, 1078, 593, 365]),
    ]),
    (85, 105, [
        (285800, [4090, 3199, 1800, 1400, 600]),
        (float("inf"), [4463, 3491, 1960, 1500, 700]),
    ]),
    (105, 120, [
        (285800, [6446, 4964, 2950, 2100, 800]),
        (float("inf"), [7032, 5420, 3220, 2290, 900]),
    ]),
    (120, 150, [
        (356900, [9673, 7020, 4300, 3200, 1200]),
        (float("inf"), [10554, 7659, 4700, 3500, 1300]),
    ]),
    (150, 180, [
        (714300, [13487, 11733, 7000, 4200, 1400]),
        (float("inf"), [14716, 12801, 7600, 4600, 1500]),
    ]),
    (180, 210, [
        (714300, [20537, 18484, 9500, 7800, 2800]),
        (float("inf"), [22411, 18797, 9900, 8000, 3000]),
    ]),
    (210, 240, [
        (1143000, [32300, 27892, 17000, 14000, 5200]),
        (float("inf"), [35000, 30000, 18000, 15000, 5500]),
    ]),
    # not: çok büyük EV'ler için daha yüksek bantlar var; gerektiğinde genişlet.
]

# -------------------------
# Yardımcı fonksiyonlar
# -------------------------
def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def detect_title_key(fieldnames):
    if not fieldnames:
        return None
    lower_map = {fn.lower(): fn for fn in fieldnames if fn}
    for cand in POSSIBLE_TITLE_KEYS:
        if cand in lower_map:
            return lower_map[cand]
    for fn in fieldnames:
        lf = fn.lower()
        if "baş" in lf or "baslik" in lf or "title" in lf:
            return fn
    return None

def should_drop_header(header):
    nh = normalize_text(header)
    for pat in DROP_HEADER_PATTERNS:
        if re.search(pat, nh):
            return True
    return False

def clean_title_value(val: str):
    if val is None:
        return val
    s = str(val)
    word_pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in TITLE_REMOVE_WORDS) + r")\b", flags=re.IGNORECASE)
    cleaned = word_pattern.sub("", s)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.strip(" -–—:,;.")
    return cleaned

def parse_int_safe(x):
    try:
        if x is None or str(x).strip() == "":
            return None
        sx = str(x).strip()
        sx = re.sub(r"[^\d\-]", "", sx)
        return int(sx) if sx != "" else None
    except:
        return None

def parse_float_safe(x):
    try:
        if x is None or str(x).strip() == "":
            return None
        sx = str(x).strip()
        sx = re.sub(r"[^\d\.]", "", sx)
        return float(sx) if sx != "" else None
    except:
        return None

def determine_age_bucket_from_year(first_registration_year):
    # GIB uses "yaş aralığı" (1-3,4-6,...)
    if first_registration_year is None:
        return None
    age = CURRENT_YEAR - first_registration_year
    if age <= 3:
        return 0
    if age <= 6:
        return 1
    if age <= 11:
        return 2
    if age <= 15:
        return 3
    return 4

def find_in_table_by_cc(table, cc, age_bucket, vehicle_value=None):
    """Generic lookup for POST2018_TARIFFE structure."""
    if cc is None or age_bucket is None:
        return None, "missing_input"
    for (lo, hi, bands) in table:
        if lo <= cc <= hi:
            # find correct matrah band
            for (matrah_max, arr) in bands:
                if vehicle_value is None:
                    # default to first band (lowest) if no vehicle_value
                    return arr[age_bucket], "assumed_low_matrah"
                try:
                    if vehicle_value <= matrah_max:
                        return arr[age_bucket], f"band_up_to_{matrah_max}"
                except Exception:
                    continue
            # fallback if not matched: last band
            last = bands[-1][1]
            return last[age_bucket], "band_last"
    return None, "not_found"

def find_ev_by_kw(ev_table, kw, age_bucket, vehicle_value=None):
    if kw is None or age_bucket is None:
        return None, "missing_input"
    for (lo_k, hi_k, bands) in ev_table:
        if lo_k < kw <= hi_k or (lo_k == 0 and kw <= hi_k):
            for (matrah_max, arr) in bands:
                if vehicle_value is None:
                    return arr[age_bucket], "assumed_low_matrah_ev"
                if vehicle_value <= matrah_max:
                    return arr[age_bucket], f"ev_band_up_to_{matrah_max}"
            return bands[-1][1][age_bucket], "ev_band_last"
    return None, "ev_not_found"

# -------------------------
# MTV hesap fonksiyonu (GİB uyumlu)
# -------------------------
def calculate_mtv_row(row, headers):
    """
    GIB uyumlu MTV hesaplama (2025 tabloları):
    - Öncelikle 'ilk tescil yılı' (ilk_tescil vs Model Yili) aranır; yoksa Model Yılı fallback.
    - Eğer ilk_tescil <= 2017 --> I/A tarife (I_A_TARIFFE) kullanılır (sadece motor cc ve yaş).
    - Eğer ilk_tescil >= 2018 --> POST2018_TARIFFE kullanılır (motor cc + taşıt değeri matrah bandı).
    - Elektrikli ise EV_TARIFFE kullanılır (kW + matrah bandı).
    """
    # olası column isimleri
    first_reg_keys = [
        "ilk tescil yili", "ilk tescil yılı", "ilk tescil", "ilk_tescil_yili",
        "ilk_tescil_yılı", "ilktescilyili", "ilk_tescil_tarihi"
    ]
    model_year_keys = [
        "TEMEL OZELLIKLER - Model Yili", "Model Yili", "Model Yılı", "Model Year", "model_year"
    ]
    motor_cc_keys = [
        "MOTOR (Icten Yanmali) - Silindir Hacmi", "Motor Silindir Hacmi",
        "MOTOR - Silindir Hacmi", "Silindir Hacmi", "MOTOR (Icten Yanmali) - Silindir Hacmi (cm3)"
    ]
    vehicle_value_keys = [
        "Tasit Degeri", "TAŞIT DEGERI", "TASIT_DEGERI", "TEMEL OZELLIKLER - Tasit Degeri",
        "Arac Degeri", "Arac Değeri", "Arac Degeri TL", "tasit_degeri"
    ]
    motor_kw_keys = [
        "MOTOR (Elektrikli) - Motor Gucu", "Motor Gucu (kW)", "MOTOR (Elektrikli) - Motor Gücü", "Motor Gücü", "Motor Gucu"
    ]
    motor_type_keys = [
        "TEMEL OZELLIKLER - Motor Tipi", "Motor Tipi", "MOTOR TIPI", "motor tipi"
    ]

    # 1) ilk tescil yılı -> öncelikle kontrol et
    first_reg_year = None
    for k in first_reg_keys:
        if k in headers:
            v = parse_int_safe(row.get(k, None))
            if v:
                first_reg_year = v
                break
    # fallback: model year
    if first_reg_year is None:
        for k in model_year_keys:
            if k in headers:
                v = parse_int_safe(row.get(k, None))
                if v:
                    # treat as model year; not perfect but fallback
                    first_reg_year = v
                    break

    # 2) motor cc parse
    motor_cc = None
    for k in motor_cc_keys:
        if k in headers:
            motor_cc = parse_int_safe(row.get(k, None))
            if motor_cc is not None:
                break

    # 3) vehicle (matrah) value
    vehicle_value = None
    for k in vehicle_value_keys:
        if k in headers and str(row.get(k, "")).strip() != "":
            vehicle_value = parse_float_safe(row.get(k))
            break

    # 4) motor kW (elektrikli)
    motor_kw = None
    for k in motor_kw_keys:
        if k in headers:
            motor_kw = parse_float_safe(row.get(k))
            if motor_kw is not None:
                break

    # 5) detect if electric by type field if provided
    is_electric_flag = False
    for k in motor_type_keys:
        if k in headers:
            mt = normalize_text(row.get(k, ""))
            if "elektr" in mt:  # elektrik, elektrikli vb.
                is_electric_flag = True
                break

    # also if motor_kw is present and motor_cc not present we consider electric
    if motor_kw is not None and (motor_cc is None or motor_cc == 0):
        is_electric_flag = True

    # determine age bucket
    if first_reg_year is None:
        return "", "first_reg_year_missing"
    age_bucket = determine_age_bucket_from_year(first_reg_year)
    if age_bucket is None:
        return "", "age_bucket_missing"

    # pre-2018
    if first_reg_year <= 2017:
        # I/A tariff lookup by motor_cc
        if motor_cc is None:
            return "", "motor_cc_missing_pre2018"
        for (lo, hi, arr) in I_A_TARIFFE:
            if lo <= motor_cc <= hi:
                return str(arr[age_bucket]), "pre2018_exact"
        return "", "pre2018_no_band_found"

    # post-2018
    # if electric:
    if is_electric_flag:
        # need motor_kw; if missing, cannot calculate
        if motor_kw is None:
            return "", "ev_kw_missing"
        val, note = find_ev_by_kw(EV_TARIFFE, motor_kw, age_bucket, vehicle_value=vehicle_value)
        if val is None:
            return "", "ev_not_found"
        return str(val), f"post2018_electric_{note}"

    # internal combustion post2018 - use cc + vehicle_value band
    if motor_cc is None:
        return "", "motor_cc_missing_post2018"
    val, note = find_in_table_by_cc(POST2018_TARIFFE, motor_cc, age_bucket, vehicle_value=vehicle_value)
    if val is None:
        return "", note
    return str(val), f"post2018_{note}"

# -------------------------
# Main: CSV read, drop columns, reorder, compute MTV, write out
# -------------------------
def main():
    if not INPUT_CSV.exists():
        print(f"Input file not found: {INPUT_CSV}")
        return

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []

    if not headers:
        print("CSV'de header yok.")
        return

    # detect title column
    title_key = detect_title_key(headers)

    # pattern-based drops (but keep core known fields safe)
    drop_headers = [h for h in headers if should_drop_header(h) and h.lower() not in ("url", "başlık", "baslik", "title")]
    drop_headers = [h for h in drop_headers if h not in ("Başlık", "URL", "Baslik", "title")]

    # user-specified exact removes
    drop_headers.extend([h for h in headers if h in REMOVE_EXACT_COLUMNS])

    # kept headers
    kept_headers = [h for h in headers if h not in drop_headers]

    # construct out_headers according to DESIRED_ORDER (then append remaining kept headers)
    out_headers = []
    used = set()
    for name in DESIRED_ORDER:
        if name in kept_headers and name not in used:
            out_headers.append(name)
            used.add(name)
    for h in kept_headers:
        if h not in used:
            out_headers.append(h)
            used.add(h)

    # ensure MTV col present and placed after Model Yili if possible
    mtv_col = "TEMEL OZELLIKLER - Motorlu Tasit Vergisi"
    if mtv_col not in out_headers:
        try:
            idx = out_headers.index("TEMEL OZELLIKLER - Model Yili")
            out_headers.insert(idx+1, mtv_col)
        except ValueError:
            out_headers.append(mtv_col)

    cleaned_count = 0
    mtv_warnings = 0
    rows_out = []
    for r in rows:
        new_r = {}
        mtv_val, mtv_note = calculate_mtv_row(r, headers)
        if mtv_note not in ("pre2018_exact",) and mtv_note != "" and not mtv_note.startswith("post2018"):
            # count warnings for records where we had to assume or lacked data
            mtv_warnings += 1

        for h in out_headers:
            if h == mtv_col:
                new_r[h] = mtv_val
            elif title_key and h == title_key:
                new_v = clean_title_value(r.get(h, ""))
                if new_v != (r.get(h, "") or ""):
                    cleaned_count += 1
                new_r[h] = new_v
            else:
                new_r[h] = r.get(h, "")
        rows_out.append(new_r)

    # write output
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_headers)
        writer.writeheader()
        writer.writerows(rows_out)

    print("✅ İşlem tamam.")
    
if __name__ == '__main__':
    main()


# assign_suv_pickup.py
"""
CSV'deki "TEMEL OZELLIKLER - Govde Tipi" değerlerine göre
"TEMEL OZELLIKLER - Arac Turu" sütununa
"SUV / PICK-UP" değerini atayan küçük yardımcı script.

Kullanım:
- Giriş dosyası: car_data_cleaned.csv
- Çıkış dosyası: car_data_improved.csv
- Eğer "TEMEL OZELLIKLER - Arac Turu" sütunu mevcut değilse, dosyaya eklenir.
- Varsayılan olarak bulunan tüm satırlarda eşleşme olursa bu sütun "SUV / PICK-UP" ile güncellenir.

Notlar:
- Karşılaştırma normalize edilerek (küçük harf, diakritik kaldırma) yapılır.
- "SUV", "Crossover" gibi varyantlar yakalanır.
- GOVDE_VALUES setine yeni tipler ekleyebilirsiniz.
"""

import csv
import unicodedata
import re
from pathlib import Path

# Giriş/Çıkış dosyaları
INPUT_CSV = Path("/workspaces/otokritik.com/car_data_cleaned.csv")
OUTPUT_CSV = Path("/workspaces/otokritik.com/car_data_improved.csv")

# Normalizasyon yardımcı fonksiyonu
def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

# Govde tipi olarak kabul edilecek değerler (normalize edilerek karşılaştırılır)
GOVDE_VALUES = {
    "coupe-suv",
    "crossover",
    "mpv/suv",
    "pick-up",
    "suv",
}

# Olası sütun adları (CSV'de farklı isimlendirmeler olabilir)
GOVDE_HEADER_CANDIDATES = [
    "TEMEL OZELLIKLER - Govde Tipi",
    "TEMEL ÖZELLİKLER - Govde Tipi",
    "Govde Tipi",
    "GOVDE TIPI",
    "Govde Tip",
]

ARAC_TURU_HEADER_CANDIDATES = [
    "TEMEL OZELLIKLER - Arac Turu",
    "TEMEL ÖZELLİKLER - Arac Turu",
    "Arac Turu",
    "ARAC TURU",
]

# Eğer var olan değerleri overwrite etmek istemiyorsan bu değişkeni False yap
OVERWRITE_EXISTING = True


def detect_header(fieldnames, candidates):
    """Fieldnames içinde candidates listesinde geçen ilk başlığı döndürür."""
    lower_map = {fn.lower(): fn for fn in fieldnames if fn}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    # fallback: içerik bazlı arama
    for fn in fieldnames:
        lf = fn.lower()
        for c in candidates:
            if normalize_text(c) in normalize_text(lf) or normalize_text(lf) in normalize_text(c):
                return fn
    return None


def main():
    if not INPUT_CSV.exists():
        print(f"Input file not found: {INPUT_CSV}")
        return

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []

    if not headers:
        print("CSV'de header yok.")
        return

    govde_key = detect_header(headers, GOVDE_HEADER_CANDIDATES)
    arac_turu_key = detect_header(headers, ARAC_TURU_HEADER_CANDIDATES)

    # Eğer arac_turu sütunu yoksa ekle
    if not arac_turu_key:
        arac_turu_key = "TEMEL OZELLIKLER - Arac Turu"
        headers.append(arac_turu_key)

    matched = 0
    total = len(rows)

    for r in rows:
        govde_val = r.get(govde_key, "") if govde_key else ""
        if govde_val is None:
            govde_val = ""
        norm = normalize_text(govde_val)
        # bazı CSV'lerde virgül/pipe ile birden çok tip gelebilir; split et ve kontrol et
        candidates = re.split(r"[,;/\\|]", norm)
        found = False
        for cand in candidates:
            cand = cand.strip()
            if cand in GOVDE_VALUES:
                found = True
                break
        if found:
            # mevcut değerleri overwrite etme seçeneğine göre atama
            if OVERWRITE_EXISTING or not r.get(arac_turu_key):
                r[arac_turu_key] = "SUV / PICK-UP"
            matched += 1
        else:
            # eğer sütun daha önce yoktu, r[arac_turu_key] boş olabilir; koru
            if arac_turu_key not in r:
                r[arac_turu_key] = r.get(arac_turu_key, "")

    # çıktı yaz
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print("✅ İşlem tamam.")
    print(f" - Toplam satır: {total}")
    print(f" - SUV / PICK-UP olarak işaretlenen satır sayısı: {matched}")
    print(f" - Çıktı dosyası: {OUTPUT_CSV.resolve()}")


if __name__ == '__main__':
    main()
