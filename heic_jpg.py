# heic_jpg.py
# converts .heic images to .jpg

import os
import glob
from PIL import Image
import pillow_heif

# Register HEIF opener with Pillow so it can read .heic files
pillow_heif.register_heif_opener()

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folders
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')


def convert_heic_to_jpg():
    """Convert all HEIC files in input folder to JPG files in output folder"""

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Find all HEIC files (case-insensitive by checking both cases)
    heic_files = glob.glob(os.path.join(input_folder, '*.heic')) + \
                 glob.glob(os.path.join(input_folder, '*.HEIC'))

    # check for heic files
    if not heic_files:
        jpg_present = glob.glob(os.path.join(input_folder, '*.jpg')) + \
                      glob.glob(os.path.join(input_folder, '*.jpeg'))
        if jpg_present:
            print("That file is already in jpg format")
        else:
            print("No HEIC files found in input folder")
        return

    print(f"Found {len(heic_files)} HEIC files to convert")


    for heic_file in heic_files:
        try:
            filename = os.path.splitext(os.path.basename(heic_file))[0]
            jpg_file = os.path.join(output_folder, f"{filename}.jpg")

            with Image.open(heic_file) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(jpg_file, 'JPEG', quality=95)
                print(f"Converted: {os.path.basename(heic_file)} -> {filename}.jpg")

        except Exception as e:
            print(f"Error converting {heic_file}: {str(e)}")


if __name__ == "__main__":
    convert_heic_to_jpg()
