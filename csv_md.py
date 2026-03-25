# csv_md.py
# converts csv files to markdown

import csv
import glob
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folders
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')


# convert a csv file to a markdown table
# handles conversion logic
def csv_to_markdown(csv_file):
    """Read a CSV file and return a markdown table string"""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows: # if csv file is empty, return an empty string
        return ""

    headers = rows[0] # assign first row as headers
    separator = ['---'] * len(headers) # builds separator row
    data_rows = rows[1:] # assign remaining rows as data rows instead of headers

    # builds markdown table
    lines = []
    lines.append('| ' + ' | '.join(headers) + ' |')
    lines.append('| ' + ' | '.join(separator) + ' |')
    for row in data_rows:
        lines.append('| ' + ' | '.join(row) + ' |')

    return '\n'.join(lines) + '\n' # joins all lines together


# convert all csv files to markdown files
# handles file system operations
def convert_csv_to_markdown():
    """Convert all CSV files in input folder to Markdown files in output folder"""

    os.makedirs(output_folder, exist_ok=True)

    csv_files = glob.glob(os.path.join(input_folder, '*.csv'))

    if not csv_files:
        md_present = glob.glob(os.path.join(input_folder, '*.md'))
        if md_present:
            print("File is already in markdown format")
        else:
            print("No CSV files found in input folder")
        return

    print(f"Found {len(csv_files)} CSV file(s) to convert")

    # loop through all csv files
    for csv_file in csv_files:
        try:
            filename = os.path.splitext(os.path.basename(csv_file))[0] # builds new filename
            md_file = os.path.join(output_folder, f"{filename}.md")

            markdown_content = csv_to_markdown(csv_file)

            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"Converted: {os.path.basename(csv_file)} -> {filename}.md")

        except Exception as e:
            print(f"Error converting {os.path.basename(csv_file)}: {str(e)}")


if __name__ == "__main__":
    convert_csv_to_markdown()
