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
            print(f"Failed: {image_filename}")
    
    print(f"\n Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Output folder: {output_folder}")
    
    # Combine all extracted text files into one
    combine_all_text_files(output_folder)

def combine_all_text_files(output_folder):
    """
    Combine all extracted text files into one single file
    Args:
        output_folder (str): Path to the output folder containing text files
    """
    try:
        # Get all extracted text files
        text_files = []
        for file in os.listdir(output_folder):
            if file.endswith('_extracted_text.txt'):
                text_files.append(file)
        
        if not text_files:
            print("No extracted text files found to combine")
            return
        
        # Sort files to ensure consistent order
        text_files.sort()
        
        # Create combined file
        combined_filename = "all_extracted_text_combined.txt"
        combined_path = os.path.join(output_folder, combined_filename)
        
        print(f"\nCombining {len(text_files)} text files into: {combined_filename}")
        
        with open(combined_path, 'w', encoding='utf-8') as combined_file:
            for i, text_file in enumerate(text_files):
                text_file_path = os.path.join(output_folder, text_file)
                
                # Read and write the content
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    combined_file.write(content)
                
                if i < len(text_files) - 1:  # Add newline between files (except last)
                    combined_file.write("\n")
        
        print(f"✅ Combined text saved to: {combined_path}")
        
    except Exception as e:
        print(f"Error combining text files: {e}")

if __name__ == "__main__":
    main()
