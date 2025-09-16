# File Converter

Simple scripts to convert files between different formats.

## Scripts

### xlsx_csv.py
Converts Excel (.xlsx) to CSV (.csv).

### pdf_md.pyu
Converts pdf (.pdf) to markdown (.md).

**Usage:**
```bash
python xlsx_csv.py
```

**Requirements:**
- pandas

**Setup:**
```bash
pip install pandas
```

### pdf_md.py
Converts PDF files to Markdown format.

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

## Folder Structure
```
converter/
├── input/          # Put your source files here
├── output/         # Converted files will appear here
├── xlsx_csv.py     # Excel to CSV converter
├── pdf_md.py       # PDF to Markdown converter
└── requirements.txt
```

## How to Use
1. Put your files in the `input` folder
2. Run the appropriate script
3. Find converted files in the `output` folder
