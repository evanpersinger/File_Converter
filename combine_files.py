# combine_files.py
# combines multiple files of the same type into one file

import os
import glob
from pathlib import Path
from PIL import Image
import pypdf

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folders
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')


def combine_pdfs(pdf_files, output_path):
    """Combine multiple PDF files into one PDF"""
    try:
        merger = pypdf.PdfMerger()
        
        for pdf_file in sorted(pdf_files):
            merger.append(pdf_file)
        
        merger.write(output_path)
        merger.close()
        return True
    except Exception as e:
        print(f"Error combining PDFs: {e}")
        return False


def combine_images(image_files, output_path, output_format='png'):
    """Combine multiple image files into one image (vertical strip)"""
    try:
        images = []
        max_width = 0
        total_height = 0
        
        # Load all images and calculate dimensions
        for img_file in sorted(image_files):
            with Image.open(img_file) as img:
                # Convert to RGB if saving as JPG, otherwise keep original mode
                if output_format.lower() == 'jpg' and img.mode != 'RGB':
                    img = img.convert('RGB')
                elif output_format.lower() != 'jpg' and img.mode == 'RGBA':
                    # Keep transparency for PNG
                    pass
                images.append(img.copy())
                max_width = max(max_width, img.width)
                total_height += img.height
        
        if not images:
            return False
        
        # Create a new image with combined dimensions
        if output_format.lower() == 'jpg':
            combined = Image.new('RGB', (max_width, total_height), color='white')
        else:
            combined = Image.new('RGBA', (max_width, total_height), color=(255, 255, 255, 0))
        
        # Paste images vertically
        current_height = 0
        for img in images:
            # Center images if widths differ
            x_offset = (max_width - img.width) // 2
            combined.paste(img, (x_offset, current_height), img if img.mode == 'RGBA' else None)
            current_height += img.height
        
        # Save combined image
        combined.save(output_path, output_format.upper(), quality=95)
        return True
    except Exception as e:
        print(f"Error combining images: {e}")
        return False


def combine_text_files(text_files, output_path):
    """Combine multiple text files into one text file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for text_file in sorted(text_files):
                with open(text_file, 'r', encoding='utf-8') as infile:
                    # Add filename as header
                    outfile.write(f"\n{'='*60}\n")
                    outfile.write(f"File: {os.path.basename(text_file)}\n")
                    outfile.write(f"{'='*60}\n\n")
                    outfile.write(infile.read())
                    outfile.write("\n\n")
        return True
    except Exception as e:
        print(f"Error combining text files: {e}")
        return False


def combine_files():
    """Main function to combine files by type"""
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Find all files by type
    pdf_files = glob.glob(os.path.join(input_folder, '*.pdf'))
    image_files = glob.glob(os.path.join(input_folder, '*.jpg')) + \
                  glob.glob(os.path.join(input_folder, '*.jpeg')) + \
                  glob.glob(os.path.join(input_folder, '*.png')) + \
                  glob.glob(os.path.join(input_folder, '*.gif')) + \
                  glob.glob(os.path.join(input_folder, '*.bmp'))
    text_files = glob.glob(os.path.join(input_folder, '*.txt')) + \
                 glob.glob(os.path.join(input_folder, '*.md'))
    
    # Combine PDFs
    if len(pdf_files) > 1:
        output_path = os.path.join(output_folder, 'combined.pdf')
        print(f"Combining {len(pdf_files)} PDF files...")
        if combine_pdfs(pdf_files, output_path):
            print(f"✓ Combined PDFs saved to: combined.pdf")
        else:
            print("✗ Failed to combine PDFs")
    elif len(pdf_files) == 1:
        print("Only 1 PDF file found. Need at least 2 files to combine.")
    
    # Combine images
    if len(image_files) > 1:
        # Determine output format based on first image
        first_ext = os.path.splitext(image_files[0])[1].lower()
        if first_ext in ['.jpg', '.jpeg']:
            output_path = os.path.join(output_folder, 'combined_images.jpg')
            output_format = 'jpg'
        else:
            output_path = os.path.join(output_folder, 'combined_images.png')
            output_format = 'png'
        
        print(f"Combining {len(image_files)} image files...")
        if combine_images(image_files, output_path, output_format):
            print(f"✓ Combined images saved to: {os.path.basename(output_path)}")
        else:
            print("✗ Failed to combine images")
    elif len(image_files) == 1:
        print("Only 1 image file found. Need at least 2 files to combine.")
    
    # Combine text files
    if len(text_files) > 1:
        output_path = os.path.join(output_folder, 'combined_text.txt')
        print(f"Combining {len(text_files)} text files...")
        if combine_text_files(text_files, output_path):
            print(f"✓ Combined text files saved to: combined_text.txt")
        else:
            print("✗ Failed to combine text files")
    elif len(text_files) == 1:
        print("Only 1 text file found. Need at least 2 files to combine.")
    
    # Summary
    total_files = len(pdf_files) + len(image_files) + len(text_files)
    if total_files == 0:
        print("No files found in input folder to combine.")
    elif total_files == 1:
        print("Only 1 file found. Need at least 2 files to combine.")


if __name__ == "__main__":
    combine_files()

