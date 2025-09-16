# pdf_md.py
# converts pdf files to markdown

import os
import glob
from pypdf import PdfReader
import markdownify

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folder containing PDF files
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Find all .pdf files in the folder
pdf_files = glob.glob(os.path.join(input_folder, '*.pdf'))

if not pdf_files:
    print("No PDF files found in input folder")
else:
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    for file in pdf_files:
        try:
            # Get just the filename
            filename = os.path.basename(file)
            
            # Create output markdown filename
            md_filename = os.path.splitext(filename)[0] + '.md'
            md_path = os.path.join(output_folder, md_filename)
            
            # Read PDF file
            reader = PdfReader(file)
            text = ""
            
            # Extract text from all pages
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            # Convert to markdown (basic conversion)
            markdown_text = markdownify.markdownify(text, heading_style="ATX")
            
            # Save as markdown file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            
            print(f"Converted {filename} to {md_filename}")
            
        except Exception as e:
            print(f"Error converting {filename}: {e}")
            