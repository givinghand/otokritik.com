#!/usr/bin/env python3
"""
compare_models.py

Compare a CSV data pool against a reference brand->models checklist and
report which models are missing from the data pool.

Designed to run in GitHub Codespaces / any Python3 environment.

Usage:
    python compare_models.py --input car_data.csv --output missing_models_report.csv

Options:
    --input/-i        Input CSV (default: car_data.csv)
    --output/-o       Output report CSV (default: missing_models_report.csv)
    --brand-col       Column name for brand (default: "TEMEL BILGILER - Marka")
    --model-col       Column name for model (default: "TEMEL BILGILER - Model")
    --partial         If set, allow substring matches (helps with variants)
    --verbose/-v      Print progress messages

The script normalizes text (lowercase, strip, remove accents) before matching.
"""

import argparse
import csv
import sys
import re
import unicodedata
from collections import defaultdict

try:
    import pandas as pd
except Exception as e:
    print("This script requires pandas. Install with: pip install pandas", file=sys.stderr)
    raise


CHECK = {
    "Alfa Romeo": ["Giulia","Giulia Quadrifoglio","Giulietta","Junior Elettrica","Junior Ibrida","Stelvio","Tonale"],
    "Aston Martin": ["DB11","DB9","DBS","Rapide","Vanquish","Vantage","DBX"],
    "Audi": ["A1","A3","A4","A5","A6","A6 E-Tron","A7","A8","E-Tron GT","R8","E-Tron","E-Tron Sportback","Q2","Q3","Q3 Sportback","Q4 E-tron","Q4 Sportback","Q5","Q5 Sportback","Q6 E-tron","Q7","Q8","Q8 E-tron","Q8 E-tron Sportback","RS Q8","SQ7","S Serisi"],
    "Bentley": ["Continental","Flying Spur","Bentayga"],
    "BMW": ["1 Serisi","2 Serisi","3 Serisi","4 Serisi","5 Serisi","6 Serisi","7 Serisi","8 Serisi","i SERİSİ","M SERİSİ","Z SERİSİ","iX SERİSİ","iX1 SERİSİ","iX2 SERİSİ","iX3 SERİSİ","X1 SERİSİ","X2 SERİSİ","X3 SERİSİ","X4 SERİSİ","X5 SERİSİ","X6 SERİSİ","X7 SERİSİ","i ","M ","Z ","iX ","iX1 ","iX2 ","iX3 ","X1 ","X2 ","X3 ","X4 ","X5 ","X6 ","X7 "],
    "BYD": ["Dolphin","Han","Seal","Atto 3","Atto 3 EV","Seal U","Seal U EV","Tang"],
    "Cadillac": ["Escalade"],
    "Chery": ["Omoda5","Omoda5 Pro","Tiggo8","Tiggo7","Tiggo7 Pro","Tiggo7 Pro Max","Tiggo8 Pro","Tiggo8 Pro Max"],
    "Chevrolet": ["Camaro","Corvette","Silverado"],
    "Citroën": ["AMI","C-Elysée","C1","C3","e-C3","C4","C4 Grand Picasso","C4 Picasso","C4 X","e-C4","e-C4 X","C5","C3 AirCross","C3 AirCross Elektrik","C4 Cactus","C5 AirCross","Berlingo","Jumper","Jumpy","Nemo"],
    "Cupra": ["Born","Leon","Ateca","Formentor","Terramar"],
    "Dacia": ["Jogger","Lodgy","Logan","Sandero","Sandero Stepway","Duster","Spring","Dokker"],
    "Dodge": ["Challenger","Charger","Ram"],
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
    "TOGG": ["T10X", "T10F"],
}


