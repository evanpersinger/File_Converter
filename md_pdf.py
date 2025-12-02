# md_pdf.py
# converts markdown files to pdf

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from shutil import which


def command_exists(cmd): 
    return which(cmd) is not None


def convert_md_to_pdf(md_path, output_path=None):
    """

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
        # Preprocess markdown to handle math symbols
        # Read the markdown file and convert Unicode math symbols to LaTeX
        with open(full_input_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        import re
        # Convert horizontal rules (---) to spacing/breaks
        # Replace lines with exactly "---" with double newlines (paragraph break for spacing)
        md_content = re.sub(
            r'^---\s*$',
            r'\n\n',
            md_content,
            flags=re.MULTILINE
        )
        
        # Convert Unicode math symbols - some to LaTeX commands, some kept as Unicode in math mode
        # Symbols that need LaTeX commands (don't render well as Unicode)
        symbol_replacements_latex = [
            (r'≈', r'\\approx'),
            (r'∑', r'\\sum'),
            (r'∫', r'\\int'),
            (r'∞', r'\\infty'),
            (r'±', r'\\pm'),
            (r'≤', r'\\leq'),
            (r'≥', r'\\geq'),
            (r'≠', r'\\neq'),
        ]
        
        # Symbols to keep as Unicode but wrap in math mode for proper rendering
        unicode_symbols = [r'ε', r'α', r'β', r'γ', r'δ', r'θ', r'λ', r'μ', r'σ']
        
        # First, wrap Unicode symbols in math mode (keep the symbol, just ensure it renders)
        for symbol in unicode_symbols:
            # Only wrap if not already in math mode
            pattern = r'(?<!\$)(?<![a-zA-Z0-9])' + re.escape(symbol) + r'(?![a-zA-Z0-9])(?!\$)'
            # Wrap in inline math mode to ensure proper rendering
            md_content = re.sub(pattern, lambda m, sym=symbol: f'${sym}$', md_content)
        
        # Then, convert symbols that need LaTeX commands
        for symbol, latex_cmd in symbol_replacements_latex:
            # Only replace if symbol is not already in a $...$ block
            pattern = r'(?<!\$)(?<![a-zA-Z0-9])' + re.escape(symbol) + r'(?![a-zA-Z0-9])(?!\$)'
            # Use lambda to wrap in inline math mode ($...$)
            md_content = re.sub(pattern, lambda m, cmd=latex_cmd: f'${cmd}$', md_content)
        
        # Create temporary markdown file with processed content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(md_content)
            temp_md_path = temp_md.name
        
        # Create header file with LaTeX packages for better rendering
        # Keep it simple to avoid conflicts
        header_content = """\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{fontspec}
% Ensure horizontal rules render properly
\\usepackage{booktabs}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as header_file:
            header_file.write(header_content)
            header_path = header_file.name
        
        try:
            cmd = [
                "pandoc",
                temp_md_path,  # Use processed markdown file
                "-o",
                str(full_output_path),
                "--pdf-engine=xelatex",
                "--standalone",
                f"--include-in-header={header_path}",
                "--from=markdown",  # Standard markdown format
                "--to=pdf",
            ]
            print(f"Converting '{full_input_path}' to '{full_output_path}' using pandoc...")
            result = subprocess.run(cmd, capture_output=True, text=True)
        finally:
            # Clean up temp files
            try:
                os.unlink(header_path)
                os.unlink(temp_md_path)
            except:
                pass
        
        if result.returncode == 0 and full_output_path.exists():
            print(f"Successfully converted to '{full_output_path}'")
            return True
        else:
            error_msg = result.stderr.strip() if result.stderr else 'unknown error'
            if result.stdout:
                error_msg += f"\nstdout: {result.stdout.strip()}"
            print(f"pandoc failed: {error_msg}")
            return False
    except Exception as e:
        print(f"Unexpected error running pandoc: {e}")
        import traceback
        traceback.print_exc()
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



