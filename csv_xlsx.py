# csv_xlsx.py
# converts csv files to excel files

import pandas as pd
import glob
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folder containing CSV files
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Find all .csv files in the folder
csv_files = glob.glob(os.path.join(input_folder, '*.csv'))

if not csv_files:
    # If only .xlsx files are present, notify they're already Excel
    xlsx_present = glob.glob(os.path.join(input_folder, '*.xlsx'))
    if xlsx_present:
        print("That file is already in Excel format")
    else:
        print("No CSV files found in input folder")
else:
    print(f"Found {len(csv_files)} CSV file(s)")
    
    for file in csv_files:
        try:
            # Get just the filename
            filename = os.path.basename(file)
            
            # Create output Excel filename
            xlsx_filename = os.path.splitext(filename)[0] + '.xlsx'
            xlsx_path = os.path.join(output_folder, xlsx_filename)
            
            # Read CSV file and convert to Excel
            df = pd.read_csv(file)
            df.to_excel(xlsx_path, index=False)
            print(f"Converted {filename} to {xlsx_filename}")
            
        except Exception as e:
            print(f"Error converting {filename}: {e}")
