#!/usr/bin/env python3
import pandas as pd
import os

IN = "car_data_missing_data_fix_11.csv"

# Mapping of BASLIK -> Sehir Ici Menzil
menzil_map = {
    "Fiat Topolino 8.2 HP (4x2)": "75 km",
    "Fiat Topolino Plus 8.2 HP (4x2)": "75 km",
    "Citroen Ami One Electric 8 HP (4x2)": "75 km",
    "2025 BYD Dolphin 204 HP Comfort (4x2)": "559 km",
    "2025 BYD Dolphin 204 HP Design (4x2)": "559 km",
    "2024 Fiat 500e HB 118 HP La Prima (4x2)": "400 km",
    "2024 Opel Corsa Elektrik 136 HP GS (4x2)": "492 km",
    "2024 Renault 5 E-Tech 150 HP (4x2)": "600 km",
    "2017 Renault ZOE 92 BG ZEN": "400 km",
    "2018 Renault ZOE 92 BG ZEN": "400 km",
    "2019 Renault ZOE 92 BG Life": "395 km",
    "2015 Renault ZOE 88 BG ZEN": "240 km",
    "2024 Renault ZOE E-Tech 135 BG Intense (4x2)": "395 km",
    "2024 Citroen e-C4 136 HP Shine Bold (4x2)": "468 km",
    "2024 Citroen e-C4 156 HP Shine Bold (4x2)": "560 km",
    "2024 Citroen e-C4 X 136 HP Shine Bold (4x2)": "461 km",
    "2024 Citroen e-C4 X 156 HP Shine Bold (4x2)": "565 km",
    "2024 MG MG4 167 HP Comfort (4x2)": "450 km",
    "2024 MG MG4 204 HP Luxury (4x2)": "435 km",
    "2024 MG MG4 435 HP XPOWER (4x4)": "385 km",
    "2018 Nissan Leaf 147 BG Otomatik": "270 km",
    "2024 Opel Astra Elektrik 156 HP Ultimate (4x2)": "418 km",
    "2024 Peugeot E-308 156 HP GT (4x2)": "510 km",
    "2024 Hyundai IONIQ 5 170 PS Progressive (4x2)": "507 km",
    "2024 Hyundai IONIQ 5 325 PS Progressive (4x4)": "481 km",
    "2024 MG Marvel R 288 PS (4x4)": "402 km",
    "2018 BMW i3 170 BG Otomatik": "290 km",
    "2015 BMW i3 170 BG Otomatik": "190 km",
    "2016 BMW i3 170 BG Otomatik": "190 km",
    "2017 BMW i3 170 BG Otomatik": "290 km",
    "2024 Mini Cooper SE 184 PS (4x2)": "402 km",
    "Opel Combo Elektrik 136 HP Edition": "458 km",
    "2024 BYD Seal 530 HP (4x4)": "520 km",
    "2024 Hyundai IONIQ 6 151 BG Progressive (4x2)": "614 km",
    "2024 Hyundai IONIQ 6 325 BG Progressive (4x4)": "583 km",
    "2024 Tesla Model 3 283 HP (4x2)": "513 km",
    "2024 Tesla Model 3 Long Range AWD 498 HP (4x4)": "629 km",
    "2024 Audi e-tron GT Quattro 530 BG (4x4)": "499 km",
    "2024 Audi RS e-tron GT Quattro 530 BG (4x4)": "504 km",
    "BYD Han 510 HP (4x4)": "662 km",
    "2023 Tesla Model S 670 HP (4x4)": "634 km",
    "2023 Tesla Model S Plaid 1020 HP (4x4)": "600 km",
    "2024 Kia EV6 229 PS Prestige Long Range (4x2)": "528 km",
    "2024 Kia EV6 325 PS GT-Line Long Range (4x4)": "484 km",
    "2024 Kia EV6 585 PS GT Long Range (4x4)": "424 km",
    "2024 Renault Megane E-Tech 220 HP Iconic (4x2)": "470 km",
    "2024 Renault Megane E-Tech 220 HP Techno (4x2)": "470 km",
    "2024 Tesla Cybertruck 600 HP (4x4)": "547 km",
    "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": "515 km",
    "2024 Dacia Spring 65 BG Extreme (4x2)": "310 km",
    "2025 Hyundai INSTER Advance 115 BG (4X2)": "493 km",
    "2024 Citroen e-C3 113 BG (4x2)": "320 km",
    "2024 Kia EV3 204 PS Otomatik Elegance St.Menzil (4x2)": "583 km",
    "2024 Kia EV3 204 PS Otomatik Elegance Uz.Menzil (4x2)": "772 km",
    "2024 Kia EV3 204 PS Otomatik GT-Line Uz.Menzil (4x2)": "755 km",
    "2024 Kia EV3 204 PS Otomatik Prestige Uz.Menzil (4x2)": "772 km",
    "2024 MG ZS EV Luxury 156 HP (4x2)": "320 km",
    "2025 Opel Frontera Elektrik 111 HP Edition (4x2)": "300 km (estimated)",
    "2024 Opel Mokka Elektrik 136 BG Ultimate (4x2)": "450 km",
    "2024 Peugeot E-2008 156 HP Active Prime (4x2)": "406 km",
    "2024 Peugeot E-2008 156 HP Allure (4x2)": "406 km",
    "2024 Peugeot E-2008 156 HP GT (4x2)": "406 km",
    "2024 Volvo EX30 272 HP (4x2)": "480 km",
    "2024 BYD Atto 3 Design 201 HP (4x2)": "565 km",
    "2024 Kia Niro EV 204 PS Elegance (4x2)": "460 km",
    "2024 Mercedes EQA 250+ 190 BG AMG+ (4x2)": "560 km",
    "2024 Mercedes EQA 350 4MATIC 292 BG AMG+ (4x4)": "497 km",
    "2025 Opel Grandland Elektrik 210 HP GS (4x2)": "700 km",
    "2025 Peugeot E-3008 GT 210 HP (4x2)": "525 km",
    "2025 Peugeot E-3008 Allure 210 HP (4x2)": "525 km",
    "2025 Tesla Model Y Long Range 340 HP (4x2)": "600 km",
    "2025 Tesla Model Y Long Range 514 HP (4x4)": "565 km",
    "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "533 km",
    "2023 Tesla Model Y Performance 534 HP (4x4)": "514 km",
    "2023 Tesla Model Y Standart 299 HP (4x2)": "455 km",
    "2024 Volvo C40 Recharge Ultimate 252 HP (4x2)": "580 km",
    "2024 Volvo C40 Recharge Ultimate 408 HP (4x4)": "551 km",
    "2024 Volvo XC40 Recharge P8 252 HP Ultimate (4x2)": "786 km",
    "2024 Volvo XC40 Recharge P8 408 HP Ultimate (4x4)": "660 km",
    "2025 BYD Seal U EV Design 218 HP (4x2)": "674 km",
    "2024 Volvo EX90 408 HP (4x4)": "585 km",
    "2023 Tesla Model X 670 HP (4x4)": "576 km",
    "2023 Tesla Model X Plaid 1020 HP (4x4)": "543 km",
    "2024 Mercedes EQB 250+ 190 BG AMG+ (4x2)": "536 km",
    "2024 Mercedes EQB 350 4MATIC 292 BG AMG+ (4x4)": "468 km"
}

