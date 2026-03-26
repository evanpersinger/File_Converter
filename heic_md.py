# heic_md.py
# converts .heic images to .md using OCR

import os
import glob
import re
import pytesseract
import pillow_heif
from PIL import Image, ImageEnhance, ImageFilter

pillow_heif.register_heif_opener()

script_dir = os.path.dirname(os.path.abspath(__file__))

# input and output folders
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')


def preprocess_image(image):
    """Preprocess image to improve OCR accuracy"""
    if image.mode != 'L':
        image = image.convert('L')

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)

    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.2)

    image = image.filter(ImageFilter.MedianFilter(size=3))

    return image



def clean_text(text):
    """Clean extracted text and format as markdown"""
    if not text:
        return ""

    text = re.sub(r'\n{3,}', '\n\n', text)

    lines = [line.rstrip() for line in text.split('\n')]

    # fix sentence structure
    fixed_lines = []
    i = 0
    while i < len(lines):
        current_line = lines[i]

        if not current_line.strip():
            fixed_lines.append(current_line)
            i += 1
            continue

        while i + 1 < len(lines):
            next_line = lines[i + 1]

            if not next_line.strip():
                break

            # check if next line starts with lowercase
            next_stripped = next_line.strip()
            starts_with_lowercase = next_stripped and next_stripped[0].islower()
            ends_with_continuation = re.search(r'[,;:—–-]\s*$', current_line)

            should_join = False
            if starts_with_lowercase:
                should_join = True
            elif ends_with_continuation and next_stripped and not next_stripped[0].isupper():
                should_join = True

            if should_join:
                current_line = current_line + ' ' + next_stripped
                i += 1
            else:
                break

        fixed_lines.append(current_line)
        i += 1

    text = '\n'.join(fixed_lines)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n +', '\n', text)

    return text.strip()


def convert_heic_to_markdown():
    """Convert all HEIC files in input folder to Markdown files in output folder"""

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    heic_files = glob.glob(os.path.join(input_folder, '*.heic')) + \
                 glob.glob(os.path.join(input_folder, '*.HEIC'))

    if not heic_files:
        md_present = glob.glob(os.path.join(input_folder, '*.md'))
        if md_present:
            print("That file is already in markdown format")
        else:
            print("No HEIC files found in input folder")
        return

    print(f"Found {len(heic_files)} HEIC files to convert")

    for heic_file in heic_files:
        try:
            filename = os.path.splitext(os.path.basename(heic_file))[0]
            md_file = os.path.join(output_folder, f"{filename}.md")

            with Image.open(heic_file) as img:
                processed_image = preprocess_image(img)

                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(
                    processed_image,
                    config=custom_config,
                    lang='eng'
                )

                text = clean_text(text)

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(text)

                print(f"Converted: {os.path.basename(heic_file)} -> {filename}.md")

        except Exception as e:
            print(f"Error converting {heic_file}: {str(e)}")


if __name__ == "__main__":
    convert_heic_to_markdown()
