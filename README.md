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

## Folder Structure
```
converter/
├── input/              # Put your source files here
├── output/             # Converted files will appear here
├── xlsx_csv.py         # Excel to CSV converter
├── pdf_md.py           # PDF to Markdown converter (basic)
├── openai_pdf_md.py    # PDF to Markdown converter (AI-powered)
├── ss_text.py          # Screenshot to text converter (OCR)
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
