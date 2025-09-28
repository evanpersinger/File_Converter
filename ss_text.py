# ss_text.py
# This script converts an image to text using OCR

"""
Screenshot to Text Converter
Converts image files to text using OCR
"""

import pytesseract
from PIL import Image
import os
import sys
from pathlib import Path

def convert_image_to_text(image_path, output_path=None):
    """
    Convert an image file to text using OCR
    Args:
        image_path (str): Path to the input image file
        output_path (str, optional): Path to save the output text file
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Convert image to text using OCR
        text = pytesseract.image_to_string(image)
        
        # Save to file if output path is provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Text saved to: {output_path}")
        
        return text
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def main():
    """Main function to process all images in input folder"""
    input_folder = "input"
    output_folder = "output"
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: '{input_folder}' folder not found")
        sys.exit(1)
    
    # Get all image files from input folder
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    image_files = []
    
    for file in os.listdir(input_folder):
        if Path(file).suffix.lower() in image_extensions:
            image_files.append(file)
    
    if not image_files:
        print(f"No image files found in '{input_folder}' folder")
        print("Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP")
        sys.exit(1)
    
    print(f"Found {len(image_files)} image(s) to process:")
    for img in image_files:
        print(f"  - {img}")
    
    print("\nProcessing...")
    
    # Process each image
    successful = 0
    failed = 0
    
    for image_filename in image_files:
        image_path = os.path.join(input_folder, image_filename)
        
        # Create output filename
        input_name = Path(image_filename).stem
        output_filename = f"{input_name}_extracted_text.txt"
        output_path = os.path.join(output_folder, output_filename)
        
        print(f"\nConverting: {image_filename}")
        
        # Convert image to text
        text = convert_image_to_text(image_path, output_path)
        
        if text:
            successful += 1
            print(f"✅ Success: {output_filename}")
        else:
            failed += 1
            print(f"❌ Failed: {image_filename}")
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📁 Output folder: {output_folder}")

if __name__ == "__main__":
    main()
