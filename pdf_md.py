# pdf_md.py
# converts pdf files to markdown

import os
import glob
import pypdf
import pdfplumber
import pytesseract
from pdfminer.high_level import extract_text
from PIL import Image

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folder containing PDF files
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Find all .pdf files in the folder
pdf_files = glob.glob(os.path.join(input_folder, '*.pdf'))

print(f"Looking for PDF files in: {input_folder}")
print(f"Found files: {pdf_files}")

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
            
            # Try multiple methods to extract text
            text = ""
            
            # Method 1: Try pdfplumber (best for complex PDFs)
            try:
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                print(f"Extracted {len(text)} characters using pdfplumber")
                if text:
                    print(f"First 100 characters: {repr(text[:100])}")
            except Exception as e:
                print(f"pdfplumber failed: {e}")
            
            # If no text extracted, try OCR
            if not text.strip():
                print("No text found, trying OCR...")
                try:
                    with pdfplumber.open(file) as pdf:
                        for page_num, page in enumerate(pdf.pages):
                            # Convert page to image with higher resolution
                            page_image = page.to_image(resolution=600)
                            
                            # OCR with better settings for accuracy
                            custom_config = r'--oem 3 --psm 6'
                            
                            # Extract text using OCR with custom config
                            page_text = pytesseract.image_to_string(
                                page_image.original, 
                                config=custom_config,
                                lang='eng'
                            )
                            
                            if page_text.strip():
                                text += page_text + "\n\n"
                    
                    # Clean up extra whitespace only
                    if text:
                        import re
                        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Remove excessive line breaks
                        text = re.sub(r' +', ' ', text)  # Remove multiple spaces
                        
                    print(f"Extracted {len(text)} characters using OCR")
                    if text:
                        print(f"First 100 characters: {repr(text[:100])}")
                except Exception as ocr_error:
                    print(f"OCR failed: {ocr_error}")
                    
                    # Method 2: Try pdfminer
                    try:
                        text = extract_text(file)
                        print(f"Extracted {len(text)} characters using pdfminer")
                        if text:
                            print(f"First 100 characters: {repr(text[:100])}")
                    except Exception as e2:
                        print(f"pdfminer failed: {e2}")
                        
                        # Method 3: Fallback to pypdf
                        try:
                            with open(file, 'rb') as pdf_file:
                                reader = pypdf.PdfReader(pdf_file)
                                for page in reader.pages:
                                    text += page.extract_text() + "\n\n"
                            print(f"Extracted {len(text)} characters using pypdf")
                            if text:
                                print(f"First 100 characters: {repr(text[:100])}")
                        except Exception as e3:
                            print(f"pypdf also failed: {e3}")
                            text = f"Error: Could not extract text from {filename}"
            
            # Save as markdown file (plain text with markdown extension)
            try:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Converted {filename} to {md_filename}")
                print(f"Saved to: {md_path}")
            except Exception as write_error:
                print(f"Error writing file {md_filename}: {write_error}")
            
        except Exception as e:
            print(f"Error converting {filename}: {e}")
            