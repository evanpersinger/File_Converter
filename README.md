# File Converter

Simple scripts to convert files between different formats. Includes an AI agent for interactive file conversion.

## Quick Start

### AI Agent (Interactive Conversion)
Use the AI agent to convert files through natural language:

```bash
python agent.py
```

Then ask it to convert files:
- "Convert mock1.md to PDF"
- "What files are in the input folder?"
- "Convert all Word documents to PDF"

The agent can use all conversion functions directly.

### Individual Scripts
Each script can be run independently for specific conversions (see details below).

## Scripts

### agent.py
AI-powered file conversion agent that can convert files through natural language interaction.

**Usage:**
```bash
python agent.py
```

**Python packages (versions from requirements.txt):**
- agents==1.4.0
- openai==1.75.0

**Features:**
- Interactive conversation interface
- Natural language file conversion requests
- Direct access to all conversion functions
- Web search capability for additional information

**Example interactions:**
- "Convert mock1.md to PDF"
- "List all files in the input folder"
- "What conversions are supported?"

### xlsx_csv.py
Converts Excel (.xlsx) to CSV (.csv).

**Usage:**
```bash
python xlsx_csv.py
```

**Python packages (versions from requirements.txt):**
- pandas==2.2.3

**How it works:**
1. Automatically processes ALL XLSX files in the `input/` folder
2. Converts Excel files to CSV format
3. Saves CSV files to the `output/` folder

### pdf_md.py
Converts PDF files to Markdown format using text extraction, with optional OCR fallback.

**Usage:**
```bash
python pdf_md.py
```

**Python packages (versions from requirements.txt):**
- pypdf==6.0.0
- pdfplumber==0.11.7
- pdfminer-six==20250506
- pytesseract==0.3.13
- pillow==11.3.0

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
- openai==1.75.0 (installed as dependency)

**Configuration:**
1. Create a `.env` file in the project root
2. Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

**Setup:**
```bash
pip install vision-parse python-dotenv
```

### ss_txt.py
Converts screenshots and images to text using OCR (Optical Character Recognition). Optimized for plain text extraction.

**Usage:**
```bash
python ss_txt.py
```

**Python packages (versions from requirements.txt):**
- pytesseract==0.3.13
- pillow==11.3.0

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
2. Preprocesses images for better OCR accuracy
3. Extracts text using OCR with proper sentence structure
4. Fixes random line breaks and preserves sentence flow
5. Saves combined text to `output/all_extracted_text_combined.txt`

**Features:**
- Image preprocessing for better accuracy
- Sentence structure preservation
- Automatic line break fixing

### ss_txt2.py
Advanced screenshot to text converter optimized for tables, shapes, and structured content.

**Usage:**
```bash
python ss_txt2.py
```

**Python packages (versions from requirements.txt):**
- pytesseract==0.3.13
- pillow==11.3.0
- opencv-python==4.12.0.88
- numpy==2.2.5

**System requirements:**
- Tesseract OCR (macOS: `brew install tesseract`)

**Features:**
- Table detection and extraction
- Shape detection
- Structured content recognition
- Better handling of complex layouts
- Saves to `output/all_extracted_structured_text.txt`

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
Converts Markdown (.md) files to PDF using Pandoc with enhanced math symbol and formatting support.

**Usage:**
```bash
# Convert all .md files in input/ folder
python md_pdf.py

# Convert specific file
python md_pdf.py file.md [output.pdf]
```

**Python packages (versions from requirements.txt):**
- nbconvert==7.16.6 (only for pandocfilters; not strictly required to run pandoc)
- pandocfilters==1.5.1 (installed, but conversion is done by the pandoc CLI)

**System requirements:**
- Pandoc (macOS: `brew install pandoc`)
- LaTeX engine (XeLaTeX recommended) for PDF generation (macOS: `brew install --cask mactex`)

**Features:**
- **Unicode math symbols**: Properly renders Unicode symbols in math mode:
  - Greek letters: ε (epsilon), α (alpha), β (beta), γ (gamma), δ (delta), θ (theta), λ (lambda), μ (mu), σ (sigma), ρ (rho), τ (tau), π (pi)
  - Comparison operators: ≤ (less than or equal), ≥ (greater than or equal)
  - Other symbols: ± (plus-minus), ≈ (approximately equal)
  - Set theory: ∪ (union), ∩ (intersection), ∈ (element of), ∃ (exists), ∀ (for all), ⋈ (bowtie)
- **Unicode subscripts**: Converts Unicode subscripts (₀, ₁, ₂, etc.) to LaTeX subscripts:
  - `θ₀` → `$\theta_0$`, `x₁` → `$x_1$`, `θₙ` → `$\theta_n$`
- **LaTeX math commands**: Converts complex symbols to LaTeX commands:
  - ∑ (sum), ∫ (integral), ∞ (infinity), ≠ (not equal)
