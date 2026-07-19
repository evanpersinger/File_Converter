"""Convert PDF files to Markdown using OpenAI's Vision API.

For each .pdf in input/, sends the pages through the vision-parse library (backed by
an OpenAI vision model) to produce high-quality markdown, retrying with backoff on
connection errors. Writes to output/. Requires OPENAI_API_KEY in a .env file.
"""


from vision_parse import VisionParser   # Library for PDF to markdown conversion
from dotenv import load_dotenv          # Load environment variables from .env file
import os                               # File system operations
import time                             # For retry delays
from pathlib import Path

load_dotenv()

# Define input and output directories relative to this script
script_dir = Path(__file__).resolve().parent
input_dir  = script_dir / "input"   # Folder containing PDF files to convert
output_dir = script_dir / "output"  # Folder where converted markdown files will be saved


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


def _build_parser(api_key: str) -> VisionParser:
    """Build the VisionParser, falling back to URL mode if base64 is unavailable."""
    # Try "base64" mode first as it's more reliable than "url" for local files
    try:
        return VisionParser(
            model_name="gpt-4o-mini",           # OpenAI model for processing
            api_key=api_key,                    # API key from environment
            temperature=0,                      # Deterministic, faithful extraction (no paraphrasing)
            image_mode="base64",                # Process images as base64 (more reliable than URL)
            detailed_extraction=True,           # Capture tables, equations, and complex layouts
            enable_concurrency=False,           # Disable concurrency to avoid connection issues
        )
    except Exception as e:
        # Fallback to URL mode if base64 doesn't work
        print(f"Warning: Could not initialize with base64 mode, trying URL mode: {e}")
        return VisionParser(
            model_name="gpt-4o-mini",
            api_key=api_key,
            temperature=0,
            image_mode="url",
            detailed_extraction=True,
            enable_concurrency=False,
        )


def convert_pdf_to_markdown_openai() -> str:
    """Convert all PDF files in the input folder to Markdown using OpenAI's Vision API.

    Higher quality than the local pdf_md.py converter, but slower and it costs money.
    Requires OPENAI_API_KEY to be set in the environment or a .env file.

    Returns:
        A summary of what was converted, suitable for showing to a caller.
    """
    # Check the API key here rather than at import time, so importing this module
    # never kills the calling process.
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return "Error: OPENAI_API_KEY not found. Please add OPENAI_API_KEY to your .env file"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process all PDF files in the input directory
    entries = list(os.listdir(input_dir)) if input_dir.is_dir() else []
    pdf_names = [n for n in entries if n.lower().endswith(".pdf")]

    # If there are no PDFs but there are Markdown files, say so and stop
    if not pdf_names:
        md_present = [n for n in entries if n.lower().endswith(".md")]
        if md_present:
            return "That file is already in md format"
        return "No PDF files found in input folder"

    parser = _build_parser(api_key)

    converted = []
    errors = []

    for pdf_name in pdf_names:
        # Create full path to the PDF file
        pdf_path = input_dir / pdf_name

        try:
            print(f"Processing {pdf_name}...")
            # Convert PDF to markdown with retry logic
            pages = convert_with_retry(parser, pdf_path)

            if not pages:
                print(f"Failed to convert {pdf_name}")
                errors.append(f"{pdf_name}: conversion returned no pages")
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
            converted.append(out_md)

        except Exception as e:
            print(f"Error converting {pdf_name}: {e}")
            print("Tip: If this is an image-based PDF, try converting the original JPG/PNG instead")
            errors.append(f"{pdf_name}: {e}")
            continue

    if not converted:
        return f"No files converted. {len(errors)} failed: {'; '.join(errors)}"

    summary = f"Converted {len(converted)} file(s) to output/: {', '.join(converted)}"
    if errors:
        summary += f". {len(errors)} failed: {'; '.join(errors)}"
    return summary


if __name__ == "__main__":
    print(convert_pdf_to_markdown_openai())
