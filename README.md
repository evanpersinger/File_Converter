# File Converter

Simple scripts to convert files between different formats.

## Scripts

### xlsx_csv.py
Converts Excel (.xlsx) to CSV (.csv).

### pdf_md.py
Converts PDF files to Markdown format using basic text extraction.

**Usage:**
```bash
python pdf_md.py
```

**Requirements:**
- pypdf
- markdownify

**Setup:**
```bash
pip install pypdf markdownify
```

### openai_pdf_md.py
Converts PDF files to Markdown using OpenAI's Vision API for high-quality conversion.

**Usage:**
```bash
python openai_pdf_md.py
```

**Requirements:**
- vision-parse
- python-dotenv
- OpenAI API key

**Setup:**
```bash
pip install vision-parse python-dotenv
```

**Configuration:**
1. Create a `.env` file in the project root
2. Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

### ss_text.py
Converts screenshots and images to text using OCR (Optical Character Recognition).

**Usage:**
```bash
python ss_text.py
```

**Requirements:**
- pytesseract
- pillow
- tesseract OCR (system installation)

**Setup:**
```bash
# Install Tesseract OCR on macOS
brew install tesseract

# Python packages are already in requirements.txt
pip install pytesseract pillow
```

**Supported formats:**
- PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP

**How it works:**
1. Automatically processes ALL images in the `input/` folder
2. Extracts text using OCR
3. Saves text files to the `output/` folder
4. Shows summary of successful/failed conversions

### ipynb_pdf.py
Converts Jupyter notebooks (.ipynb) to PDF files.

**Usage:**
```bash
# Option A: run with no args – auto-detect a single notebook in input/
python ipynb_pdf.py

# Option B: specify a file (filename only; script prepends input/)
python ipynb_pdf.py notebook_name.ipynb
python ipynb_pdf.py notebook_name.ipynb custom_output.pdf
```

**Requirements:**
- jupyter
- nbconvert
- LaTeX (for PDF generation)

**Setup:**
```bash
pip install jupyter nbconvert
# Install LaTeX on macOS
brew install --cask mactex
```

**How it works:**
1. Put your `.ipynb` file in the `input/` folder
2. If you run without arguments and there is exactly one notebook in `input/`,
   the script prints only the file name (e.g., `HW2.ipynb`) and converts it.
3. If multiple notebooks are present, it lists them and asks you to specify one.
4. If none are present, it shows usage instructions.
5. PDF is saved to the `output/` folder. Custom output filenames are supported.

**Alternative (no LaTeX):**
If you prefer not to install LaTeX, you can export using the browser-based PDF:
```bash
pip install pyppeteer
jupyter nbconvert --to webpdf --output output/NAME.pdf input/NAME.ipynb
```

## Folder Structure
```
converter/
├── input/              # Put your source files here
├── output/             # Converted files will appear here
├── xlsx_csv.py         # Excel to CSV converter
├── pdf_md.py           # PDF to Markdown converter (basic)
├── openai_pdf_md.py    # PDF to Markdown converter (AI-powered)
├── ss_text.py          # Screenshot to text converter (OCR)
├── ipynb_pdf.py        # Jupyter notebook to PDF converter
├── requirements.txt
└── .env                # Store your OpenAI API key here
```

## How to Use
1. **Create the required folders** (if they don't exist):
   ```bash
   mkdir input output
   ```
2. Put your files in the `input` folder
3. Run the appropriate script
4. Find converted files in the `output` folder
