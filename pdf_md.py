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
                    
                    # Clean up extra whitespace and fix common statistics symbols
                    if text:
                        import re
                        
                        # Fix common statistics symbol OCR mistakes
                        # Only apply these fixes when they make sense in context
                        text = re.sub(r'\bσ\b', 'sigma', text)  # Greek sigma
                        text = re.sub(r'\bμ\b', 'mu', text)     # Greek mu
                        text = re.sub(r'\bα\b', 'alpha', text) # Greek alpha
                        text = re.sub(r'\bβ\b', 'beta', text)   # Greek beta
                        text = re.sub(r'\bχ\b', 'chi', text)   # Greek chi
                        text = re.sub(r'\bδ\b', 'delta', text) # Greek delta
                        
                        # Fix common OCR mistakes for Greek letters and math symbols
                        text = re.sub(r'\boC\b', 'σ', text)  # oC becomes σ (sigma)
                        text = re.sub(r'\bo\b(?=\s*[=<>])', 'σ', text)  # o before = becomes σ
                        text = re.sub(r'\bu\b(?=\s*[=<>])', 'μ', text)  # u before = becomes μ
                        text = re.sub(r'\bπ\b', 'π', text)  # Ensure pi symbol is correct
                        
                        # Fix common OCR mistakes for mathematical notation
                        text = re.sub(r'—', '-', text)  # Replace em dash with minus sign
                        text = re.sub(r'–', '-', text)  # Replace en dash with minus sign
                        text = re.sub(r'×', '×', text)  # Ensure multiplication symbol
                        text = re.sub(r'÷', '÷', text)  # Ensure division symbol
                        text = re.sub(r'±', '±', text)  # Ensure plus-minus symbol
                        
                        # Fix common probability notation patterns
                        text = re.sub(r'(\d+), = (\d+),(\d+), = (\d+),(\d+), = \.(\d+)', r'π₁ = 0.\2\3, π₂ = 0.\4\5, π₃ = 0.\6', text)  # General probability pattern
                        text = re.sub(r'(\d+), = (\d+),(\d+)', r'π₁ = 0.\2\3', text)  # Single probability pattern
                        
                        # Fix common fraction patterns
                        text = re.sub(r'(\d+)/(\d+)', r'\1/\2', text)  # Ensure proper fraction formatting
                        
                        # Fix common mathematical operators
                        text = re.sub(r'<=', '≤', text)  # Less than or equal
                        text = re.sub(r'>=', '≥', text)  # Greater than or equal
                        text = re.sub(r'!=', '≠', text)  # Not equal
                        
                        # Fix LaTeX-style summation notation that OCR misreads
                        text = re.sub(r'\\sum\s*_\{i=1\}\^n', r'∑ᵢ₌₁ⁿ', text)           # \sum _{i=1}^n
                        text = re.sub(r'\\sum\s*_\{i=0\}\^n', r'∑ᵢ₌₀ⁿ', text)           # \sum _{i=0}^n
                        text = re.sub(r'\\sum\s*_\{i=1\}\^\{n\}', r'∑ᵢ₌₁ⁿ', text)       # \sum _{i=1}^{n}
                        text = re.sub(r'\\sum\s*_\{i=0\}\^\{n\}', r'∑ᵢ₌₀ⁿ', text)       # \sum _{i=0}^{n}
                        
                        # Fix common OCR misreadings of sigma notation
                        text = re.sub(r'sigma\s*\(i=1\s+to\s+n\)', r'∑ᵢ₌₁ⁿ', text)      # sigma (i=1 to n)
                        text = re.sub(r'sigma\s*\(i=0\s+to\s+n\)', r'∑ᵢ₌₀ⁿ', text)      # sigma (i=0 to n)
                        text = re.sub(r'sigma\s+from\s+i=1\s+to\s+n', r'∑ᵢ₌₁ⁿ', text)   # sigma from i=1 to n
                        text = re.sub(r'sigma\s+from\s+i=0\s+to\s+n', r'∑ᵢ₌₀ⁿ', text)   # sigma from i=0 to n
                        
                        # Fix garbled summation symbols (common OCR issue)
                        text = re.sub(r'∑[^∑]*ᵢ[^∑]*₌[^∑]*₁[^∑]*ⁿ', r'∑ᵢ₌₁ⁿ', text)  # Fix garbled summation
                        text = re.sub(r'∑[^∑]*ᵢ[^∑]*₌[^∑]*₀[^∑]*ⁿ', r'∑ᵢ₌₀ⁿ', text)  # Fix garbled summation from 0
                        
                        # Fix common OCR misreadings of LaTeX notation
                        text = re.sub(r'nN\s*Di\s*i=\]', r'∑ᵢ₌₁ⁿ', text)               # nN Di i=] → ∑ᵢ₌₁ⁿ
                        text = re.sub(r'nN\s*Di\s*i=\[', r'∑ᵢ₌₀ⁿ', text)               # nN Di i=[ → ∑ᵢ₌₀ⁿ
                        
                        # Fix more common sigma notation OCR errors
                        text = re.sub(r'sigma\s*_\{i=1\}\^n', r'∑ᵢ₌₁ⁿ', text)          # sigma_{i=1}^n
                        text = re.sub(r'sigma\s*_\{i=0\}\^n', r'∑ᵢ₌₀ⁿ', text)          # sigma_{i=0}^n
                        text = re.sub(r'sigma\s*_i=1\^n', r'∑ᵢ₌₁ⁿ', text)             # sigma_i=1^n
                        text = re.sub(r'sigma\s*_i=0\^n', r'∑ᵢ₌₀ⁿ', text)             # sigma_i=0^n
                        
                        # Fix summation with different variable names
                        text = re.sub(r'sigma\s*_\{j=1\}\^n', r'∑ⱼ₌₁ⁿ', text)          # sigma_{j=1}^n
                        text = re.sub(r'sigma\s*_\{k=1\}\^n', r'∑ₖ₌₁ⁿ', text)          # sigma_{k=1}^n
                        text = re.sub(r'sigma\s*_\{x=1\}\^n', r'∑ₓ₌₁ⁿ', text)          # sigma_{x=1}^n
                        
                        # Fix summation notation (sigma with limits)
                        text = re.sub(r'sigma\s+from\s+i=(\d+)\s+to\s+(\d+)', r'∑ᵢ₌₁ⁿ', text)  # sigma from i=1 to n
                        text = re.sub(r'sigma\s+from\s+i=0\s+to\s+(\d+)', r'∑ᵢ₌₀ⁿ', text)   # sigma from i=0 to n
                        text = re.sub(r'sigma\s+from\s+i=1\s+to\s+n', r'∑ᵢ₌₁ⁿ', text)      # sigma from i=1 to n
                        text = re.sub(r'sigma\s+from\s+i=0\s+to\s+n', r'∑ᵢ₌₀ⁿ', text)     # sigma from i=0 to n
                        
                        # Fix common OCR patterns for summation
                        text = re.sub(r'sigma\s+\(i=1\s+to\s+n\)', r'∑ᵢ₌₁ⁿ', text)        # sigma (i=1 to n)
                        text = re.sub(r'sigma\s+\(i=0\s+to\s+n\)', r'∑ᵢ₌₀ⁿ', text)        # sigma (i=0 to n)
                        
                        # Fix common OCR misreadings of sigma symbol itself
                        text = re.sub(r'\bsigma\b', '∑', text)  # Replace "sigma" with ∑ symbol
                        text = re.sub(r'\bSigma\b', '∑', text)  # Replace "Sigma" with ∑ symbol
                        text = re.sub(r'\bSIGMA\b', '∑', text)  # Replace "SIGMA" with ∑ symbol
                        
                        # Fix OCR misreadings where sigma becomes other characters
                        text = re.sub(r'\bs\b(?=\s*\(i=)', '∑', text)  # s (i= becomes ∑ (i=
                        text = re.sub(r'\bs\b(?=\s*_\{i=)', '∑', text)  # s _{i= becomes ∑ _{i=
                        text = re.sub(r'\bs\b(?=\s*from)', '∑', text)  # s from becomes ∑ from
                        
                        # Fix summation with different limits after sigma replacement
                        text = re.sub(r'∑\s*\(i=1\s+to\s+n\)', r'∑ᵢ₌₁ⁿ', text)      # ∑ (i=1 to n)
                        text = re.sub(r'∑\s*\(i=0\s+to\s+n\)', r'∑ᵢ₌₀ⁿ', text)      # ∑ (i=0 to n)
                        text = re.sub(r'∑\s*from\s+i=1\s+to\s+n', r'∑ᵢ₌₁ⁿ', text)   # ∑ from i=1 to n
                        text = re.sub(r'∑\s*from\s+i=0\s+to\s+n', r'∑ᵢ₌₀ⁿ', text)   # ∑ from i=0 to n
                        
                        # Fix subscripts and superscripts
                        text = re.sub(r'x\^2', 'x²', text)  # x^2 becomes x²
                        text = re.sub(r'x\^3', 'x³', text)  # x^3 becomes x³
                        text = re.sub(r'x_2', 'x₂', text)   # x_2 becomes x₂
                        text = re.sub(r'x_1', 'x₁', text)   # x_1 becomes x₁
                        
                        # Fix squared symbols for common statistics terms (more specific patterns)
                        text = re.sub(r'σ\^2', 'σ²', text)  # σ^2 becomes σ²
                        text = re.sub(r'σ\s+2\b', 'σ²', text)  # σ 2 becomes σ² (with word boundary)
                        text = re.sub(r'sigma\^2', 'σ²', text)  # sigma^2 becomes σ²
                        text = re.sub(r'sigma\s+2\b', 'σ²', text)  # sigma 2 becomes σ² (with word boundary)
                        
                        # Fix "standard deviation squared" specifically
                        text = re.sub(r'standard\s+deviation\s+squared', 'σ²', text)  # standard deviation squared
                        text = re.sub(r'standard\s+deviation\s*\^2', 'σ²', text)  # standard deviation^2
                        text = re.sub(r'standard\s+deviation\s*2', 'σ²', text)  # standard deviation 2
                        text = re.sub(r'std\s+dev\s+squared', 'σ²', text)  # std dev squared
                        text = re.sub(r'std\s+dev\s*\^2', 'σ²', text)  # std dev^2
                        text = re.sub(r'std\s+dev\s*2', 'σ²', text)  # std dev 2
                        
                        # Fix variance (which is standard deviation squared)
                        text = re.sub(r'variance\s*\^2', 'σ²', text)  # variance^2
                        text = re.sub(r'variance\s*2', 'σ²', text)  # variance 2
                        text = re.sub(r'var\s*\^2', 'σ²', text)  # var^2
                        text = re.sub(r'var\s*2', 'σ²', text)  # var 2
                        
                        # Fix population variance
                        text = re.sub(r'population\s+variance', 'σ²', text)  # population variance
                        text = re.sub(r'pop\s+var', 'σ²', text)  # pop var
                        text = re.sub(r'population\s+std\s+dev\s+squared', 'σ²', text)  # population std dev squared
                        text = re.sub(r'μ\^2', 'μ²', text)  # μ^2 becomes μ²
                        text = re.sub(r'μ\s+2\b', 'μ²', text)  # μ 2 becomes μ² (with word boundary)
                        text = re.sub(r'mu\^2', 'μ²', text)  # mu^2 becomes μ²
                        text = re.sub(r'mu\s+2\b', 'μ²', text)  # mu 2 becomes μ² (with word boundary)
                        
                        # Fix common OCR misreadings of squared symbols
                        text = re.sub(r'σ\s*\(2\)', 'σ²', text)  # σ (2) becomes σ²
                        text = re.sub(r'sigma\s*\(2\)', 'σ²', text)  # sigma (2) becomes σ²
                        text = re.sub(r'σ\s*\[2\]', 'σ²', text)  # σ [2] becomes σ²
                        text = re.sub(r'sigma\s*\[2\]', 'σ²', text)  # sigma [2] becomes σ²
                        
                        # Fix squared symbols for other common variables (more specific patterns)
                        text = re.sub(r's\^2', 's²', text)  # s^2 becomes s²
                        text = re.sub(r's\s+2\b', 's²', text)  # s 2 becomes s² (with word boundary)
                        text = re.sub(r'n\^2', 'n²', text)  # n^2 becomes n²
                        text = re.sub(r'n\s+2\b', 'n²', text)  # n 2 becomes n² (with word boundary)
                        text = re.sub(r'X\^2', 'X²', text)  # X^2 becomes X²
                        text = re.sub(r'X\s+2\b', 'X²', text)  # X 2 becomes X² (with word boundary)
                        text = re.sub(r'Y\^2', 'Y²', text)  # Y^2 becomes Y²
                        text = re.sub(r'Y\s+2\b', 'Y²', text)  # Y 2 becomes Y² (with word boundary)
                        
                        # Fix cubed symbols for common statistics terms (more specific patterns)
                        text = re.sub(r'σ\^3', 'σ³', text)  # σ^3 becomes σ³
                        text = re.sub(r'σ\s+3\b', 'σ³', text)  # σ 3 becomes σ³ (with word boundary)
                        text = re.sub(r'sigma\^3', 'σ³', text)  # sigma^3 becomes σ³
                        text = re.sub(r'sigma\s+3\b', 'σ³', text)  # sigma 3 becomes σ³ (with word boundary)
                        text = re.sub(r'μ\^3', 'μ³', text)  # μ^3 becomes μ³
                        text = re.sub(r'μ\s+3\b', 'μ³', text)  # μ 3 becomes μ³ (with word boundary)
                        text = re.sub(r'mu\^3', 'μ³', text)  # mu^3 becomes μ³
                        text = re.sub(r'mu\s+3\b', 'μ³', text)  # mu 3 becomes μ³ (with word boundary)
                        
                        # Fix common OCR misreadings of cubed symbols
                        text = re.sub(r'σ\s*\(3\)', 'σ³', text)  # σ (3) becomes σ³
                        text = re.sub(r'sigma\s*\(3\)', 'σ³', text)  # sigma (3) becomes σ³
                        text = re.sub(r'σ\s*\[3\]', 'σ³', text)  # σ [3] becomes σ³
                        text = re.sub(r'sigma\s*\[3\]', 'σ³', text)  # sigma [3] becomes σ³
                        
                        # Fix cubed symbols for other common variables (more specific patterns)
                        text = re.sub(r's\^3', 's³', text)  # s^3 becomes s³
                        text = re.sub(r's\s+3\b', 's³', text)  # s 3 becomes s³ (with word boundary)
                        text = re.sub(r'n\^3', 'n³', text)  # n^3 becomes n³
                        text = re.sub(r'n\s+3\b', 'n³', text)  # n 3 becomes n³ (with word boundary)
                        text = re.sub(r'X\^3', 'X³', text)  # X^3 becomes X³
                        text = re.sub(r'X\s+3\b', 'X³', text)  # X 3 becomes X³ (with word boundary)
                        text = re.sub(r'Y\^3', 'Y³', text)  # Y^3 becomes Y³
                        text = re.sub(r'Y\s+3\b', 'Y³', text)  # Y 3 becomes Y³ (with word boundary)
                        
                        # Fix common variable subscripts and OCR misreadings
                        text = re.sub(r'w_i', 'wᵢ', text)    # w_i becomes wᵢ
                        text = re.sub(r'x_i', 'xᵢ', text)    # x_i becomes xᵢ
                        text = re.sub(r'y_i', 'yᵢ', text)    # y_i becomes yᵢ
                        text = re.sub(r'z_i', 'zᵢ', text)    # z_i becomes zᵢ
                        
                        
                        # Fix common numbering issues (double periods)
                        text = re.sub(r'(\d+)\.(\d+)\.', r'\1.\2', text)  # Fix double periods in numbering
                        
                        # Fix incorrect superscripts that shouldn't be there (general patterns)
                        text = re.sub(r'(\w+)²(\s)', r'\1 2\2', text)  # Fix word² followed by space
                        text = re.sub(r'(\w+)³(\s)', r'\1 3\2', text)  # Fix word³ followed by space
                        text = re.sub(r'(\w+)²(\d)', r'\1 2\2', text)  # Fix word² followed by digit
                        text = re.sub(r'(\w+)³(\d)', r'\1 3\2', text)  # Fix word³ followed by digit
                        text = re.sub(r'(\w+)²(\.)', r'\1 2\2', text)  # Fix word² followed by period
                        text = re.sub(r'(\w+)³(\.)', r'\1 3\2', text)  # Fix word³ followed by period
                        
                        # Clean up formatting
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
            