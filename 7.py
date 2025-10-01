import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# === CONFIG ===
INPUT_CSV = "CAR_DATA_MIXED.csv"   # your file
OUTPUT_EXCEL = "CAR_DATA_MIXED.csv"   # result file

# Load CSV
df = pd.read_csv(INPUT_CSV)

# Save to Excel first
df.to_excel(OUTPUT_EXCEL, index=False)

# Open with openpyxl
wb = load_workbook(OUTPUT_EXCEL)
ws = wb.active

# Yellow fill for missing values
yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

# Iterate over dataframe to highlight NaNs
for row in range(2, len(df) + 2):  # +2 because Excel rows start at 1 and header is first row
    for col in range(1, len(df.columns) + 1):
        if df.iloc[row - 2, col - 1] != df.iloc[row - 2, col - 1]:  # NaN check
            ws.cell(row=row, column=col).fill = yellow_fill

# Save highlighted Excel
wb.save(OUTPUT_EXCEL)

print(f"✅ Missing values highlighted and saved to {OUTPUT_EXCEL}")
