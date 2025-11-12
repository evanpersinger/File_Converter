# md_pdf.py
# converts markdown files to pdf

import os
import sys
import subprocess
from pathlib import Path
from shutil import which


def command_exists(cmd):
    return which(cmd) is not None


def convert_md_to_pdf(md_path, output_path=None):
    """
    Convert a .md file to PDF using pandoc.

    Args:
        md_path (str | Path): Path to the .md file (relative to input folder or absolute)
        output_path (str | Path | None): Desired output PDF filename. If None, uses input stem + .pdf

    Returns:
        bool: True if conversion successful, False otherwise
    """
    
    input_dir = Path("input")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Build full input path
    # if the provided path already points to a PDF, bail out early
    try:
        provided_suffix = Path(md_path).suffix.lower()
        if provided_suffix == ".pdf":
            print("That file is already in pdf format")
            return False
    except Exception:
        pass
    full_input_path = Path(md_path) if os.path.isabs(str(md_path)) else input_dir / md_path
    if not full_input_path.exists():
        print(f"Error: Markdown file '{full_input_path}' not found")
        return False

    # Compute output name
    if output_path is None:
        pdf_name = f"{full_input_path.stem}.pdf"
    else:
        pdf_name = Path(output_path).name
    full_output_path = output_dir / pdf_name

    if not command_exists("pandoc"):
        print("Error: pandoc not found. Please install pandoc to convert Markdown to PDF.")
        return False

    try:
        cmd = [
            "pandoc",
            str(full_input_path),
            "-o",
            str(full_output_path),
            "--pdf-engine=xelatex",
        ]
        print(f"Converting '{full_input_path}' to '{full_output_path}' using pandoc...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and full_output_path.exists():
            print(f"Successfully converted to '{full_output_path}'")
            return True
        else:
            print(f"pandoc failed: {result.stderr.strip() if result.stderr else 'unknown error'}")
            return False
    except Exception as e:
        print(f"Unexpected error running pandoc: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        # No args: convert all .md files in input/
        input_dir = Path("input")
        md_files = sorted(p for p in input_dir.glob("*.md"))
        if not md_files:
            print("No .md files found in input folder")
            print("Usage: python md_pdf.py <file.md> [output.pdf]")
            print("Example: python md_pdf.py notes.md")
            print("Example: python md_pdf.py notes.md my_notes.pdf")
            return
        any_failed = False
        for md in md_files:
            ok = convert_md_to_pdf(md.name, None)
            if not ok:
                any_failed = True
        if any_failed:
            sys.exit(1)
        return

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    success = convert_md_to_pdf(md_file, output_file)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()



