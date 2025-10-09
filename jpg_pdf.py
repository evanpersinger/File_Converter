# jpg_pdf.py
# converts jpg to pdf

import os
import glob
from PIL import Image

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folders
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')


def convert_jpg_to_pdf():
    """Convert all JPG files in input folder to PDF files in output folder"""
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Find all JPG files
    jpg_files = glob.glob(os.path.join(input_folder, '*.jpg')) + \
                glob.glob(os.path.join(input_folder, '*.jpeg'))
    
    if not jpg_files:
        print("No JPG files found in input folder")
        return
    
    print(f"Found {len(jpg_files)} JPG files to convert")
    
    for jpg_file in jpg_files:
        try:
            # Get filename without extension
            filename = os.path.splitext(os.path.basename(jpg_file))[0]
            pdf_file = os.path.join(output_folder, f"{filename}.pdf")
            
            # Open and convert image to PDF
            with Image.open(jpg_file) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as PDF
                img.save(pdf_file, "PDF", resolution=100.0)
                print(f"Converted: {os.path.basename(jpg_file)} -> {filename}.pdf")
                
        except Exception as e:
            print(f"Error converting {jpg_file}: {str(e)}")

if __name__ == "__main__":
    convert_jpg_to_pdf()

