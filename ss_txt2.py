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
    Uses multiple methods: line detection and text region detection
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
    
    # METHOD 1: Detect table with lines (for tables with borders)
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
    
    # Filter and extract cell regions from line detection
    table_cells = []
    min_area = (width * height) * 0.001  # Minimum cell area
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter out very small or very large regions
            if w > 20 and h > 20 and w < width * 0.9 and h < height * 0.9:
                table_cells.append((x, y, w, h))
    
    # METHOD 2: Detect text regions using connected components (for tables without borders)
    # This helps detect tables that are just aligned text
    # Only use this if line detection found very few cells (likely no borders)
    if len(table_cells) < 2:  # If line detection didn't find much, try text region detection
        # Use morphological operations to find text blocks
        # Create a kernel to connect nearby text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # Find connected components (text regions)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
        
        text_regions = []
        for i in range(1, num_labels):  # Skip background (label 0)
            x, y, w, h, area = stats[i]
            # Filter for reasonable text region sizes (table cells are usually small and compact)
            # Exclude very wide regions (likely full sentences)
            if (w > 15 and h > 10 and w < width * 0.3 and h < height * 0.2 and 
                area > 50 and area < width * height * 0.1):
                text_regions.append((x, y, w, h))
        
        # Validate that these regions actually form a table structure
        if len(text_regions) >= 4:  # Need at least 4 cells for a reasonable table
            # Group by y-position to find rows
            sorted_regions = sorted(text_regions, key=lambda r: r[1])
            avg_height = sum(h for _, _, _, h in text_regions) / len(text_regions)
            row_tolerance = max(avg_height * 0.6, 20)
            
            # Group into rows
            rows = []
            current_row = []
            last_y = sorted_regions[0][1]
            
            for region in sorted_regions:
                _, y, _, _ = region
                if abs(y - last_y) <= row_tolerance:
                    current_row.append(region)
                else:
                    if current_row:
                        rows.append(current_row)
                    current_row = [region]
                    last_y = y
            if current_row:
                rows.append(current_row)
            
            # Validate table structure:
            # 1. Must have at least 2 rows
            # 2. Most rows should have similar number of columns (within 1-2)
            # 3. Cells should be roughly aligned in columns
            if len(rows) >= 2:
                # Count columns per row
                cols_per_row = [len(row) for row in rows]
                avg_cols = sum(cols_per_row) / len(cols_per_row)
                
                # Check if most rows have similar column counts (table-like)
                similar_cols = sum(1 for c in cols_per_row if abs(c - avg_cols) <= 1)
                if similar_cols >= len(rows) * 0.7:  # At least 70% of rows have similar column count
                    # Check column alignment - cells in same column should have similar x positions
                    # Sort each row by x
                    for row in rows:
                        row.sort(key=lambda r: r[0])
                    
                    # Check if columns are roughly aligned
                    num_cols = int(round(avg_cols))
                    if num_cols >= 2:  # At least 2 columns
                        # Calculate column x positions from first few rows
                        first_row_x = [r[0] for r in rows[0]] if len(rows[0]) >= num_cols else []
                        if first_row_x:
                            # Check alignment consistency - be more lenient
                            alignment_ok = True
                            aligned_rows = 1  # Count how many rows are aligned
                            x_tolerance = width * 0.15  # More tolerance (15% of width)
                            
                            for row in rows[1:]:
                                if len(row) >= num_cols:
                                    row_aligned = True
                                    for i in range(min(len(row), len(first_row_x))):
                                        if abs(row[i][0] - first_row_x[i]) > x_tolerance:
                                            row_aligned = False
                                            break
                                    if row_aligned:
                                        aligned_rows += 1
                            
                            # If at least 60% of rows are aligned, consider it a table
                            if aligned_rows >= len(rows) * 0.6:
                                table_cells = text_regions
    
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
    
    # Fix letter+number misreadings where number "1" is read as "i" or "l"
    # "bi" -> "b1", "ai" -> "a1", "ci" -> "c1" when standalone (word boundaries)
    # This fixes table cells like "b1", "a1", "c1" that OCR reads as "bi", "ai", "ci"
    text = re.sub(r'\b([a-z])i\b', r'\g<1>1', text)  # "bi" -> "b1", "ai" -> "a1", etc.
    
    # Fix letter+number misreadings where number "1" is read as "l"
    # "al" -> "a1", "bl" -> "b1", "cl" -> "c1" when standalone (word boundaries)
    # For short patterns (2-3 chars), fix "l" at end if preceded by letter
    text = re.sub(r'\b([a-z])l\b', r'\g<1>1', text)  # "al" -> "a1", "cl" -> "c1", etc.
    
    # Special cases for longer misreadings
    text = re.sub(r'\blon\b', 'c1', text)  # "lon" -> "c1"
    
    # Fix patterns where letter "a" is read as "1" and number "1" is read as "t"
    # "1t" -> "a1" (in table cell context)
    text = re.sub(r'\b1t\b', 'a1', text)  # "1t" -> "a1"
    
    # Fix patterns where number "1" is read as "t" after a letter
    # "at" -> "a1" (when "a1" is misread as "at")
    # Be careful: "at" is a real word, but in 2-char table cells it's likely "a1"
    text = re.sub(r'\bat\b', 'a1', text)  # "at" -> "a1" (standalone, like in table cells)
    
    # Fix similar patterns for other letters
    # "bt" -> "b1", "ct" -> "c1", etc.
    text = re.sub(r'\b([a-z])t\b', r'\g<1>1', text)  # "at" -> "a1", "bt" -> "b1", etc.
    
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

