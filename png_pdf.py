# png_pdf.py
# converts png to pdf

import os
import glob
from PIL import Image

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folders
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')


def convert_png_to_pdf():
    """Convert all PNG files in input folder to PDF files in output folder"""
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Find all PNG files
    png_files = glob.glob(os.path.join(input_folder, '*.png'))
    
    if not png_files:
        # If there are only PDFs present, notify the user those are already in target format
        pdf_present = glob.glob(os.path.join(input_folder, '*.pdf'))
        if pdf_present:
            print("That file is already in pdf format")
        else:
            print("No PNG files found in input folder")
        return
    
    print(f"Found {len(png_files)} PNG files to convert")
    
    for png_file in png_files:
        try:
            # Get filename without extension
            filename = os.path.splitext(os.path.basename(png_file))[0]
            pdf_file = os.path.join(output_folder, f"{filename}.pdf")
            
            # Open and convert image to PDF
            with Image.open(png_file) as img:
                # Convert to RGB if necessary (PNG files often have transparency/RGBA)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as PDF
                img.save(pdf_file, "PDF", resolution=100.0)
                print(f"Converted: {os.path.basename(png_file)} -> {filename}.pdf")
                
        except Exception as e:
            print(f"Error converting {png_file}: {str(e)}")

if __name__ == "__main__":
    convert_png_to_pdf()

