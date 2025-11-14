# ss_txt2.py
# This script converts images with tables, shapes, and structured content to text
# advanced version of ss_txt.py
# used to identify more than just plain text from screenshots
# attempts to identify tables, shapes, and other structured content

"""
Screenshot to Structured Text Converter
Optimized for extracting tables, shapes, and structured content from images
"""

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import os
import sys
import re
from pathlib import Path

def detect_table_structure(image):
    """
    Detect table structure and extract cell regions
    Args:
        image: PIL Image object
    
    Returns:
        tuple: (processed_image, table_cells) where table_cells is list of (x, y, w, h) regions
    """
    # Convert to numpy array for OpenCV processing
    img_array = np.array(image)
    
    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Scale up image for better detection (if small)
    original_height, original_width = gray.shape
    scale = 1.0
    if original_width < 1000:
        scale = 2.0
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    height, width = gray.shape
    
    # Apply multiple preprocessing techniques
    # Method 1: Adaptive threshold
    binary1 = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Method 2: Otsu threshold
    _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Use the better binary image
    binary = cv2.bitwise_or(binary1, binary2)
    
    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(int(width*0.1), 20), 1))
    detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    horizontal_lines = cv2.dilate(detected_lines, horizontal_kernel, iterations=2)
    
    # Detect vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(int(height*0.1), 20)))
    detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    vertical_lines = cv2.dilate(detected_lines, vertical_kernel, iterations=2)
    
    # Combine to get table structure
    table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
    
    # Find contours to detect cells
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter and extract cell regions
    table_cells = []
    min_area = (width * height) * 0.001  # Minimum cell area
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter out very small or very large regions
            if w > 20 and h > 20 and w < width * 0.9 and h < height * 0.9:
                table_cells.append((x, y, w, h))
    
    # Sort cells by position (top to bottom, left to right)
    table_cells.sort(key=lambda cell: (cell[1] // 50, cell[0]))  # Group by approximate row
    
    # Enhance original image for OCR
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Sharpen
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # Scale back down if we scaled up
    if scale > 1.0:
        sharpened = cv2.resize(sharpened, (original_width, original_height), interpolation=cv2.INTER_AREA)
        # Scale cell coordinates back
        table_cells = [(int(x/scale), int(y/scale), int(w/scale), int(h/scale)) 
                      for x, y, w, h in table_cells]
    
    enhanced_pil = Image.fromarray(sharpened)
    
    return enhanced_pil, table_cells

def preprocess_for_tables(image):
    """
    Preprocess image specifically for table and structure detection
    Args:
        image: PIL Image object
    
    Returns:
        PIL Image: Preprocessed image optimized for tables
    """
    processed, _ = detect_table_structure(image)
    return processed

def detect_shapes_and_contours(image):
    """
    Detect shapes and contours in the image
    Args:
        image: PIL Image object
    
    Returns:
        list: Detected shape information
    """
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply threshold
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    shapes = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # Filter small noise
            # Approximate the contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Classify shape
            if len(approx) == 3:
                shape_type = "Triangle"
            elif len(approx) == 4:
                shape_type = "Rectangle"
            elif len(approx) > 4:
                shape_type = "Circle/Ellipse"
            else:
                shape_type = "Unknown"
            
            shapes.append({
                'type': shape_type,
                'area': area,
                'vertices': len(approx)
            })
    
    return shapes

def are_texts_similar(text1, text2, threshold=0.7):
    """
    Check if two texts are similar (to detect duplicates)
    Args:
        text1 (str): First text
        text2 (str): Second text
        threshold (float): Similarity threshold (0-1)
    
    Returns:
        bool: True if texts are similar
    """
    if not text1 or not text2:
        return False
    
    # Normalize texts for comparison
    def normalize(t):
        # Remove extra whitespace and convert to lowercase
        return re.sub(r'\s+', ' ', t.lower().strip())
    
    norm1 = normalize(text1)
    norm2 = normalize(text2)
    
    # If one is much shorter, check if it's contained in the longer one
    if len(norm1) < len(norm2):
        shorter, longer = norm1, norm2
    else:
        shorter, longer = norm2, norm1
    
    # If shorter text is mostly contained in longer, they're similar
    if len(shorter) > 0:
        similarity = len(shorter) / len(longer) if len(longer) > 0 else 0
        if similarity >= threshold:
            return True
    
    # Check word overlap
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    if len(words1) == 0 or len(words2) == 0:
        return False
    
    overlap = len(words1 & words2)
    total_unique = len(words1 | words2)
    similarity = overlap / total_unique if total_unique > 0 else 0
    
    return similarity >= threshold

def fix_common_ocr_errors(text):
    """
    Fix common OCR misreadings
    Args:
        text (str): Text with potential OCR errors
    
    Returns:
        str: Corrected text
    """
    if not text:
        return text
    
    # Remove empty circles/MCQ bubbles (© symbol)
    # Handle patterns like "©2", "©)", "© " etc.
    text = re.sub(r'©\s*(\d+)', r'\1', text)  # "©2" -> "2"
    text = re.sub(r'©\s*\)', ')', text)  # "©)" -> ")"
    text = re.sub(r'©\s*', '', text)  # Remove © with spaces
    text = re.sub(r'©', '', text)  # Remove any remaining ©
    
    # Fix single letter misreadings with leading "I" or "l"
    # "Ic" -> "c", "Ia" -> "a", "Ib" -> "b"
    text = re.sub(r'\bIc\b', 'c', text)  # "Ic" -> "c"
    text = re.sub(r'\bIa\b', 'a', text)  # "Ia" -> "a"
    text = re.sub(r'\bIb\b', 'b', text)  # "Ib" -> "b"
    
    # Fix single letter misreadings with leading "l"
    text = re.sub(r'\bla\b', 'a', text)  # "la" -> "a"
    text = re.sub(r'\blc\b', 'c', text)  # "lc" -> "c"
    text = re.sub(r'\blb\b', 'b', text)  # "lb" -> "b"
    
    # Fix at start of line or after space
    text = re.sub(r'^Ia\s', 'a ', text)
    text = re.sub(r'^Ic\s', 'c ', text)
    text = re.sub(r'^Ib\s', 'b ', text)
    text = re.sub(r'^la\s', 'a ', text)
    text = re.sub(r'^lc\s', 'c ', text)
    text = re.sub(r'^lb\s', 'b ', text)
    text = re.sub(r'\sIa\s', ' a ', text)
    text = re.sub(r'\sIc\s', ' c ', text)
    text = re.sub(r'\sIb\s', ' b ', text)
    text = re.sub(r'\sla\s', ' a ', text)
    text = re.sub(r'\slc\s', ' c ', text)
    text = re.sub(r'\slb\s', ' b ', text)
    
    # Fix table header patterns
    text = re.sub(r'\bIa\s+b\s+Ic\b', 'a b c', text)
    text = re.sub(r'\bla\s+b\s+lc\b', 'a b c', text)
    text = re.sub(r'^Ia\s+b\s+Ic\s*$', 'a b c', text, flags=re.MULTILINE)
    text = re.sub(r'^la\s+b\s+lc\s*$', 'a b c', text, flags=re.MULTILINE)
    
    # Fix "Oo" (empty circle) -> remove or replace
    text = re.sub(r'\bOo\b', '', text)
    text = re.sub(r'^Oo\s*$', '', text, flags=re.MULTILINE)
    
    # Fix "Os6" -> "6" (empty circle + number)
    text = re.sub(r'\bOs(\d+)\b', r'\1', text)
    
    # Fix number misreadings
    corrections = {
        r'\bl0\b': '0',  # "l0" -> "0"
        r'\bl1\b': '1',  # "l1" -> "1"
        r'\bl2\b': '2',  # "l2" -> "2"
        r'\bl3\b': '3',  # "l3" -> "3"
        r'\bl4\b': '4',  # "l4" -> "4"
        r'\bl5\b': '5',  # "l5" -> "5"
        r'\bl6\b': '6',  # "l6" -> "6"
        r'\bl7\b': '7',  # "l7" -> "7"
        r'\bl8\b': '8',  # "l8" -> "8"
        r'\bl9\b': '9',  # "l9" -> "9"
        r'\bO0\b': '0',  # "O0" -> "0"
        r'\bO1\b': '1',  # "O1" -> "1"
        r'\bO2\b': '2',  # "O2" -> "2"
        r'\bO3\b': '3',  # "O3" -> "3"
        r'\bO4\b': '4',  # "O4" -> "4"
        r'\bO5\b': '5',  # "O5" -> "5"
        r'\bO6\b': '6',  # "O6" -> "6"
        r'\bO7\b': '7',  # "O7" -> "7"
        r'\bO8\b': '8',  # "O8" -> "8"
        r'\bO9\b': '9',  # "O9" -> "9"
        r'\bI0\b': '10', # "I0" -> "10"
        r'\bI1\b': '11', # "I1" -> "11"
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text)
    
    # Clean up: remove lines that are only whitespace or single characters that are artifacts
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Keep the line if it has meaningful content (more than 1 char, or is a single digit/letter that's valid)
        if len(stripped) > 1 or (len(stripped) == 1 and stripped.isalnum()):
            cleaned_lines.append(line)
        # Also keep empty lines that separate sections (but not multiple in a row)
        elif not stripped and cleaned_lines and cleaned_lines[-1].strip():
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    return text.strip()

def preprocess_cell_image(cell_img):
    """
    Preprocess individual cell image for better OCR
    Args:
        cell_img: numpy array of cell image
    
    Returns:
        PIL Image: Preprocessed cell image
    """
    # Scale up if too small
    height, width = cell_img.shape[:2]
    if width < 50 or height < 20:
        scale = max(50 / width, 20 / height, 2.0)
        cell_img = cv2.resize(cell_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(cell_img, None, 10, 7, 21)
    
    # Enhance contrast with CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Sharpen
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # Convert to PIL
    return Image.fromarray(sharpened)

def extract_table_cells(image, table_cells):
    """
    Extract text from individual table cells
    Args:
        image: PIL Image object
        table_cells: List of (x, y, w, h) tuples representing cell regions
    
    Returns:
        str: Formatted table text
    """
    if not table_cells:
        return ""
    
    img_array = np.array(image)
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    cell_texts = []
    current_row = -1
    row_cells = []
    
    for x, y, w, h in table_cells:
        # Extract cell region with padding
        padding = 5
        y1 = max(0, y - padding)
        x1 = max(0, x - padding)
        y2 = min(gray.shape[0], y + h + padding)
        x2 = min(gray.shape[1], x + w + padding)
        
        cell_img = gray[y1:y2, x1:x2]
        
        # Skip if cell is too small
        if cell_img.size < 100:
            continue
        
        # Preprocess cell image for better OCR
        cell_pil = preprocess_cell_image(cell_img)
        
        # Try multiple PSM modes for cells and pick the best result
        cell_texts_tried = []
        for psm in [7, 8, 6, 11]:  # 7=line, 8=word, 6=block, 11=sparse
            try:
                config = f'--oem 3 --psm {psm}'
                text = pytesseract.image_to_string(cell_pil, config=config, lang='eng')
                text = text.strip()
                if text:
                    # Fix common OCR errors
                    text = fix_common_ocr_errors(text)
                    cell_texts_tried.append(text)
            except:
                continue
        
        # Use the longest result (most complete)
        if cell_texts_tried:
            text = max(cell_texts_tried, key=len).strip()
            # Apply error correction one more time
            text = fix_common_ocr_errors(text)
        else:
            text = ""
        
        if text:
            # Determine row (group cells by y position)
            row = y // 30  # Approximate row grouping
            
            if row != current_row and row_cells:
                # New row, format previous row
                cell_texts.append(' | '.join(row_cells))
                row_cells = []
                current_row = row
            
            if current_row == -1:
                current_row = row
            
            row_cells.append(text)
    
    # Add last row
    if row_cells:
        cell_texts.append(' | '.join(row_cells))
    
    return '\n'.join(cell_texts)

def extract_with_multiple_psm_modes(image):
    """
    Extract text using multiple PSM modes optimized for tables and structured content
    Args:
        image: PIL Image object
    
    Returns:
        str: Best unique extracted text
    """
    results = []
    
    # PSM modes optimized for different structures:
    # PSM 6: Uniform block of text (good for tables)
    # PSM 11: Sparse text (good for scattered content)
    # PSM 4: Single column (good for structured lists)
    # PSM 3: Fully automatic (fallback)
    
    psm_modes = [
        (6, "Uniform block"),   # Best for tables
        (11, "Sparse text"),     # Good for scattered content
        (4, "Single column"),    # Good for structured lists
        (3, "Automatic")         # Fallback
    ]
    
    for psm, description in psm_modes:
        try:
            config = f'--oem 3 --psm {psm}'
            text = pytesseract.image_to_string(image, config=config, lang='eng')
            text = text.strip()
            
            if text and len(text) > 10:  # Only keep substantial results
                # Fix common OCR errors
                text = fix_common_ocr_errors(text)
                results.append({
                    'text': text,
                    'psm': psm,
                    'description': description,
                    'length': len(text)
                })
        except Exception as e:
            continue
    
    if not results:
        return ""
    
    # Deduplicate: keep only unique results
    unique_results = []
    for result in results:
        is_duplicate = False
        for existing in unique_results:
            if are_texts_similar(result['text'], existing['text']):
                # If current result is longer/more complete, replace the existing one
                if result['length'] > existing['length']:
                    unique_results.remove(existing)
                    unique_results.append(result)
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_results.append(result)
    
    # Sort by length (prefer longer/more complete results) and return the best one
    if unique_results:
        best_result = max(unique_results, key=lambda x: x['length'])
        return best_result['text']
    
    return ""

def clean_structured_text(text):
    """
    Clean and format extracted structured text
    Args:
        text (str): Raw extracted text
    
    Returns:
        str: Cleaned and formatted text
    """
    if not text:
        return ""
    
    # Fix common OCR errors first
    text = fix_common_ocr_errors(text)
    
    # Remove excessive blank lines (more than 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Try to detect and format table-like structures
    # Look for patterns that might be table rows
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        # If line has multiple spaces/tabs, might be table row
        if re.search(r'\s{3,}', line) or '\t' in line:
            # Try to align columns
            parts = re.split(r'\s{2,}|\t+', line)
            formatted_line = ' | '.join(part.strip() for part in parts if part.strip())
            if formatted_line:
                formatted_lines.append(formatted_line)
        else:
            formatted_lines.append(line)
    
    text = '\n'.join(formatted_lines)
    
    return text.strip()

def convert_image_to_structured_text(image_path):
    """
    Convert an image file to structured text (tables, shapes, etc.)
    Args:
        image_path (str): Path to the input image file
    
    Returns:
        str: Extracted structured text
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Detect table structure and get processed image
        processed_image, table_cells = detect_table_structure(image)
        
        # Try extracting from table cells first if cells are detected
        table_text = ""
        if table_cells and len(table_cells) > 2:  # Need at least a few cells
            table_text = extract_table_cells(image, table_cells)
        
        # Also extract with regular OCR methods
        regular_text = extract_with_multiple_psm_modes(processed_image)
        
        # Combine results - prefer table extraction if it found substantial content
        if table_text and len(table_text.strip()) > 20:
            # Use table extraction as primary, supplement with regular if needed
            text = table_text
            # Add non-table content from regular extraction if it's different
            if regular_text and not are_texts_similar(table_text, regular_text, threshold=0.5):
                # Extract parts that might not be in table
                text = regular_text + "\n\n--- Table Content ---\n" + table_text
        else:
            # Use regular extraction, but try to format any table-like content
            text = regular_text
        
        # Clean the extracted text
        text = clean_structured_text(text)
        
        return text
        
    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to process all images in input folder"""
    # Resolve folders relative to this script for consistency
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(script_dir, "input")
    output_folder = os.path.join(script_dir, "output")
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: '{input_folder}' folder not found")
        sys.exit(1)
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Get all image files from input folder
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    image_files = []
    
    for file in os.listdir(input_folder):
        if Path(file).suffix.lower() in image_extensions:
            image_files.append(file)
    
    if not image_files:
        # If only .txt files are present, they are already text outputs
        txt_present = [f for f in os.listdir(input_folder) if f.lower().endswith('.txt')]
        if txt_present:
            print("That file is already in txt format")
        else:
            print(f"No image files found in '{input_folder}' folder")
            print("Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP")
        sys.exit(1)
    
    print(f"Found {len(image_files)} image(s) to process:")
    for img in image_files:
        print(f"  - {img}")
    
    print("\nProcessing for tables and structured content...")
    
    # Create single output file
    combined_filename = "all_extracted_structured_text.txt"
    combined_path = os.path.join(output_folder, combined_filename)
    
    # Collect all extracted text
    all_text_parts = []
    
    # Process each image
    for image_filename in image_files:
        image_path = os.path.join(input_folder, image_filename)
        
        print(f"\nConverting: {image_filename}")
        
        # Convert image to structured text
        text = convert_image_to_structured_text(image_path)
        
        if text:
            all_text_parts.append(text)
            print(f"Success")
        else:
            print(f"Failed: {image_filename}")
    
    # Write all text to single file
    if all_text_parts:
        with open(combined_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(all_text_parts))
        print(f"\nAll structured text saved to: {combined_filename}")
    else:
        print("\nNo text extracted from any images")

if __name__ == "__main__":
    main()

