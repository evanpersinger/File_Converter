"""Convert CSV files to Excel workbooks.

For each .csv in input/, reads it with pandas and writes an .xlsx to output/.
"""

import pandas as pd
import glob
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folder containing CSV files
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')


def convert_csv_to_xlsx() -> str:
    """Convert all CSV files in the input folder to XLSX files in the output folder.

    Returns:
        A summary of what was converted, suitable for showing to a caller.
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Find all .csv files in the folder
    csv_files = glob.glob(os.path.join(input_folder, '*.csv'))

    if not csv_files:
        # If only .xlsx files are present, notify they're already Excel
        xlsx_present = glob.glob(os.path.join(input_folder, '*.xlsx'))
        if xlsx_present:
            return "That file is already in Excel format"
        return "No CSV files found in input folder"

    print(f"Found {len(csv_files)} CSV file(s)")

    converted = []
    errors = []

    for file in csv_files:
        # Get just the filename (outside the try so it's always available for errors)
        filename = os.path.basename(file)

        try:
            # Create output Excel filename
            xlsx_filename = os.path.splitext(filename)[0] + '.xlsx'
            xlsx_path = os.path.join(output_folder, xlsx_filename)

            # Read CSV file and convert to Excel
            df = pd.read_csv(file)
            df.to_excel(xlsx_path, index=False)
            print(f"Converted {filename} to {xlsx_filename}")
            converted.append(xlsx_filename)

        except Exception as e:
            print(f"Error converting {filename}: {e}")
            errors.append(f"{filename}: {e}")

    if not converted:
        return f"No files converted. {len(errors)} failed: {'; '.join(errors)}"

    summary = f"Converted {len(converted)} file(s) to output/: {', '.join(converted)}"
    if errors:
        summary += f". {len(errors)} failed: {'; '.join(errors)}"
    return summary


if __name__ == "__main__":
    print(convert_csv_to_xlsx())