# Define the target column for updates
target_column = "MOTOR (Elektrikli) - Menzil (WLTP - Sehir Ici)"

try:
    # Read the CSV into a pandas DataFrame
    df = pd.read_csv(IN, low_memory=False)

    # Use the .replace() method on the target column, applying the menzil_map.
    # The 'loc' method is safer for updating based on conditions.
    # For each row where 'BASLIK' is in menzil_map, update the 'target_column'.
    df.loc[df["BASLIK"].isin(menzil_map.keys()), target_column] = \
        df["BASLIK"].map(menzil_map)

    # Save the modified DataFrame back to the original CSV file
    df.to_csv(IN, index=False, encoding="utf-8")

    print(f"Successfully updated '{target_column}' in '{IN}' for {len(menzil_map)} entries.")

except FileNotFoundError:
    print(f"Error: The file '{IN}' was not found.")
except KeyError as e:
    print(f"Error: A required column was not found. Please check 'BASLIK' or '{target_column}'. Detail: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# The TMP file is no longer needed with this pandas approach,
# so no os.replace or TMP variable is necessary.


############################################################################

############################################################################


import csv

IN = "car_data_missing_data_fix_11.csv"
TMP = IN + ".tmp"

# Torque data to add
data = {
"2015 Mini Cooper 3 Kapi 1.5 136 BG Steptronic": "7.8 saniye",
"2015 Audi A5 Coupe 2.0 TDI 177 HP Multitronic": "7.8 saniye",
"2015 Audi A5 Coupe 2.0 TDI 190 HP Multitronic": "7.8 saniye",
"2016 Audi A5 Coupe 2.0 TDI 190 HP Multitronic": "7.8 saniye",
"Fiat Topolino 8.2 HP (4x2)": "10 saniye",
"Fiat Topolino Plus 8.2 HP (4x2)": "10 saniye",
"Citroen Ami One Electric 8 HP (4x2)": "10 saniye",
"2017 Ford Ka+ 1.2 Durateq 69 PS": "13.3 saniye",
"2014 Volkswagen Polo 1.4 TSI ACT BMT 150 PS DSG BlueGT": "7.8 saniye",
"2016 Volkswagen Polo 1.4 TSI ACT BMT 150 PS DSG BlueGT": "7.8 saniye",
"2018 Nissan Leaf 147 BG Otomatik": "7.9 saniye",
"2018 Mini Cooper 3K 1.5 136 BG Steptronic": "7.8 saniye",
"2016 Mini Cooper 3K 1.5 136 BG Steptronic": "7.8 saniye",
"2017 Mini Cooper 3K 1.5 136 BG Steptronic": "7.8 saniye",
"2015 Mini Cooper 5 Kapi 1.5 136 BG Steptronic": "7.8 saniye",
"2018 Fiat Fiorino Panorama 1.3 Mjet 80 HP Otomatik Premio": "13.9 saniye",
"2018 Fiat Fiorino Panorama 1.3 Mjet 95 HP Pop": "13.9 saniye",
"2018 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio": "13.9 saniye",
"2018 Fiat Fiorino Panorama 1.3 Mjet 95 HP Safeline": "13.9 saniye",
"2019 Fiat Fiorino Panorama 1.3 Mjet 80 HP Otomatik Premio": "13.9 saniye",
"2019 Fiat Fiorino Panorama 1.3 Mjet 95 HP Pop": "13.9 saniye",
"2019 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio": "13.9 saniye",
"2020 Fiat Fiorino Panorama 1.3 Mjet 95 HP Pop": "13.9 saniye",
"2020 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio": "13.9 saniye",
"2016 Fiat Fiorino Panorama 1.3 Mjet 75 HP Emotion": "16 saniye",
"2016 Fiat Fiorino Panorama 1.3 Mjet 75 HP Pop": "16 saniye",
"2016 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio": "13.9 saniye",
"2017 Fiat Fiorino Panorama 1.3 Mjet 75 HP Emotion": "16 saniye",
"2017 Fiat Fiorino Panorama 1.3 Mjet 75 HP Pop": "16 saniye",
"2017 Fiat Fiorino Panorama 1.3 Mjet 95 HP Premio": "13.9 saniye",
"2019 BMW 520i 1.6 170 BG Steptronic Luxury Line": "7.8 saniye",
"2020 BMW 520i 1.6 170 BG Steptronic Luxury Line": "7.8 saniye",
"2020 BMW 520i 1.6 170 BG Steptronic M Sport": "7.8 saniye",
"2015 Mercedes E 250 BlueTEC 2.2 204 BG 4MATIC 7G-Tronic EditionE (4x4)": "7.8 saniye",
"2016 Mercedes E 250 BlueTEC 2.2 204 BG 4MATIC 7G-Tronic EditionE (4x4)": "7.8 saniye",
"2015 Volvo S80 2.4 D5 215 HP Geartronic Advance (4x4)": "7.8 saniye",
"2014 Volvo S80 D5 215 HP AWD Geartronic Advance (4x4)": "7.8 saniye",
"2015 Audi A4 2.0 TDI 190 HP Quattro S tronic (4x4)": "7.8 saniye",
"2016 Audi A5 Sportback 2.0 TDI 190 HP Multitronic": "7.8 saniye",
"2017 Ford Ranger 2.2 TDCi 160 PS Otomatik XLT (4x2)": "12.0 saniye",
"2017 Ford Ranger 2.2 TDCi 160 PS Otomatik XLT (4x4)": "12.0 saniye",
"2017 Ford Ranger 2.2 TDCi 160 PS XLT (4x2)": "12.0 saniye",
"2017 Ford Ranger 2.2 TDCi 160 PS XLT (4x4)": "12.0 saniye",
"2017 Ford Ranger 3.2 TDCi 200 PS Otomatik Wildtrak (4x4)": "10.4 saniye",
"2018 Mitsubishi L200 2.4 DI-D 154 BG Storm (4x4)": "12.0 saniye",
"2018 Mitsubishi L200 2.4 DI-D 181 BG Otomatik Blizzard (4x4)": "11.8 saniye",
"2018 Mitsubishi L200 2.4 DI-D 181 BG Otomatik Tornado (4x4)": "11.8 saniye",
"2018 Mitsubishi L200 2.4 DI-D 181 BG Tornado (4x4)": "11.8 saniye",
"2017 Mitsubishi L200 2.4 DI-D 154 BG Otomatik Storm (4x2)": "12.0 saniye",
"2017 Mitsubishi L200 2.4 DI-D 154 BG Storm (4x2)": "12.0 saniye",
"2017 Mitsubishi L200 2.4 DI-D 154 BG Storm (4x4)": "12.0 saniye",
"2017 Mitsubishi L200 2.4 DI-D 181 BG Otomatik Blizzard (4x4)": "11.8 saniye",
"2017 Mitsubishi L200 2.4 DI-D 181 BG Otomatik Tornado (4x4)": "11.8 saniye",
"2017 Mitsubishi L200 2.4 DI-D 181 BG Tornado (4x4)": "11.8 saniye",
"2017 Toyota Hilux 2.4 Dizel 150 PS Active (4x2)": "12.8 saniye",
"2018 Toyota Hilux 2.4 Dizel 150 PS Active (4x2)": "12.8 saniye",
"2018 Toyota Hilux 2.4 Dizel 150 PS Adventure (4x2)": "12.8 saniye",
"2018 Toyota Hilux 2.4 Dizel 150 PS Adventure (4x4)": "12.8 saniye",
"2018 Toyota Hilux 2.4 Dizel 150 PS Otomatik Adventure (4x2)": "12.8 saniye",
"2018 Toyota Hilux 2.4 Dizel 150 PS Otomatik Hi-Cruiser (4x4)": "12.8 saniye",
"2017 Suzuki Jimny 1.3 VVT 85 BG Otomatik Style (4x4)": "14.1 saniye",
"2018 Suzuki Jimny 1.5 102 PS Otomatik GLX (4x4)": "12.6 saniye",
"2016 Suzuki Jimny 1.3 VVT 85 BG Otomatik JLX (4x4)": "14.1 saniye",
"2016 Suzuki Jimny 1.3 VVT 85 BG Otomatik Style (4x4)": "14.1 saniye",
"2024 Kia Niro EV 204 PS Elegance (4x2)": "7.8 saniye",
"2018 Volvo XC90 D5 2.0 235 HP Geartronic Inscription (4x4)": "7.8 saniye",
"2018 Volvo XC90 D5 2.0 235 HP Geartronic Momentum (4x4)": "7.8 saniye",
"2018 Volvo XC90 D5 2.0 235 HP Geartronic R-Design (4x4)": "7.8 saniye",
"2019 Volvo XC90 D5 2.0 235 HP Geartronic Inscription (4x4)": "7.8 saniye",
"2019 Volvo XC90 D5 2.0 235 HP Geartronic Momentum (4x4)": "7.8 saniye",
"2019 Volvo XC90 D5 2.0 235 HP Geartronic R-Design (4x4)": "7.8 saniye",
"2015 Volvo XC90 D5 2.0 225 HP AWD Otomatik Inscription (4x4)": "7.8 saniye",
"2015 Volvo XC90 D5 2.0 225 HP AWD Otomatik Momentum (4x4)": "7.8 saniye",
"2015 Volvo XC90 D5 2.0 225 HP AWD Otomatik R-Design (4x4)": "7.8 saniye",
"2016 Volvo XC90 D5 2.0 225 HP AWD Otomatik Inscription (4x4)": "7.8 saniye",
"2016 Volvo XC90 D5 2.0 225 HP AWD Otomatik Momentum (4x4)": "7.8 saniye",
"2018 Mercedes GLS 350d 3.0 CDI 258 BG 4MATIC 9G-Tronic Power (4x4)": "7.8 saniye",
"2016 Mercedes GLS 350d 3.0 CDI 258 BG 4MATIC 9G-Tronic Power (4x4)": "7.8 saniye",
"2017 Mercedes GLS 350d 3.0 CDI 258 BG 4MATIC 9G-Tronic Power (4x4)": "7.8 saniye",
"2017 Ford Transit Custom Kombi 310S 2.0 TDCi 170 PS Otomatik Deluxe (5+1)": "11.7 saniye",
"2017 Ford Transit Custom Kombi 310S 2.2 TDCi 125 PS Trend (5+1)": "13.5 saniye",
"2017 Ford Transit Custom Kombi 310S 2.2 TDCi 155 PS Deluxe (5+1)": "12.4 saniye",
"2017 Ford Transit Custom Kombi Van 310S 2.2 TDCi 125 PS Trend (5+1)": "13.5 saniye",
"2017 Ford Transit Custom Kombi Van 310S 2.2 TDCi 155 PS Deluxe (5+1)": "12.4 saniye",
"2018 Ford Transit Courier Kombi Van 1.5 TDCi 75 PS Trend": "14.0 saniye",
"2016 Ford Transit Courier Kombi Van 1.5 TDCi 75 PS Trend": "14.0 saniye",
"2017 Ford Transit Courier Kombi Van 1.5 TDCi 75 PS Trend": "14.0 saniye",
"2018 Fiat Ducato Minibus City 2.3 130 HP (13+1)": "15.7 saniye",
"2018 Fiat Ducato Minibus City 2.3 130 HP (16+1)": "15.7 saniye",
"2017 Fiat Ducato Minibus City 2.3 130 HP (13+1)": "15.7 saniye",
"2017 Fiat Ducato Minibus City 2.3 130 HP (16+1)": "15.7 saniye",
"2018 Fiat Ducato Minibus Delux 2.3 130 HP (16+1)": "15.7 saniye",
"2017 Fiat Ducato Minibus Delux 2.3 130 HP (16+1)": "15.7 saniye",
"2018 Fiat Ducato Minibus Technolux 2.3 130 HP (16+1)": "15.7 saniye",
"2017 Fiat Ducato Minibus Technolux 2.3 130 HP (16+1)": "15.7 saniye",
"2017 Ford Tourneo Custom 300L 2.2 TDCi 125 PS Trend": "13.5 saniye",
"2017 Ford Tourneo Custom 300L 2.2 TDCi 155 PS Titanium": "12.4 saniye",
"2017 Ford Tourneo Custom 300S 2.2 TDCi 125 PS Trend": "13.5 saniye",
"2018 Ford Tourneo Custom 320L 2.0 TDCi 130 PS Trend": "13.5 saniye",
"2018 Ford Tourneo Custom 320L 2.0 TDCi 170 PS Otomatik Titanium Plus (Bagajli)": "11.7 saniye",
"2018 Ford Tourneo Custom 320L 2.0 TDCi 170 PS Otomatik Titanium Plus": "11.7 saniye",
"2018 Ford Tourneo Custom 320L 2.0 TDCi 170 PS Otomatik Titanium": "11.7 saniye",
"2018 Ford Tourneo Custom 320L 2.0 TDCi 170 PS Titanium Plus (Bagajli)": "11.7 saniye",
"2018 Ford Tourneo Custom 320L 2.0 TDCi 170 PS Titanium": "11.7 saniye",
"2018 Ford Tourneo Custom 320S 2.0 TDCi 130 PS Trend": "13.5 saniye",
"2018 Ford Tourneo Custom 320S 2.0 TDCi 170 PS Otomatik Titanium Plus": "11.7 saniye",
"2018 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (10+1)": "15.6 saniye",
"2018 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (11+1)": "15.6 saniye",
"2018 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (14+1 Bagajli)": "15.6 saniye",
"2018 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (14+1)": "15.6 saniye",
"2018 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (16+1)": "15.6 saniye",
"2018 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (17+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (16+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (17+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (14+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (11+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe Turizm (10+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Deluxe (14+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Trend (16+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Trend (17+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Trend (14+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Trend (11+1)": "15.6 saniye",
"2017 Ford Transit Minibus 2.2 TDCi 155 PS Trend (14+1)": "15.6 saniye",
"2018 Ford Transit Minibus 460ED 2.2 TDCi 155 PS Deluxe (16+1)": "15.6 saniye",
"2018 Ford Transit Minibus 460ED 2.2 TDCi 155 PS Deluxe (17+1)": "15.6 saniye",
"2017 Ford Transit Minibus 460ED 2.2 TDCi 155 PS Deluxe (16+1)": "15.6 saniye",
"2017 Ford Transit Minibus 460ED 2.2 TDCi 155 PS Deluxe (17+1)": "15.6 saniye",
"2017 Ford Transit Minibus 460ED 2.2 TDCi 155 PS Trend (16+1)": "15.6 saniye",
"2017 Ford Transit Minibus 460ED 2.2 TDCi 155 PS Trend (17+1)": "15.6 saniye",
"2017 Mercedes Sprinter Okul 316 CDI 2.2 163 BG Comfort E.Uzun (19+1)": "12.0 saniye",
"2017 Mercedes Sprinter Okul 316 CDI 2.2 163 BG Comfort Plus E.Uzun (19+1)": "12.0 saniye",
"2017 Mercedes Sprinter Okul 316 CDI 2.2 163 BG Comfort Plus Uzun (16+1)": "12.0 saniye",
"2017 Mercedes Sprinter Okul 316 CDI 2.2 163 BG Comfort Uzun (16+1)": "12.0 saniye",
"2017 Mercedes Sprinter Okul 416 CDI 2.2 163 BG Comfort E.Uzun (19+1)": "12.0 saniye",
"2017 Mercedes Sprinter Okul 416 CDI 2.2 163 BG Comfort Plus E.Uzun (19+1)": "12.0 saniye",
"2018 Mercedes Sprinter Servis 316 CDI 2.2 163 BG Comfort Plus Uzun (14+1)": "12.0 saniye",
"2018 Mercedes Sprinter Servis 316 CDI 2.2 163 BG Comfort Plus Uzun (15+1)": "12.0 saniye",
"2018 Mercedes Sprinter Servis 316 CDI 2.2 163 BG Comfort Uzun (14+1)": "12.0 saniye",
"2018 Mercedes Sprinter Servis 316 CDI 2.2 163 BG Comfort Uzun (16+1)": "12.0 saniye",
"2018 Mercedes Sprinter Servis 416 CDI 2.2 163 BG Comfort E.Uzun (19+1)": "12.0 saniye",
"2018 Mercedes Sprinter Servis 416 CDI 2.2 163 BG Comfort Plus E.Uzun (19+1)": "12.0 saniye",
"2018 Renault Master Minibus Okul 2.3 dCi 125 BG Elegance (16+1)": "13.0 saniye",
"2018 Renault Master Minibus Servis 2.3 dCi 125 BG Elegance (16+1)": "13.0 saniye",
"2017 Volkswagen Crafter Okul E.U.Sasi 2.0 BiTDI 163 PS (18+1)": "11.0 saniye",
"2017 Volkswagen Crafter Okul E.U.Sasi 2.0 BiTDI 163 PS (19+1)": "11.0 saniye",
"2017 Volkswagen Crafter Okul E.U.Sasi 2.0 BiTDI 163 PS (22+1)": "11.0 saniye",
"2017 Volkswagen Crafter Okul U.Sasi 2.0 BiTDI 163 PS (16+1)": "11.0 saniye",
"2017 Volkswagen Crafter Servis E.U.Sasi 2.0 BiTDI 163 PS (16+1)": "11.0 saniye",
"2017 Volkswagen Crafter Servis E.U.Sasi 2.0 BiTDI 163 PS (19+1)": "11.0 saniye",
"2017 Volkswagen Crafter Servis U.Sasi 2.0 BiTDI 163 PS (14+1)": "11.0 saniye",
"2017 Volkswagen Crafter Servis U.Sasi 2.0 BiTDI 163 PS (15+1)": "11.0 saniye",
"2018 Citroen Jumper Van L4H2 2.0 HDI 130 HP (15 m3)": "15.6 saniye",
"2018 Citroen Jumper Van L4H2 2.2 HDI 150 HP (15 m3)": "15.6 saniye",
"2017 Citroen Jumper Van L4H2 2.0 HDI 130 HP (15 m3)": "15.6 saniye",
"2017 Citroen Jumper Van L4H2 2.2 HDI 150 HP (15 m3)": "15.6 saniye",
"2018 Fiat Ducato Van 2.3 Multijet 130 HP (8m3)": "15.7 saniye",
"2017 Fiat Ducato Van 2.3 Multijet 130 HP (8m3)": "15.7 saniye",
"2018 Fiat Ducato Van Maxi 2.3 Multijet 130 HP (11.5m3)": "15.7 saniye",
"2018 Fiat Ducato Van Maxi 2.3 Multijet 130 HP (13m3)": "15.7 saniye",
"2018 Fiat Ducato Van Maxi 2.3 Multijet 130 HP (15m3)": "15.7 saniye",
"2018 Fiat Ducato Van Maxi 2.3 Multijet 130 HP (17m3)": "15.7 saniye",
"2017 Fiat Ducato Van Maxi 2.3 Multijet 130 HP (11.5m3)": "15.7 saniye",
"2017 Fiat Ducato Van Maxi 2.3 Multijet 130 HP (13m3)": "15.7 saniye",
"2017 Fiat Ducato Van Maxi 2.3 Multijet 130 HP (15m3)": "15.7 saniye",
"2017 Fiat Ducato Van Maxi 2.3 Multijet 130 HP (17m3)": "15.7 saniye",
"2018 Ford Transit Custom Van 2.0 TDCi 105 PS Trend (320S)": "13.5 saniye",
"2018 Ford Transit Custom Van 2.0 TDCi 130 PS Trend (340L)": "12.4 saniye",
"2018 Ford Transit Custom Van 2.0 TDCi 130 PS Trend (340S)": "12.4 saniye",
"2018 Ford Transit Custom Van 2.0 TDCi 170 PS Otomatik Trend (340S)": "11.7 saniye",
"2017 Ford Transit Custom Van 310S 2.2 TDCi 100 PS Trend": "14.0 saniye",
"2017 Ford Transit Custom Van 330L 2.2 TDCi 125 PS Trend": "13.5 saniye",
"2017 Ford Transit Custom Van 330L O.T. 2.2 TDCi 125 PS Trend": "13.5 saniye",
"2017 Ford Transit Custom Van 330S O.T. 2.2 TDCi 125 PS Trend": "13.5 saniye",
"2018 Ford Transit Custom Van O.Tavan 2.0 TDCi 130 PS Trend (340L)": "12.4 saniye",
"2018 Ford Transit Van 2.0 TDCi 130 PS Trend (10m3 L2H2)": "12.4 saniye",
"2018 Ford Transit Van 2.0 TDCi 130 PS Trend (9.5m3 L2H2)": "12.4 saniye",
"2018 Ford Transit Van 2.0 TDCi 170 PS Otomatik Trend (10m3 L2H2)": "11.7 saniye",
"2018 Ford Transit Van 2.0 TDCi 170 PS Otomatik Trend (11.5m3 L3H2)": "11.7 saniye",
"2018 Ford Transit Van 2.0 TDCi 170 PS Trend (11.5m3 L3H2)": "11.7 saniye",
"2018 Ford Transit Van 2.0 TDCi 170 PS Trend (11m3 L3H2)": "11.7 saniye",
"2018 Ford Transit Van 2.0 TDCi 170 PS Trend (12.4m3 L3H3)": "11.7 saniye",
"2018 Ford Transit Van 2.0 TDCi 170 PS Trend (13m3 L3H3)": "11.7 saniye",
"2017 Ford Transit Van 2.0 TDCi 170 PS Otomatik Trend (10m3)": "11.7 saniye",
"2017 Ford Transit Van 2.0 TDCi 170 PS Otomatik Trend (11.5m3)": "11.7 saniye",
"2017 Ford Transit Van 2.2 TDCi 125 PS Trend (9.5m3)": "13.5 saniye",
"2017 Ford Transit Van 2.2 TDCi 125 PS Trend (10m3)": "13.5 saniye",
"2017 Ford Transit Van 2.2 TDCi 155 PS Trend (11.5m3)": "12.4 saniye",
"2017 Ford Transit Van 2.2 TDCi 155 PS Trend (11m3)": "12.4 saniye",
"2017 Ford Transit Van 2.2 TDCi 155 PS Trend (12.4m3)": "12.4 saniye",
"2017 Ford Transit Van 2.2 TDCi 155 PS Trend (13m3)": "12.4 saniye",
"2018 Mercedes Sprinter Panelvan 314CDi 2.2 143 BG (10.5m3) 3500KG": "12.0 saniye",
"2018 Mercedes Sprinter Panelvan 314CDi 2.2 143 BG (14.0m3) 3500KG": "12.0 saniye",
"2018 Mercedes Sprinter Panelvan 314CDi 2.2 143 BG (9.0m3) 3500KG": "12.0 saniye",
"2017 Mercedes Sprinter Panelvan 314CDi 2.2 143 BG (10.5m3) 3500KG": "12.0 saniye",
"2017 Mercedes Sprinter Panelvan 314CDi 2.2 143 BG (9.0m3) 3500KG": "12.0 saniye",
"2017 Mercedes Sprinter Panelvan 314CDi 2.2 143 BG (14.0m3) 3500KG": "12.0 saniye",
"2018 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (10.5m3) 3500KG": "12.0 saniye",
"2018 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (10.5m3) 4050KG": "12.0 saniye",
"2018 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (14.0m3) 3500KG": "12.0 saniye",
"2018 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (15.5m3) 4050KG": "12.0 saniye",
"2018 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (9.0m3) 3500KG": "12.0 saniye",
"2017 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (10.5m3) 3500KG": "12.0 saniye",
"2017 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (9.0m3) 3500KG": "12.0 saniye",
"2017 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (10.5m3) 4050KG": "12.0 saniye",
"2017 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (14.0m3) 3500KG": "12.0 saniye",
"2017 Mercedes Sprinter Panelvan 316CDi 2.2 163 BG (15.5m3) 4050KG": "12.0 saniye",
"2017 Peugeot Boxer Van L3H2 2.2 HDi 130 HP (13 m3)": "15.0 saniye",
"2018 Peugeot Boxer Van L3H2 2.2 HDi 130 HP (13 m3)": "15.0 saniye",
"2017 Peugeot Boxer Van L4H2 2.0 BlueHDi 160 HP (15 m3)": "12.0 saniye",
"2017 Peugeot Boxer Van L4H2 2.2 HDi 130 HP (15 m3)": "15.0 saniye",
"2017 Peugeot Boxer Van L4H2 2.2 HDi 150 HP (15 m3)": "12.0 saniye",
"2018 Peugeot Boxer Van L4H2 2.0 BlueHDi 160 HP (15 m3)": "12.0 saniye",
"2018 Peugeot Boxer Van L4H2 2.2 HDi 130 HP (15 m3)": "15.0 saniye",
"2018 Peugeot Boxer Van L4H2 2.2 HDi 150 HP (15 m3)": "12.0 saniye",
"2017 Peugeot Boxer Van L4H3 2.2 HDi 150 HP (17 m3)": "12.0 saniye",
"2018 Peugeot Boxer Van L4H3 2.2 HDi 150 HP (17 m3)": "12.0 saniye",
"2017 Renault Master P.Van L2H2 2.3 dCi 125 BG 3.5T (11 m3)": "13.0 saniye",
"2018 Renault Master P.Van L2H2 2.3 dCi 125 BG 3.5T (11 m3)": "13.0 saniye",
"2017 Renault Master P.Van L3H2 2.3 dCi 125 BG 3.5T (13 m3)": "13.0 saniye",
"2018 Renault Master P.Van L3H2 2.3 dCi 125 BG 3.5T (13 m3)": "13.0 saniye",
"2017 Renault Master P.Van L4H2 2.3 dCi 125 BG 3.5T (15 m3)": "13.0 saniye",
"2017 Renault Master P.Van L4H3 2.3 dCi 165 BG 3.5T S&S (17 m3)": "12.0 saniye",
"2017 Renault Master P.Van L4H3 2.3 dCi 125 BG 4.5T (17 m3)": "13.0 saniye",
"2017 Renault Master P.Van L4H3 2.3 dCi 165 BG 4.5T S&S (17 m3)": "12.0 saniye",
"2018 Renault Master P.Van L4H3 2.3 dCi 165 BG 3.5T S&S (17 m3)": "12.0 saniye",
"2018 Renault Master P.Van L4H3 2.3 dCi 165 BG 4.5T S&S (17 m3)": "12.0 saniye",
"2017 Volkswagen Crafter Panelvan 2.0 BiTDI 163 PS (3.5 Ton)": "11.0 saniye",
"2017 Volkswagen Crafter Panelvan 2.0 BiTDI 163 PS (3.88 Ton)": "11.0 saniye",
"2018 Volkswagen Crafter Panelvan S.Tavan 2.0 TDI 140 PS Comfort (3.5T)": "13.5 saniye",
"2018 Volkswagen Crafter Panelvan Y.Tavan 2.0 BITDI 177 PS Comfort Plus (3.5T Uzun)": "11.0 saniye",
"2018 Volkswagen Crafter Panelvan Y.Tavan 2.0 TDI 140 PS Comfort (3.5T Uzun)": "13.5 saniye",
"2018 Volkswagen Crafter Panelvan Y.Tavan 2.0 TDI 140 PS Comfort (3.5T)": "13.5 saniye",
"2016 Citroen Nemo Panelvan 1.3 HDi 75 HP X": "14.9 saniye",
"2016 Fiat Fiorino Cargo 1.3 Mjet 75 HP Cargo Plus": "16.0 saniye",
"2016 Fiat Fiorino Cargo 1.3 Mjet 75 HP Cargo": "16.0 saniye",
"2017 Fiat Fiorino Cargo 1.3 Mjet 75 HP Cargo Plus": "16.0 saniye",
"2017 Fiat Fiorino Cargo 1.3 Mjet 75 HP Cargo": "16.0 saniye",
"2018 Ford Transit Courier Van 1.5 TDCi 75 PS Trend": "14.0 saniye",
"2018 Ford Transit Courier Van 1.5 TDCi 95 PS Deluxe": "12.0 saniye",
"2018 Ford Transit Courier Van 1.5 TDCi 75 PS Trend": "14.0 saniye",
"2018 Ford Transit Courier Van 1.5 TDCi 95 PS Deluxe": "12.0 saniye",
"2016 Ford Transit Courier Van 1.5 TDCi 75 PS Trend": "14.0 saniye",
"2016 Ford Transit Courier Van 1.6 TDCi 95 PS Deluxe": "12.0 saniye",
"2017 Ford Transit Courier Van 1.5 TDCi 75 PS Trend": "14.0 saniye",
"2017 Ford Transit Courier Van 1.6 TDCi 95 PS Deluxe": "12.0 saniye",
"2016 Peugeot Bipper Van 1.3 HDi 75 HP": "14.9 saniye"
}

with open(IN, newline="", encoding="utf-8") as f, open(TMP, "w", newline="", encoding="utf-8") as o:
    r = csv.DictReader(f)
    w = csv.DictWriter(o, fieldnames=r.fieldnames)
    w.writeheader()
    for row in r:
        if row["BASLIK"] in data:
            row["PERFORMANS - 0 - 100 Km Hizlanma"] = data[row["BASLIK"]]
        w.writerow(row)

import os
os.replace(TMP, IN)




############################################################################

############################################################################




import csv
import os

IN = "car_data_missing_data_fix_11.csv"
TMP = IN + ".tmp"

targets_to_remove = [
    "2017 Ford Ka+ 1.2 Durateq 69 PS",
    "2017 Ford GT 3.5 V6 Ecoboost 600 HP Otomatik"
]

# --- Count initial rows ---
initial_row_count = 0
try:
    with open(IN, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        initial_row_count = sum(1 for row in reader)
    print(f"Initial row count in '{IN}': {initial_row_count}")
except FileNotFoundError:
    print(f"Error: The file '{IN}' was not found.")
    exit() # Exit if the file doesn't exist

rows_removed_count = 0
try:
    with open(IN, newline="", encoding="utf-8") as f, \
         open(TMP, "w", newline="", encoding="utf-8") as o:
        r = csv.DictReader(f)
        w = csv.DictWriter(o, fieldnames=r.fieldnames)
        w.writeheader()
        for row in r:
            if row["BASLIK"] not in targets_to_remove:
                w.writerow(row)
            else:
                rows_removed_count += 1

    os.replace(TMP, IN)

    # --- Count final rows ---
    final_row_count = 0
    with open(IN, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        final_row_count = sum(1 for row in reader)

    print(f"\nProcessing complete for '{IN}'.")
    print(f"Number of rows identified for removal: {rows_removed_count}")
    print(f"Final row count in '{IN}': {final_row_count}")

    if initial_row_count - rows_removed_count == final_row_count:
        print("SUCCESS: The specified rows have been removed successfully and the file updated.")
    else:
        print("WARNING: Row counts do not perfectly match expected removal. Please verify the file manually.")

except Exception as e:
    print(f"An error occurred during processing: {e}")

# Optional: Clean up the temporary file if something went wrong before os.replace
if os.path.exists(TMP):
    os.remove(TMP)




############################################################################

############################################################################



import csv

IN = "car_data_missing_data_fix_11.csv"
TMP = IN + ".tmp"

# Torque data to add
data ={
  "2018 Toyota Hilux 2.4 Dizel 150 PS Adventure (4x2)": "Adventure",
  "2018 Toyota Hilux 2.4 Dizel 150 PS Adventure (4x4)": "Adventure",
  "2018 Toyota Hilux 2.4 Dizel 150 PS Otomatik Adventure (4x2)": "Adventure",
  "2019 Citroen C5 Aircross 1.5 BlueHDi 130 HP EAT8 Adventure (4x2)": "Adventure",
  "2017 Subaru Forester 2.0 240 PS Turbo CVT AWD Adventure (4x4)": "Adventure",
  "2015 Subaru Forester 2.0 240 PS Turbo CVT AWD Adventure (4x4)": "Adventure",
  "2016 Subaru Forester 2.0 240 PS Turbo CVT AWD Adventure (4x4)": "Adventure",
  "2014 Subaru Forester 2.0L Turbo 150 PS CVT AWD Adventure (4x4)": "Adventure",
  "2017 Renault Kangoo Multix 1.5 dCi 110 BG Extrem": "Extrem",
  "2017 Renault Kangoo Multix 1.5 dCi 90 BG Extrem": "Extrem",
  "2015 Renault Kangoo Multix 1.5 dCi 110 BG Extrem": "Extrem",
  "2015 Renault Kangoo Multix 1.5 dCi 90 BG Extrem": "Extrem",
  "2016 Renault Kangoo Multix 1.5 dCi 110 BG Extrem": "Extrem",
  "2016 Renault Kangoo Multix 1.5 dCi 90 BG Extrem": "Extrem",
  "2014 BMW 220d Coupe 184 BG": "Luxury Line",
  "2018 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "Pure Impulse",
  "2015 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "Pure Impulse",
  "2016 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "Pure Impulse",
  "2017 BMW i8 Hibrit 1.5 362 BG Otomatik (4x4)": "Pure Impulse",
  "Citroen Ami One Electric 8 HP (4x2)": "My Ami Pop",
  "2024 Renault 5 E-Tech 150 HP (4x2)": "Techno",
  "2014 Fiat Bravo 1.4 MULTIAIR 16V 140 HP SPORT": "Sport",
  "2014 Fiat Bravo 1.4 T-JET 16V 120 HP EASY": "Easy",
  "2014 Fiat Bravo 1.6 MULTIJET 120 HP DualogicTM SPORT": "Sport",
  "2014 Fiat Bravo 1.6 MULTIJET 120 HP EASY": "Easy",
  "2016 Ford Focus ST 2.0 EcoBoost 250 HP S&S": "ST",
  "2018 Nissan Leaf 147 BG Otomatik": "Tekna",
  "2024 MG Marvel R 288 PS (4x4)": "Performance",
  "2019 BMW 116d 1.5 116 BG Otomatik": "Sport Line",
  "2019 BMW 118i 1.5 136 BG Otomatik": "Sport Line",
  "2018 BMW i3 170 BG Otomatik": "Loft",
  "2024 Mini Cooper SE 184 PS (4x2)": "Classic",
  "2014 Peugeot 3008 1.6 e-HDi 115 HP ETG6 S&S Allure (4x2)": "Allure",
  "2014 Peugeot 3008 1.6 e-HDi 115 HP ETG6 S&S Feline (4x2)": "Feline",
  "2014 BMW 218i 136 PS Active Tourer": "Luxury Line",
  "2017 Mercedes B 180 1.6 122 PS 7G-DCT": "Style",
  "2017 Mercedes B 180d 1.5 109 PS 7G-DCT": "Style",
  "2017 Mercedes B 200 1.6 156 PS 7G-DCT": "Style",
  "2021 Renault Megane Sedan 1.0 TCe 115 BG": "Joy",
  "2021 Renault Megane Sedan 1.3 TCe 140 BG EDC": "Icon",
  "2021 Renault Megane Sedan 1.3 TCe 140 BG": "Icon",
  "2021 Renault Megane Sedan 1.5 Blue dCi 115 BG EDC": "Icon",
  "2021 Renault Megane Sedan 1.5 Blue dCi 115 BG": "Joy",
  "2024 BYD Seal 530 HP (4x4)": "Excellence AWD",
  "2015 Honda Accord 2.0 156 PS Executive": "Executive",
  "2016 Honda Accord 2.0 156 PS Otomatik Executive": "Executive",
  "2024 Tesla Model 3 283 HP (4x2)": "Rear-Wheel Drive",
  "2024 Tesla Model 3 Long Range AWD 498 HP (4x4)": "Long Range AWD",
  "2024 Audi e-tron GT Quattro 530 BG (4x4)": "Quattro",
  "2024 Audi RS e-tron GT Quattro 530 BG (4x4)": "RS",
  "2018 BMW 520d 2.0 190 BG Steptronic": "Luxury Line",
  "2018 BMW 520d 2.0 190 BG xDrive Steptronic (4x4)": "Luxury Line",
  "2017 BMW 520d 2.0 190 BG Steptronic": "Luxury Line",
  "2017 BMW 520d 2.0 190 BG xDrive Steptronic (4x4)": "Luxury Line",
  "2018 BMW 520i 1.6 170 BG Steptronic": "Luxury Line",
  "2018 BMW 530i 2.0 252 BG Steptronic": "Luxury Line",
  "2018 BMW 530i 2.0 252 BG xDrive Steptronic (4x4)": "Luxury Line",
  "2017 BMW 530i 2.0 252 BG Steptronic": "Luxury Line",
  "2017 BMW 530i 2.0 252 BG xDrive Steptronic (4x4)": "Luxury Line",
  "2018 BMW 540i 3.0 340 BG xDrive Steptronic (4x4)": "M Sport",
  "BYD Han 510 HP (4x4)": "Excellence AWD",
  "2018 BMW 730i 2.0 258 BG Otomatik": "Pure Excellence",
  "2018 BMW 730Li 2.0 258 BG Otomatik": "Pure Excellence",
  "2018 BMW 740Ld 3.0 320 BG xDrive Otomatik (4x4)": "Pure Excellence",
  "2018 BMW 750Ld 3.0 400 BG xDrive Otomatik (4x4)": "Pure Excellence",
  "2019 BMW 318i 1.5 136 BG Steptronic Edition Sport Line": "Sport Line",
  "2019 BMW 320d 2.0 190 BG Steptronic Premium Line": "Premium Line",
  "2019 Volvo S60 T5 2.0 254 HP Geartronic": "Inscription",
  "2023 Tesla Model S 670 HP (4x4)": "Dual Motor AWD",
  "2023 Tesla Model S Plaid 1020 HP (4x4)": "Plaid",
  "2024 Tesla Cybertruck 600 HP (4x4)": "All-Wheel Drive",
  "2024 Tesla Cybertruck Cyberbeast 845 HP (4x4)": "Cyberbeast",
  "2024 Citroen e-C3 113 BG (4x2)": "Max",
  "2014 Opel Mokka 1.4 140 BG Cosmo (4x2)": "Cosmo",
  "2014 Opel Mokka 1.4 140 BG S&S Cosmo (4x4)": "Cosmo",
  "2014 Opel Mokka 1.4 140 BG S&S Enjoy (4x4)": "Enjoy",
  "2014 Opel Mokka 1.6 115 BG Cosmo (4x2)": "Cosmo",
  "2014 Opel Mokka 1.6 115 BG Enjoy (4x2)": "Enjoy",
  "2024 Volvo EX30 272 HP (4x2)": "Plus Single Motor",
  "2025 Tesla Model Y Long Range 340 HP (4x2)": "Long Range Rear-Wheel Drive",
  "2025 Tesla Model Y Long Range 514 HP (4x4)": "Long Range All-Wheel Drive",
  "2023 Tesla Model Y Long Range AWD 345 HP (4x4)": "Long Range AWD",
  "2023 Tesla Model Y Performance 534 HP (4x4)": "Performance",
  "2023 Tesla Model Y Standart 299 HP (4x2)": "Rear-Wheel Drive",
  "2018 BMW X3 sDrive20i 1.6 170 BG Otomatik (4x2)": "xLine",
  "2017 BMW X3 sDrive20i 1.6 170 BG Otomatik (4x2)": "xLine",
  "2017 BMW X3 xDrive20d 2.0 190 BG Otomatik (4x4)": "xLine",
  "2018 BMW X3 xDrive20d 2.0 190 BG Otomatik (4x4)": "xLine",
  "2016 Ford Edge 2.0 TDCi 210 HP PowerShift (4x4)": "Titanium",
  "2018 Audi Q8 50 3.0 TDI 286 HP Quattro Tiptronic (4x4)": "S line",
  "2018 BMW X5 xDrive25d 2.0 231 BG Otomatik (4x4)": "xLine",
  "2017 BMW X5 xDrive40e iPerformance 2.0 313 BG Otomatik (4x4)": "xLine",
  "2017 Maserati Levante 3.0 350 HP AWD Otomatik (4x4)": "GranLusso",
  "2024 Volvo EX90 408 HP (4x4)": "Twin Motor",
  "2023 Tesla Model X 670 HP (4x4)": "Dual Motor AWD",
  "2023 Tesla Model X Plaid 1020 HP (4x4)": "Plaid",
  "2018 BMW X1 sDrive16d 1.5 116 BG (4x2)": "Advantage",
  "2016 BMW X1 sDrive16d 1.5 116 BG (4x2)": "Advantage",
  "2017 BMW X1 sDrive16d 1.5 116 BG (4x2)": "Advantage",
  "2018 BMW X1 sDrive18i 1.5 136 BG Steptronic (4x2)": "Advantage",
  "2016 BMW X1 sDrive18i 1.5 136 BG Otomatik (4x2)": "Advantage",
  "2017 BMW X1 sDrive18i 1.5 136 BG Steptronic (4x2)": "Advantage",
  "2018 BMW X1 xDrive20d 2.0 190 BG Steptronic (4x4)": "xLine",
  "2016 BMW X1 xDrive20d 2.0 190 BG (4x4)": "xLine",
  "2017 BMW X1 xDrive20d 2.0 190 BG Steptronic (4x4)": "xLine",
  "2018 BMW X2 sDrive18i 140 BG Steptronic (4x2)": "Advantage",
  "2024 Mercedes EQB 250+ 190 BG AMG+ (4x2)": "AMG Line",
  "2024 Mercedes EQB 350 4MATIC 292 BG AMG+ (4x4)": "AMG Line",
  "2014 BMW X3 sDrive20i 170 BG Otomatik (4x2)": "xLine",
  "2016 BMW X3 sDrive20i 1.6 170 BG Otomatik (4x2)": "xLine",
  "2017 BMW X3 sDrive20i 1.6 170 BG Otomatik (4x2)": "xLine",
  "2014 BMW X3 xDrive20d 190 BG Otomatik (4x4)": "xLine",
  "2016 BMW X3 xDrive20d 2.0 190 BG Otomatik (4x4)": "xLine",
  "2017 BMW X3 xDrive20d 2.0 190 BG Otomatik (4x4)": "xLine"
}

with open(IN, newline="", encoding="utf-8") as f, open(TMP, "w", newline="", encoding="utf-8") as o:
    r = csv.DictReader(f)
    w = csv.DictWriter(o, fieldnames=r.fieldnames)
    w.writeheader()
    for row in r:
        if row["BASLIK"] in data:
            row["TEMEL OZELLIKLER - Donanim Paketi"] = data[row["BASLIK"]]
        w.writerow(row)

import os
os.replace(TMP, IN)


############################################################################
#❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌
############################################################################
#✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
############################################################################
############################################################################
#❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌
############################################################################
#✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
############################################################################


'''

import csv

IN = "car_data_missing_data_fix_11.csv"
OUT = "car_data_missing_data_fix_12.csv"

keep_always = {"BASLIK", "TEMEL OZELLIKLER - Yakit Tipi"}

with open(IN, newline="", encoding="utf-8") as f:
    r = list(csv.DictReader(f))

# Determine columns to keep
columns = r[0].keys()
keep = []
for col in columns:
    if col in keep_always:
        keep.append(col)
    else:
        if any(row[col].strip() == "" for row in r):
            keep.append(col)

# Write filtered CSV
with open(OUT, "w", newline="", encoding="utf-8") as o:
    w = csv.DictWriter(o, fieldnames=keep)
    w.writeheader()
    for row in r:
        w.writerow({c: row[c] for c in keep})

print("✅ Cleaned file saved as:", OUT)



'''

############################################################################
#❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌
############################################################################
#✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
############################################################################
############################################################################
#❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌
############################################################################
#✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
############################################################################


