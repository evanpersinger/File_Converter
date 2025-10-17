# pptx_pdf.py
# converts pptx to pdf

import os
import glob
import subprocess
import sys

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Folders
input_folder = os.path.join(script_dir, 'input')
output_folder = os.path.join(script_dir, 'output')

def convert_pptx_to_pdf():
    """Convert all PPTX files in input folder to PDF files in output folder"""
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Find all PPTX files
    pptx_files = glob.glob(os.path.join(input_folder, '*.pptx'))
    
    if not pptx_files:
        # If only PDFs are present, notify the file(s) are already PDF
        pdf_present = glob.glob(os.path.join(input_folder, '*.pdf'))
        if pdf_present:
            print("That file is already in pdf format")
        else:
            print("No PPTX files found in input folder")
        return
    
    print(f"Found {len(pptx_files)} PPTX files to convert")
    
    # Resolve LibreOffice executable across platforms
    libreoffice_executables = [
        'libreoffice',  # common on Linux
        'soffice',      # common alias
        '/Applications/LibreOffice.app/Contents/MacOS/soffice'  # macOS app bundle
    ]
    resolved_executable = None
    for candidate in libreoffice_executables:
        try:
            check = subprocess.run([candidate, '--version'], capture_output=True, text=True)
            if check.returncode == 0 or 'LibreOffice' in check.stdout:
                resolved_executable = candidate
                break
        except FileNotFoundError:
            continue

    if not resolved_executable:
        print("LibreOffice not found in PATH.")
        print("On macOS (Homebrew cask): brew install --cask libreoffice")
        print("If already installed via .app, you can add a symlink:")
        print("  sudo ln -s /Applications/LibreOffice.app/Contents/MacOS/soffice /usr/local/bin/soffice")
        print("Then re-run this script.")
        return

    print(f"Using LibreOffice executable: {resolved_executable}")

    for pptx_file in pptx_files:
        try:
            # Get filename without extension
            filename = os.path.splitext(os.path.basename(pptx_file))[0]
            pdf_file = os.path.join(output_folder, f"{filename}.pdf")
            
            # Use LibreOffice to convert PPTX to PDF
            # This requires LibreOffice to be installed
            cmd = [
                resolved_executable,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_folder,
                pptx_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Converted: {os.path.basename(pptx_file)} -> {filename}.pdf")
            else:
                print(f"Error converting {pptx_file}: {result.stderr}")
                
        except FileNotFoundError:
            print("LibreOffice executable became unavailable during run. Please ensure it is installed and on PATH.")
            break
        except Exception as e:
            print(f"Error converting {pptx_file}: {str(e)}")

if __name__ == "__main__":
    convert_pptx_to_pdf()