- **Math expression combination**: Automatically combines adjacent math expressions in table cells:
  - `$d_i$ = $y_i$ - $x_i$` → `$d_i = y_i - x_i$`
- **Table page break prevention**: Tables automatically move to the next page if they don't fit, preventing tables from splitting across pages
- **Horizontal rules**: Converts `---` to proper spacing/breaks
- **Inline math mode**: Keeps math symbols on the same line as text
- **Font support**: Uses fontspec and amssymb for proper Unicode and LaTeX symbol rendering
- **Display math**: Supports both `$$...$$` and `\[...\]` for display math blocks

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
- pillow==11.3.0

**How it works:**
1. Automatically processes ALL JPG/JPEG files in the `input/` folder
2. Converts images to PDF format
3. Saves PDF files to the `output/` folder
4. Shows summary of successful/failed conversions

### png_pdf.py
Converts PNG images to PDF files.

**Usage:**
```bash
python png_pdf.py
```

**Python packages (versions from requirements.txt):**
- pillow==11.3.0

**How it works:**
1. Automatically processes ALL PNG files in the `input/` folder
2. Converts images to PDF format (handles transparency by converting to RGB)
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

### docx_pdf.py
Converts Microsoft Word (.docx) files to PDF format with proper table rendering, image extraction, and formatting preservation.

**Usage:**
```bash
# Option A: Convert all DOCX files in input/ directory
python docx_pdf.py

# Option B: Convert specific file
python docx_pdf.py file.docx [output.pdf]

# Option C: Use custom input/output directories
python docx_pdf.py --input-dir myinput --output-dir myoutput
```

**Python packages (versions from requirements.txt):**
- reportlab==4.4.4
- python-docx==1.1.2
- pillow==11.3.0

**How it works:**
1. Automatically processes ALL DOCX files in the `input/` folder
2. Extracts text, tables, and images from Word documents
3. Creates PDF with proper formatting, table rendering, and embedded images
4. Saves PDF files to the `output/` folder
5. Shows summary of successful/failed conversions

**Features:**
- Clean text formatting and spacing
- **Text formatting preservation** (bold, italic, underline)
- **Image extraction and embedding** with proper sizing
- **Proper text/image ordering** - maintains document structure
- Table rendering with borders and proper layout
- Preserves document structure (paragraphs, tables, and images in order)
- Support for UTF-8 encoding and special characters
- Custom input/output directories support

### sql_pdf.py
Converts SQL files to PDF format with syntax highlighting and proper formatting.

**Usage:**
```bash
# Option A: Convert all SQL files in input/ directory
python sql_pdf.py

# Option B: Convert specific file
python sql_pdf.py file.sql [output.pdf]
```

**Python packages (versions from requirements.txt):**
- reportlab==4.4.4

**How it works:**
1. Automatically processes ALL SQL files in the `input/` folder
2. Formats SQL with proper indentation and keyword highlighting
3. Creates PDF with syntax highlighting and clean formatting
4. Saves PDF files to the `output/` folder
5. Shows summary of successful/failed conversions

**Features:**
- SQL syntax highlighting
- Proper code formatting and indentation
- Clean PDF layout with title and formatted code blocks
- Support for all SQL dialects (MySQL, PostgreSQL, SQLite, etc.)

### txt_pdf.py
Converts text (.txt) files to PDF format with clean formatting.

**Usage:**
```bash
# Option A: Convert all TXT files in input/ directory
python txt_pdf.py

# Option B: Convert specific file
python txt_pdf.py file.txt [output.pdf]
```

**Python packages (versions from requirements.txt):**
- reportlab==4.4.4

**How it works:**
1. Automatically processes ALL TXT files in the `input/` folder
2. Creates PDF with clean formatting and readable fonts
3. Saves PDF files to the `output/` folder
4. Shows summary of successful/failed conversions

**Features:**
- Clean text formatting
- Proper line breaks and spacing
- Support for UTF-8 encoding

### R_Rmd.py
Converts R (.R) files to R Markdown (.Rmd) format.

**Usage:**
```bash
# Option A: Convert all R files in input/ directory
python R_Rmd.py

# Option B: Convert specific file
python R_Rmd.py file.R [output.Rmd]

# Option C: Use custom input/output directories
python R_Rmd.py --input-dir myinput --output-dir myoutput
```

**Python packages:**
- None beyond the standard library

**How it works:**
1. Reads R file and converts comments to markdown text
2. Wraps code sections in R code chunks (```{r} ... ```)
3. Formats headers and removes separator lines
4. Groups related code into logical chunks
5. Saves Rmd files to the `output/` folder

**Features:**
- Converts R comments to markdown text
- Groups code into logical chunks
- Formats section headers properly
- Removes separator lines (===)
- Formats name/ID at the top
- Limits empty lines for clean output

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

