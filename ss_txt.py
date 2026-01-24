# ss_tet.py
# This script converts an image to text using OCR
# it's only good at converting text images to text
# avoid using this script for images with tables, shapes, or other structured content

"""
Screenshot to Text Converter
Converts image files to text using OCR
"""

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import sys
import re
from pathlib import Path

def preprocess_image(image):
    """
    Preprocess image to improve OCR accuracy
    Args:
        image: PIL Image object
    
    Returns:
        list: List of preprocessed PIL Images with different processing methods
    """
    preprocessed_images = []
    
    # Enhanced grayscale (original approach)
    gray_img = image.convert('L')
    enhancer = ImageEnhance.Contrast(gray_img)
    gray_img = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Sharpness(gray_img)
    gray_img = enhancer.enhance(1.2)
    gray_img = gray_img.filter(ImageFilter.MedianFilter(size=3))
    preprocessed_images.append(gray_img)
    
    # High contrast grayscale for colored backgrounds
    gray_high = image.convert('L')
    enhancer = ImageEnhance.Contrast(gray_high)
    gray_high = enhancer.enhance(2.5)
    preprocessed_images.append(gray_high)
    
    # Original color image (works better for colored text/backgrounds)
    if image.mode != 'RGB':
        color_img = image.convert('RGB')
    else:
        color_img = image
    preprocessed_images.append(color_img)
    
    return preprocessed_images


def clean_text(text):
    """
    Clean extracted text by removing excessive whitespace and fixing sentence structure
    Args:
        text (str): Raw extracted text
    
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive blank lines (more than 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    
    # Fix sentence structure: join lines that are clearly part of the same sentence
    # Only join when the next line starts with lowercase (continuation of sentence)
    # OR when current line ends with continuation punctuation (comma, dash, etc.)
    
    fixed_lines = []
    i = 0
    while i < len(lines):
        current_line = lines[i]
        
        # If this is an empty line, preserve it (paragraph break)
        if not current_line.strip():
            fixed_lines.append(current_line)
            i += 1
            continue
        
        # Try to join with following lines that are clearly continuations
        while i + 1 < len(lines):
            next_line = lines[i + 1]
            
            # Stop if next line is empty (paragraph break)
            if not next_line.strip():
                break
            
            # Check if next line starts with lowercase (continuation)
            next_stripped = next_line.strip()
            starts_with_lowercase = next_stripped and next_stripped[0].islower()
            
            # Check if current line ends with continuation punctuation
            ends_with_continuation = re.search(r'[,;:—–-]\s*$', current_line)
            
            # Only join if:
            # 1. Next line starts with lowercase (clear continuation), OR
            # 2. Current line ends with continuation punctuation AND next doesn't start with uppercase
            should_join = False
            
            if starts_with_lowercase:
                # Next line clearly continues the sentence
                should_join = True
            elif ends_with_continuation and next_stripped and not next_stripped[0].isupper():
                # Current line has continuation punctuation and next doesn't start new sentence
                should_join = True
            
            if should_join:
                # Join with a space
                current_line = current_line + ' ' + next_stripped
                i += 1  # Move to next line
            else:
                # Don't join, stop here
                break
        
        # Add the (possibly joined) line
        fixed_lines.append(current_line)
        i += 1
    
    text = '\n'.join(fixed_lines)
    
    # Final cleanup: remove excessive spaces
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n +', '\n', text)  # Remove leading spaces after newlines
    
    return text.strip()

def convert_image_to_text(image_path):
    """
    Convert an image file to text using OCR with multiple preprocessing methods
    Args:
        image_path (str): Path to the input image file
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Preprocess image with multiple methods
        processed_images = preprocess_image(image)
        
        # OCR with better configuration for accuracy
        custom_config = r'--oem 3 --psm 6'
        
        # Try OCR with all preprocessing methods and combine results
        all_texts = []
        for processed_image in processed_images:
            text = pytesseract.image_to_string(
                processed_image,
                config=custom_config,
                lang='eng'
            )
            if text and text.strip():
                all_texts.append(text)
        
        # Use the longest result (likely the most complete)
        if all_texts:
            text = max(all_texts, key=len)
        else:
            text = ""
        
        # Clean the extracted text
        text = clean_text(text)
        
        return text
        
    except Exception as e:
        print(f"Error processing image: {e}")
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
    
    # Sort files to process in order
    image_files.sort()
    
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
    
    print("\nProcessing...")
    
    # Create single output file
    combined_filename = "all_extracted_text_combined.txt"
    combined_path = os.path.join(output_folder, combined_filename)
    
    # Collect all extracted text
    all_text_parts = []
    
    # Process each image
    for image_filename in image_files:
        image_path = os.path.join(input_folder, image_filename)
        
        print(f"\nConverting: {image_filename}")
        
        # Convert image to text
        text = convert_image_to_text(image_path)
        
        if text:
            all_text_parts.append(text)
            print(f"Success")
        else:
            print(f"Failed: {image_filename}")
    
    # Write all text to single file
    if all_text_parts:
        with open(combined_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(all_text_parts))
        print(f"\nAll text saved to: {combined_filename}")
    else:
        print("\nNo text extracted from any images")

if __name__ == "__main__":
    main()
