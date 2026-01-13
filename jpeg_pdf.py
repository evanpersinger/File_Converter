# jpeg_pdf.py
# converts jpeg to pdf

import os
import glob
from PIL import Image

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folders
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')


def convert_jpeg_to_pdf():
    """Convert all JPEG files in input folder to PDF files in output folder"""
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Find all JPEG files
    jpeg_files = glob.glob(os.path.join(input_folder, '*.jpeg')) + \
                 glob.glob(os.path.join(input_folder, '*.jpg'))
    
    if not jpeg_files:
        # If there are only PDFs present, notify the user those are already in target format
        pdf_present = glob.glob(os.path.join(input_folder, '*.pdf'))
        if pdf_present:
            print("That file is already in pdf format")
        else:
            print("No JPEG files found in input folder")
        return
    
    print(f"Found {len(jpeg_files)} JPEG files to convert")
    
    for jpeg_file in jpeg_files:
        try:
            # Get filename without extension
            filename = os.path.splitext(os.path.basename(jpeg_file))[0]
            pdf_file = os.path.join(output_folder, f"{filename}.pdf")
            
            # Open and convert image to PDF
            with Image.open(jpeg_file) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as PDF
                img.save(pdf_file, "PDF", resolution=100.0)
                print(f"Converted: {os.path.basename(jpeg_file)} -> {filename}.pdf")
                
        except Exception as e:
            print(f"Error converting {jpeg_file}: {str(e)}")

if __name__ == "__main__":
    convert_jpeg_to_pdf()