def group_cells_into_rows(table_cells, row_tolerance=None):
    """
    Group table cells into rows based on their y-coordinates
    Args:
        table_cells: List of (x, y, w, h) tuples
        row_tolerance: Maximum y-distance to consider cells in same row (auto if None)
    
    Returns:
        list: List of rows, each row is a list of (x, y, w, h) cell tuples
    """
    if not table_cells:
        return []
    
    # Calculate row tolerance based on average cell height if not provided
    if row_tolerance is None:
        avg_height = sum(h for _, _, _, h in table_cells) / len(table_cells)
        row_tolerance = max(avg_height * 0.5, 15)  # 50% of avg height or 15px, whichever is larger
    
    # Sort cells by y-coordinate first
    sorted_cells = sorted(table_cells, key=lambda cell: (cell[1], cell[0]))
    
    rows = []
    current_row = []
    current_row_y = None
    
    for cell in sorted_cells:
        x, y, w, h = cell
        cell_center_y = y + h // 2  # Use center y for better grouping
        
        if current_row_y is None or abs(cell_center_y - current_row_y) <= row_tolerance:
            # Same row
            current_row.append(cell)
            if current_row_y is None:
                current_row_y = cell_center_y
            else:
                # Update row y to average of all cells in row
                current_row_y = sum(cy + ch // 2 for _, cy, _, ch in current_row) / len(current_row)
        else:
            # New row
            if current_row:
                # Sort cells in row by x-coordinate (left to right)
                current_row.sort(key=lambda c: c[0])
                rows.append(current_row)
            current_row = [cell]
            current_row_y = cell_center_y
    
    # Add last row
    if current_row:
        current_row.sort(key=lambda c: c[0])
        rows.append(current_row)
    
    return rows

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
    
    # Group cells into rows
    rows = group_cells_into_rows(table_cells)
    
    if not rows:
        return ""
    
    cell_texts = []
    
    # Process each row
    for row_cells in rows:
        row_texts = []
        
        for x, y, w, h in row_cells:
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
                if text:
                    row_texts.append(text)
        
        # Format row with pipe separators and borders
        if row_texts:
            cell_texts.append('| ' + ' | '.join(row_texts) + ' |')
    
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

def detect_and_group_table_lines(lines):
    """
    Detect if lines form a table pattern (each cell on separate line) and group them
    Args:
        lines: List of text lines
    
    Returns:
        List of lines with table rows grouped
    """
    if not lines:
        return lines
    
    # First pass: collect all potential table cells with their original line indices
    table_cell_indices = []  # List of line indices that contain table cells
    table_cells = []  # List of cell values
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and len(stripped) <= 8 and ' ' not in stripped:
            table_cell_indices.append(i)
            table_cells.append(stripped)
    
    if len(table_cells) < 4:  # Need at least 4 cells to form a table
        return lines
    
    # Try different column counts (3, 2, 4) and see which fits best
    # Prefer 3 columns as default, but check if others fit better
    best_column_count = 3
    best_fit_score = -1000
    
    for col_count in [3, 2, 4]:
        complete_rows = len(table_cells) // col_count
        remainder = len(table_cells) % col_count
        
        # Prefer exact fits (remainder = 0) and prefer 3 columns
        if remainder == 0:
            # Perfect fit - prefer 3 columns
            fit_score = complete_rows * 100 + (10 if col_count == 3 else 0)
        else:
            # Not perfect fit - penalize remainder
            fit_score = complete_rows * 10 - remainder * 5
        
        if fit_score > best_fit_score:
            best_fit_score = fit_score
            best_column_count = col_count
    
    # Group cells into rows with borders
    table_rows = []
    for i in range(0, len(table_cells), best_column_count):
        row_cells = table_cells[i:i + best_column_count]
        if len(row_cells) >= 2:
            table_rows.append('| ' + ' | '.join(row_cells) + ' |')
    
    # Second pass: find table section and replace with grouped rows
    result = []
    i = 0
    processed_indices = set()
    
    while i < len(lines):
        if i in table_cell_indices and i not in processed_indices:
            # Found start of table section - find the end
            table_start = i
            table_end = i
            
            # Find where table section ends (all consecutive table cells)
            j = i
            while j < len(lines):
                if j in table_cell_indices:
                    table_end = j
                    processed_indices.add(j)
                    j += 1
                elif not lines[j].strip() and j + 1 < len(lines) and (j + 1) in table_cell_indices:
                    # Empty line between table cells - part of table section
                    j += 1
                else:
                    # End of table section
                    break
            
            # Replace entire table section with grouped rows
            for row in table_rows:
                result.append(row)
            
            # Skip all lines in table section
            i = j
        else:
            # Not a table cell or already processed
            if i not in processed_indices:
                result.append(lines[i])
            i += 1
    
    return result

def clean_structured_text(text, is_table=False):
    """
    Clean and format extracted structured text
    Args:
        text (str): Raw extracted text
        is_table (bool): Whether this text came from table detection
    
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
    
    # Only format as table if explicitly from table detection
    # OR if it clearly looks like table data (not regular sentences)
    if is_table:
        # Already formatted as table, just clean up
        pass
    else:
        # Try to detect table patterns where each cell is on a separate line
        lines = text.split('\n')
        lines = detect_and_group_table_lines(lines)
        
        # Also format lines with multiple spaces/tabs as table rows
        formatted_lines = []
        
        for line in lines:
            # Only format as table if:
            # 1. Has multiple spaces/tabs AND
            # 2. Has 2-5 parts (typical table columns) AND
            # 3. Each part is relatively short (not full sentences)
            if re.search(r'\s{3,}', line) or '\t' in line:
                parts = re.split(r'\s{2,}|\t+', line)
                parts = [part.strip() for part in parts if part.strip()]
                
                # Check if this looks like a table row (not a sentence)
                if (2 <= len(parts) <= 6 and 
                    all(len(part) < 50 for part in parts) and  # Each cell is short
                    not any(len(part) > 30 and ' ' in part for part in parts)):  # No long multi-word cells
                    formatted_line = '| ' + ' | '.join(parts) + ' |'
                    formatted_lines.append(formatted_line)
                else:
                    # Regular text with spacing - keep as is
                    formatted_lines.append(line)
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
        if table_cells and len(table_cells) >= 2:  # Need at least 2 cells (could be 2x1 or 1x2 table)
            table_text = extract_table_cells(image, table_cells)
        
        # Also extract with regular OCR methods
        regular_text = extract_with_multiple_psm_modes(processed_image)
        
        # Combine results - prefer table extraction if we detected table cells
        if table_text and len(table_text.strip()) > 0:
            # Use table extraction as primary
            text = table_text
            # Add non-table content from regular extraction if it's substantially different
            # (e.g., question text above the table)
            if regular_text and not are_texts_similar(table_text, regular_text, threshold=0.3):
                # Check if regular text has content not in table (likely question/context)
                regular_lines = [line.strip() for line in regular_text.split('\n') if line.strip()]
                table_lines = [line.strip() for line in table_text.split('\n') if line.strip()]
                # If regular text has lines not similar to table, prepend them
                unique_regular = [line for line in regular_lines 
                                if not any(are_texts_similar(line, t_line, 0.5) for t_line in table_lines)]
                if unique_regular:
                    text = '\n'.join(unique_regular) + "\n\n" + table_text
            # Clean with table formatting enabled (since we detected a table)
            text = clean_structured_text(text, is_table=True)
        else:
            # Use regular extraction - don't format as table
            text = regular_text
            # Clean without table formatting (just basic cleaning)
            text = clean_structured_text(text, is_table=False)
        
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