def normalize_text(s):
    """Lowercase, strip, remove accents, collapse spaces."""
    if s is None:
        return ""
    s = str(s)
    s = s.strip().lower()
    # remove diacritics
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    # collapse whitespace
    s = re.sub(r'\s+', ' ', s)
    return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', '-i', default='car_data.csv', help='Input CSV file')
    p.add_argument('--output', '-o', default='missing_models_report.csv', help='Output CSV report')
    p.add_argument('--brand-col', default='TEMEL BILGILER - Marka', help='Brand column name')
    p.add_argument('--model-col', default='TEMEL BILGILER - Model', help='Model column name')
    p.add_argument('--partial', action='store_true', help='Allow substring matching for models')
    p.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = p.parse_args()
    # ---- FORCE the script to use the exact input/output and brand/model names from your provided script ----
    # This ensures the script uses your files without requiring CLI flags.
    args.input = 'CAR_DATA_FINAL_3.csv'
    args.output = 'CAR_DATA_FINAL_4_MISS.csv'
    args.brand_col = 'MARKA'
    args.model_col = 'MODEL'
    # ------------------------------------------------------------------------------------------

    if args.verbose:
        print(f"Loading input: {args.input}")

    try:
        # CSV from Excel / regional exports uses semicolon as separator — use that by default.
        # Use python engine and on_bad_lines='warn' to tolerate a few malformed rows.
        df = pd.read_csv(args.input, dtype=str, sep=';', engine='python', encoding='utf-8', on_bad_lines='warn')
    except Exception as e:
        print(f"Failed to read {args.input}: {e}", file=sys.stderr)
        sys.exit(2)

    # check columns
    if args.brand_col not in df.columns or args.model_col not in df.columns:
        print("Input CSV doesn't contain expected columns. Found columns:\n", file=sys.stderr)
        for c in df.columns:
            print(c)
        print(f"\nExpected brand column: {args.brand_col}\nExpected model column: {args.model_col}", file=sys.stderr)
        sys.exit(3)

    # build normalized lookup
    df['_brand_norm'] = df[args.brand_col].apply(normalize_text)
    df['_model_norm'] = df[args.model_col].apply(normalize_text)

    # group models by brand in the data pool
    brand_to_models = defaultdict(set)
    for _, row in df.iterrows():
        brand = row['_brand_norm']
        model = row['_model_norm']
        if brand and model:
            brand_to_models[brand].add(model)

    # helper to check presence
    def model_found(brand_name, model_name):
        bnorm = normalize_text(brand_name)
        mnorm = normalize_text(model_name)
        # direct brand match
        found_in_brand = False
        if bnorm in brand_to_models:
            for m in brand_to_models[bnorm]:
                if m == mnorm:
                    return True, 'exact_in_brand'
                if args.partial and mnorm in m:
                    return True, 'partial_in_brand(m contains)'
                if args.partial and m in mnorm:
                    return True, 'partial_in_brand(m contained)'
        # fallback: search all models regardless of brand
        for b, models in brand_to_models.items():
            for m in models:
                if m == mnorm:
                    return True, f'exact_in_other_brand({b})'
                if args.partial and (mnorm in m or m in mnorm):
                    return True, f'partial_in_other_brand({b})'
        return False, 'not_found'

    rows = []
    total_checked = 0
    missing_counts = defaultdict(int)
    present_counts = defaultdict(int)

    for brand, model_list in CHECK.items():
        for model in model_list:
            total_checked += 1
            found, reason = model_found(brand, model)
            rows.append({
                'brand': brand,
                'model': model,
                'found': found,
                'reason': reason,
            })
            if found:
                present_counts[brand] += 1
            else:
                missing_counts[brand] += 1

    report_df = pd.DataFrame(rows)

    # Create new rows for missing brand/model entries and append to the original data pool
    missing_df = report_df[report_df['found'] == False].copy()
    total_missing = missing_df.shape[0]

    # build new rows with only brand/model filled, other columns empty (NaN)
    new_rows = []
    for _, r in missing_df.iterrows():
        # create a dict with all original columns set to NA, then set brand/model
        new_row = {c: pd.NA for c in df.columns}
        new_row[args.brand_col] = r['brand']
        new_row[args.model_col] = r['model']
        new_rows.append(new_row)

    if new_rows:
        new_rows_df = pd.DataFrame(new_rows)
        # drop internal norm columns before concatenation if present
        base_df = df.drop(columns=['_brand_norm', '_model_norm'], errors='ignore')
        final_df = pd.concat([base_df, new_rows_df], ignore_index=True)
    else:
        final_df = df.drop(columns=['_brand_norm', '_model_norm'], errors='ignore')

    # save combined CSV (preserve semicolon separator)
    final_df.to_csv(args.output, index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC)

    # minimal console summary
    print(f'Total models checked: {total_checked}')
    print(f'Total missing: {total_missing}')
    print(f"Final CSV with appended missing rows saved to: {args.output}")

if __name__ == '__main__':
    main()
