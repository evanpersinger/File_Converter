# openai_pdf_md.py
# Converts PDF files to Markdown using OpenAI's Vision API
# Requires OpenAI API key stored in .env file
# Uses vision-parse library for high-quality PDF to markdown conversion


from vision_parse import VisionParser  # Library for PDF to markdown conversion
from dotenv import load_dotenv          # Load environment variables from .env file
import os                               # File system operations 
import sys                              # System operations (for exit)
import time                             # For retry delays
from pathlib import Path

load_dotenv()

# Check if API key exists
if 'OPENAI_API_KEY' not in os.environ:
    print("Error: OPENAI_API_KEY not found in environment variables")
    print("Please add OPENAI_API_KEY to your .env file")
    sys.exit(1)

# Define input and output directories relative to this script
script_dir = Path(__file__).resolve().parent
input_dir  = script_dir / "input"   # Folder containing PDF files to convert
output_dir = script_dir / "output"  # Folder where converted markdown files will be saved

# Ensure output directory exists
output_dir.mkdir(parents=True, exist_ok=True)


def convert_with_retry(parser, pdf_path, max_retries=3, retry_delay=5):
    """Convert PDF with retry logic for connection errors"""
    for attempt in range(max_retries):
        try:
            # Convert PDF to markdown (returns list of pages)
            pages = parser.convert_pdf(str(pdf_path))
            return pages
        except Exception as e:
            error_msg = str(e).lower()
            # Check if it's a connection error
            if "connection" in error_msg or "timeout" in error_msg or "network" in error_msg:
                if attempt < max_retries - 1:
                    print(f"Connection error (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise Exception(f"Connection failed after {max_retries} attempts: {e}")
            else:
                # Not a connection error, don't retry
                raise e
    return None


# Initialize parser with OpenAI model
# Try "base64" mode first as it's more reliable than "url" for local files
try:
    parser = VisionParser(
        model_name="gpt-4o-mini",           # OpenAI model for processing
        api_key=os.environ['OPENAI_API_KEY'], # API key from environment
        temperature=0.7,                    # Controls randomness (0-1)
        top_p=0.4,                          # Controls diversity of responses
        image_mode="base64",                # Process images as base64 (more reliable than URL)
        detailed_extraction=False,          # Basic extraction mode
        enable_concurrency=False,           # Disable concurrency to avoid connection issues
    )
except Exception as e:
    # Fallback to URL mode if base64 doesn't work
    print(f"Warning: Could not initialize with base64 mode, trying URL mode: {e}")
    parser = VisionParser(
        model_name="gpt-4o-mini",
        api_key=os.environ['OPENAI_API_KEY'],
        temperature=0.7,
        top_p=0.4,
        image_mode="url",
        detailed_extraction=False,
        enable_concurrency=False,
    )


# Process all PDF files in the input directory
entries = list(os.listdir(input_dir))
pdf_names = [n for n in entries if n.lower().endswith(".pdf")]

# If there are no PDFs but there are Markdown files, notify and exit early
if not pdf_names:
    md_present = [n for n in entries if n.lower().endswith(".md")]
    if md_present:
        print("That file is already in md format")
    else:
        print("No PDF files found in input folder")
    sys.exit(0)

for pdf_name in pdf_names:
    # Create full path to the PDF file
    pdf_path = input_dir / pdf_name

    try:
        print(f"Processing {pdf_name}...")
        # Convert PDF to markdown with retry logic
        pages = convert_with_retry(parser, pdf_path)
        
        if not pages:
            print(f"Failed to convert {pdf_name}")
            continue
            
        # Join all pages into a single markdown document
        full_md = "\n\n".join(pages)

        # Create output filename (replace .pdf with .md)
        base = pdf_name.rsplit(".pdf", 1)[0]  # Remove .pdf extension
        out_md = f"{base}.md"                 # Add .md extension
        out_path = output_dir / out_md

        # Write markdown content to output file
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_md)

        # confirmation message
        print(f"Converted {pdf_name} -> {out_md}")
    
    except Exception as e:
        print(f"Error converting {pdf_name}: {e}")
        print("Tip: If this is an image-based PDF, try converting the original JPG/PNG instead")
        continue


