# pdf_md.py
# converts pdf files to markdown
# supports both searchable PDFs and scanned image-based PDFs with OCR

import os
import glob
import pypdf
import pdfplumber
import pytesseract
import shutil
from pdfminer.high_level import extract_text
from PIL import Image

# Dynamically find tesseract executable
tesseract_path = shutil.which('tesseract')
if tesseract_path:
    pytesseract.pytesseract.pytesseract_cmd = tesseract_path

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folder containing PDF files
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)


def clean_math_text(text):
    """
    Clean up math notation in extracted text.
    Handles subscripts, superscripts, square roots, and common OCR math mistakes.
    Runs on all extracted text regardless of whether it came from OCR or pdfplumber.
    """
    import re

    subscript_map = {
        'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ',
        'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ', 'p': 'ₚ', 'r': 'ᵣ',
        's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ', 'v': 'ᵥ', 'x': 'ₓ', 'y': 'ᵧ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    }
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    }

    # Join √ that is on its own line with the following expression
    text = re.sub(r'√\s*\n\s*', '√', text)

    # Handle explicit underscore subscript notation: F_x, x_1, x_i, etc.
    def replace_subscript(m):
        base, sub = m.group(1), m.group(2)
        return base + subscript_map.get(sub, '_' + sub)

    text = re.sub(r'([a-zA-Z])_([a-zA-Z0-9])', replace_subscript, text)

    # Handle explicit caret superscript notation: x^2, x^n, etc.
    def replace_superscript(m):
        base, exp = m.group(1), m.group(2)
        return base + superscript_map.get(exp, '^' + exp)

    text = re.sub(r'([a-zA-Z])\^([0-9])', replace_superscript, text)

    # Handle digit directly after a variable at end of expression: x2, n2, etc.
    # Only convert when the digit is followed by a non-digit (space, operator, end of line)
    for digit, superscript in superscript_map.items():
        text = re.sub(rf'([a-zA-Z]){digit}(?=[^0-9a-zA-Z]|$)', rf'\1{superscript}', text)

    # Fix sqrt notation
    text = re.sub(r'\bsqrt\s*\(', '√(', text)
    text = re.sub(r'\bsqrt\s+', '√', text)

    # Fix em/en dashes used as minus signs
    text = re.sub(r'—', '-', text)
    text = re.sub(r'–', '-', text)

    # Clean up excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)

    return text


def is_pdf_scanned(pdf_path, sample_pages=3):
    """
    Detect if a PDF is scanned (image-based) or searchable.
    Returns True if PDF is likely scanned, False if searchable.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_check = min(sample_pages, total_pages)
            
            for i in range(pages_to_check):
                page = pdf.pages[i]
                
                # Try to extract text
                text = page.extract_text()
                
                # If we found substantial text, it's likely searchable
                if text and len(text.strip()) > 100:
                    return False
                
                # Check if page has images (scanned PDFs usually have images)
                if page.images:
                    return True
        
        # If no text found and no images, assume scanned
        return True
    except Exception as e:
        print(f"Could not determine if PDF is scanned: {e}")
        return True  # Default to assuming it's scanned for OCR fallback

# Find all .pdf files in the folder
pdf_files = glob.glob(os.path.join(input_folder, '*.pdf'))

print(f"Looking for PDF files in: {input_folder}")
print(f"Found files: {pdf_files}")

if not pdf_files:
    # If only Markdown files are present, notify they're already in MD format
    md_present = glob.glob(os.path.join(input_folder, '*.md'))
    if md_present:
        print("That file is already in md format")
    else:
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
            
            # Detect if PDF is scanned before attempting extraction
            is_scanned = is_pdf_scanned(file)
            if is_scanned:
                print(f"Detected scanned PDF: {filename}")
            else:
                print(f"Detected searchable PDF: {filename}")
            
            # Method 1: Try pdfplumber (best for complex PDFs)
            if not is_scanned:
                try:
                    with pdfplumber.open(file) as pdf:
                        for page_num, page in enumerate(pdf.pages):
                            # Check if page has images and skip them
                            if page.images:
                                print(f"Page {page_num + 1}: Contains {len(page.images)} image(s)")
                            
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n\n"
                    print(f"Extracted {len(text)} characters using pdfplumber")
                    if text:
                        print(f"First 100 characters: {repr(text[:100])}")
                except Exception as e:
                    print(f"pdfplumber failed: {e}")
            
            # If no text extracted or PDF is scanned, try OCR
            if not text.strip() or is_scanned:
                if not text.strip():
                    print("No text found in searchable format, attempting OCR...")
                else:
                    print("Attempting OCR for scanned PDF...")
                try:
                    with pdfplumber.open(file) as pdf:
                        for page_num, page in enumerate(pdf.pages):
                            # Check if page has images and notify
                            if page.images:
                                print(f"Page {page_num + 1}: Contains {len(page.images)} image(s), using OCR")
                            
                            # Convert page to image with higher resolution for scanned PDFs
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
            
            # Apply math cleanup to all extracted text regardless of source
            if text.strip():
                text = clean_math_text(text)

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
            