### combine_files.py
Combines multiple files into one output file. Automatically detects file types and combines accordingly.

**Usage:**
```bash
# Combine all files in input/ folder (auto-detects format)
python combine_files.py

# Combine specific files
python combine_files.py file1.jpg file2.jpg

# Combine with custom output name
python combine_files.py file1.pdf file2.pdf combined.pdf
```

**Python packages (versions from requirements.txt):**
- pillow==11.3.0
- pypdf==6.0.0

**How it works:**
1. Reads files from the `input/` folder (or specified files)
2. Automatically detects file types and combines:
   - **Images** (JPG, PNG, GIF, BMP, TIFF, WEBP) → stacks vertically into one image (`combined.jpg`)
   - **PDFs** → merges all pages into one PDF (`combined.pdf`)
   - **Text files** → concatenates with separators showing filenames (`combined.txt`)
3. Saves combined file to the `output/` folder
4. Skips system files like `.DS_Store`

**Features:**
- Auto-detects output format based on input files (JPG→JPG, PDF→PDF, etc.)
- Images are stacked vertically in a single image file
- Text files are concatenated with clear file separators
- PDFs are merged preserving all pages in order
- Handles mixed file types gracefully

## Folder Structure
```
converter/
├── input/              # Put your source files here
├── output/             # Converted files will appear here
├── agent.py            # AI agent for interactive file conversion
├── xlsx_csv.py         # Excel to CSV converter
├── pdf_md.py           # PDF to Markdown converter (basic + OCR)
├── openai_pdf_md.py    # PDF to Markdown converter (AI-powered)
├── ss_txt.py           # Screenshot to text converter (OCR, plain text)
├── ss_txt2.py          # Screenshot to text converter (OCR, structured content)
├── ipynb_pdf.py        # Jupyter notebook to PDF converter
├── md_pdf.py           # Markdown to PDF converter (Pandoc, enhanced)
├── html_pdf.py         # HTML to PDF converter (wkhtmltopdf/Pandoc)
├── jpg_pdf.py          # JPG/JPEG to PDF converter
├── png_pdf.py          # PNG to PDF converter
├── combine_files.py    # File combiner (PDFs, images, text)
├── pptx_pdf.py         # PowerPoint to PDF converter (LibreOffice)
├── docx_pdf.py         # Word to PDF converter
├── R_Rmd.py            # R to R Markdown converter
├── Rmd_pdf.py          # R Markdown to PDF converter
├── sql_pdf.py          # SQL to PDF converter
├── txt_pdf.py          # TXT to PDF converter
├── requirements.txt    # Python package dependencies
└── .env                # Store your OpenAI API key here (optional)
```

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create the required folders** (if they don't exist):
   ```bash
   mkdir input output
   ```

3. **Install system dependencies** (as needed):
   - Tesseract OCR: `brew install tesseract` (for OCR features)
   - Pandoc: `brew install pandoc` (for markdown/HTML conversions)
   - LaTeX: `brew install --cask mactex` (for PDF generation)
   - LibreOffice: `brew install --cask libreoffice` (for PowerPoint conversion)

4. **Optional: Set up OpenAI API key** (for `openai_pdf_md.py`):
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

## How to Use

### Using the AI Agent (Recommended)
1. Put your files in the `input` folder
2. Run: `python agent.py`
3. Ask the agent to convert files using natural language
4. Find converted files in the `output` folder

### Using Individual Scripts
1. Put your files in the `input` folder
2. Run the appropriate conversion script
3. Find converted files in the `output` folder

### File Overwriting
**Important:** Converting the same file multiple times will automatically overwrite the existing output file. For example:
- First conversion: `mock2.md` → `output/mock2.pdf` (creates new file)
- Second conversion: `mock2.md` → `output/mock2.pdf` (overwrites the existing PDF)

This means you can update your source file and convert it again to get an updated PDF without needing to delete the old one first.

## Supported Conversions

| From | To | Script |
|------|-----|--------|
| Markdown (.md) | PDF | `md_pdf.py` |
| PDF | Markdown (.md) | `pdf_md.py` |
| Word (.docx) | PDF | `docx_pdf.py` |
| PowerPoint (.pptx) | PDF | `pptx_pdf.py` |
| Excel (.xlsx) | CSV | `xlsx_csv.py` |
| HTML | PDF | `html_pdf.py` |
| Text (.txt) | PDF | `txt_pdf.py` |
| SQL | PDF | `sql_pdf.py` |
| Jupyter Notebook (.ipynb) | PDF | `ipynb_pdf.py` |
| Images (JPG/PNG) | PDF | `jpg_pdf.py`, `png_pdf.py` |
| Images (screenshots) | Text | `ss_txt.py`, `ss_txt2.py` |
| R (.R) | R Markdown (.Rmd) | `R_Rmd.py` |
| R Markdown (.Rmd) | PDF | `Rmd_pdf.py` |
