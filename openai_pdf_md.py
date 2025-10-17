# openai_pdf_md.py
# Converts PDF files to Markdown using OpenAI's Vision API
# Requires OpenAI API key stored in .env file
# Uses vision-parse library for high-quality PDF to markdown conversion


from vision_parse import VisionParser  # Library for PDF to markdown conversion
from dotenv import load_dotenv          # Load environment variables from .env file
import os                               # File system operations 
from pathlib import Path

load_dotenv()


# Define input and output directories relative to this script
script_dir = Path(__file__).resolve().parent
input_dir  = script_dir / "input"   # Folder containing PDF files to convert
output_dir = script_dir / "output"  # Folder where converted markdown files will be saved

# Ensure output directory exists
output_dir.mkdir(parents=True, exist_ok=True)



# Initialize parser with OpenAI model
parser = VisionParser(
    model_name="gpt-4o-mini",           # OpenAI model for processing
    api_key=os.environ['OPENAI_API_KEY'], # API key from environment
    temperature=0.7,                    # Controls randomness (0-1)
    top_p=0.4,                          # Controls diversity of responses
    image_mode="url",                   # Process images via URL
    detailed_extraction=False,          # Basic extraction mode
    enable_concurrency=True,            # Allow parallel processing
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
    pass

for pdf_name in pdf_names:
    # Skip files that aren't PDFs
    # already filtered to .pdf

    # Create full path to the PDF file
    pdf_path = os.path.join(input_dir, pdf_name)

    # Convert PDF to markdown (returns list of pages)
    pages = parser.convert_pdf(pdf_path)
    # Join all pages into a single markdown document
    full_md = "\n\n".join(pages)

    # Create output filename (replace .pdf with .md)
    base = os.path.splitext(pdf_name)[0]  # Remove .pdf extension
    out_md = f"{base}.md"                 # Add .md extension
    out_path = os.path.join(output_dir, out_md)

    # Write markdown content to output file
    with open(out_path, "w") as f:
        f.write(full_md)

    # confirmation message
    print(f"Converted {pdf_name} -> {out_md}")


