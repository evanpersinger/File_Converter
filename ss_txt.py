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
        PIL Image: Preprocessed image
    """
    # Convert to grayscale for better OCR
    if image.mode != 'L':
        image = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.2)
    
    # Apply slight denoising
    image = image.filter(ImageFilter.MedianFilter(size=3))
    
    return image

def clean_text(text):
    """
    Clean extracted text by removing excessive whitespace
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
    text = '\n'.join(lines)
    
    return text.strip()

def convert_image_to_text(image_path):
    """
    Convert an image file to text using OCR with preprocessing
    Args:
        image_path (str): Path to the input image file
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Preprocess image for better OCR accuracy
        processed_image = preprocess_image(image)
        
        # OCR with better configuration for accuracy
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(
            processed_image,
            config=custom_config,
            lang='eng'
        )
        
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
