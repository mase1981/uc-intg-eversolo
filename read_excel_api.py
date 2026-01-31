#!/usr/bin/env python3
"""Read and parse Eversolo API Excel file."""

import pandas as pd
from pathlib import Path

excel_path = Path(r"C:\Downloads\Eversolo API.xlsx")

# Read all sheets
xl_file = pd.ExcelFile(excel_path)
print(f"Excel file has {len(xl_file.sheet_names)} sheets:")
for i, sheet_name in enumerate(xl_file.sheet_names, 1):
    print(f"  {i}. {sheet_name}")

print("\n" + "="*80)

# Read and display each sheet
for sheet_name in xl_file.sheet_names:
    print(f"\n### SHEET: {sheet_name}")
    print("="*80)
    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    # Display shape
    print(f"Dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")
    print()

    # Display all data
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    print(df.to_string(index=False))
    print("\n" + "="*80)
