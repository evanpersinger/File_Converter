# File Converter

Simple scripts to convert files between different formats.

## Scripts

### xlsx_csv.py
Converts Excel (.xlsx) to CSV (.csv).

### pdf_md.py
Converts PDF files to Markdown format using text extraction, with optional OCR fallback.

**Usage:**
```bash
python pdf_md.py
```

**Python packages (versions from requirements.txt):**
- pypdf==6.1.2
- pdfplumber==0.11.7
- pdfminer-six==20250506
- pytesseract==0.3.13
- pillow==12.0.0

**System requirements (optional for OCR):**
- Tesseract OCR (macOS: `brew install tesseract`)

### openai_pdf_md.py
Converts PDF files to Markdown using OpenAI's Vision API for high-quality conversion.

**Usage:**
```bash
python openai_pdf_md.py
```

**Python packages (versions from requirements.txt):**
- vision-parse==0.1.13
- python-dotenv==1.1.1
- openai==2.5.0 (transitive dependency via vision-parse)

**Configuration:**
1. Create a `.env` file in the project root
2. Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

**Setup:**
```bash
pip install vision-parse python-dotenv
```

### ss_text.py
Converts screenshots and images to text using OCR (Optical Character Recognition).

**Usage:**
```bash
python ss_text.py
```

**Python packages (versions from requirements.txt):**
- pytesseract==0.3.13
- pillow==12.0.0

**System requirements:**
- Tesseract OCR (macOS: `brew install tesseract`)

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

**Python packages (versions from requirements.txt):**
- jupyter==1.1.1
- nbconvert==7.16.6
- nbclient==0.10.2
- nbformat==5.10.4
- jinja2==3.1.6
- traitlets==5.14.3

**System requirements:**
- LaTeX distribution for PDF export (macOS: `brew install --cask mactex`)

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

### md_pdf.py
Converts Markdown (.md) files to PDF using Pandoc.

**Usage:**
```bash
python md_pdf.py file.md [output.pdf]
```

**Python packages (versions from requirements.txt):**
- nbconvert==7.16.6 (only for pandocfilters; not strictly required to run pandoc)
- pandocfilters==1.5.1 (installed, but conversion is done by the pandoc CLI)

**System requirements:**
- Pandoc (macOS: `brew install pandoc`)
- LaTeX engine (XeLaTeX recommended) for PDF generation (macOS: `brew install --cask mactex`)

### html_pdf.py
Converts HTML files to PDF. Prefers `wkhtmltopdf`; falls back to `pandoc` if unavailable.

**Usage:**
```bash
python html_pdf.py file.html [output.pdf]
```

**Python packages:**
- None beyond the standard library

**System requirements:**
- wkhtmltopdf (recommended for best HTML rendering) — macOS: `brew install wkhtmltopdf`
- or Pandoc with LaTeX engine (fallback) — macOS: `brew install pandoc` and `brew install --cask mactex`

### jpg_pdf.py
Converts JPG/JPEG images to PDF files.

**Usage:**
```bash
python jpg_pdf.py
```

**Python packages (versions from requirements.txt):**
- pillow==12.0.0

**How it works:**
1. Automatically processes ALL JPG/JPEG files in the `input/` folder
2. Converts images to PDF format
3. Saves PDF files to the `output/` folder
4. Shows summary of successful/failed conversions

### pptx_pdf.py
Converts PowerPoint (.pptx) files to PDF using LibreOffice.

**Usage:**
```bash
python pptx_pdf.py
```

**Python packages:**
- None beyond the standard library

**System requirements:**
- LibreOffice (macOS: `brew install --cask libreoffice`)
- Alternative: Add symlink if LibreOffice is installed as .app:
  ```bash
  sudo ln -s /Applications/LibreOffice.app/Contents/MacOS/soffice /usr/local/bin/soffice
  ```

**How it works:**
1. Automatically processes ALL PPTX files in the `input/` folder
2. Uses LibreOffice headless mode to convert to PDF
3. Saves PDF files to the `output/` folder
4. Shows summary of successful/failed conversions

### Rmd_pdf.py
Converts R Markdown (.Rmd) files to PDF. Prefers R's rmarkdown; falls back to pandoc if R unavailable.

**Usage:**
```bash
python Rmd_pdf.py file.Rmd [output.pdf]
```

**Python packages:**
- None beyond the standard library

**System requirements:**
- R with rmarkdown package (recommended for R code execution)
  ```bash
  # Install R (macOS)
  brew install r
  # Install rmarkdown package
  Rscript -e 'install.packages("rmarkdown")'
  ```
- or Pandoc with LaTeX engine (fallback) — macOS: `brew install pandoc` and `brew install --cask mactex`

**How it works:**
1. Tries R's rmarkdown first (executes R code chunks)
2. Falls back to pandoc if R unavailable (treats as plain markdown)
3. Saves PDF files to the `output/` folder

## Folder Structure
```
converter/
├── input/              # Put your source files here
├── output/             # Converted files will appear here
├── xlsx_csv.py         # Excel to CSV converter
├── pdf_md.py           # PDF to Markdown converter (basic + OCR)
├── openai_pdf_md.py    # PDF to Markdown converter (AI-powered)
├── ss_text.py          # Screenshot to text converter (OCR)
├── ipynb_pdf.py        # Jupyter notebook to PDF converter
├── md_pdf.py           # Markdown to PDF converter (Pandoc)
├── html_pdf.py         # HTML to PDF converter (wkhtmltopdf/Pandoc)
├── jpg_pdf.py          # JPG/JPEG to PDF converter
├── pptx_pdf.py         # PowerPoint to PDF converter (LibreOffice)
├── Rmd_pdf.py          # R Markdown to PDF converter
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
