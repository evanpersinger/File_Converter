# xlsx_csv.py
# converts excel files to csv

import pandas as pd
import glob
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folder containing Excel files
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Find all .xlsx files in the folder
excel_files = glob.glob(os.path.join(input_folder, '*.xlsx'))

if not excel_files:
    print("No Excel files found in input folder")
else:
    print("Found {len(excel_files)} Excel file(s)")
    
    for file in excel_files:
        try:
            # Get just the filename
            filename = os.path.basename(file)
            
            # Create output CSV filename
            csv_filename = os.path.splitext(filename)[0] + '.csv'
            csv_path = os.path.join(output_folder, csv_filename)
            
            # Read excel file and convert to CSV
            df = pd.read_excel(file)
            df.to_csv(csv_path, index=False)
            print(f"Converted {filename} to {csv_filename}")
            
        except Exception as e:
            print(f"Error converting {filename}: {e}")