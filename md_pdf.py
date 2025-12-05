# md_pdf.py
# converts markdown files to pdf

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from shutil import which


# verify that a command exists before processing
def command_exists(cmd): 
    return which(cmd) is not None


def convert_md_to_pdf(md_path: str, output_path: str | None = None) -> bool:
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
        # Convert \[...\] to $$...$$ for better pandoc compatibility
        # This handles display math blocks more reliably
        md_content = re.sub(r'\\\[', '$$', md_content)
        md_content = re.sub(r'\\\]', '$$', md_content)
        
        # Replace em-dashes globally (they can break LaTeX rendering)
        md_content = md_content.replace('—', '-').replace('–', '-')
        
        # Normalize table spacing: fix spacing around | pipes while preserving cell content
        # This is necessary because inconsistent spacing can break pandoc's table parser
        lines = md_content.split('\n')
        cleaned_lines = []
        
        # Track table context to detect problematic header rows
        prev_line_was_table = False
        prev_cell_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Check if this is a table row
            if stripped.startswith('|') and '|' in stripped[1:]:
                # Check if separator row
                is_separator = bool(re.match(r'^\|\s*[-:]+\s*(\|\s*[-:]+\s*)*\|?\s*$', stripped))
                
                if is_separator:
                    # Normalize separator row spacing
                    parts = stripped.split('|')
                    cells = []
                    for part in parts[1:-1]:  # Skip first and last empty parts
                        # Get the separator content (hyphens/colons)
                        sep_content = re.sub(r'[^\-\:]', '', part)  # Keep only - and :
                        if not sep_content:
                            sep_content = '---'
                        cells.append(sep_content)
                    # Rejoin with consistent spacing: | --- | --- |
                    cleaned_line = '| ' + ' | '.join(cells) + ' |'
                    cleaned_lines.append(cleaned_line)
                    prev_cell_count = len(cells)
                    prev_line_was_table = True
                else:
                    # Regular table row: normalize spacing around pipes, preserve cell content
                    parts = stripped.split('|')
                    cells = []
                    for part in parts[1:-1]:  # Skip first and last empty parts
                        # Strip whitespace but preserve empty cells as empty strings
                        cell_content = part.strip()
                        # Protect negative numbers from line breaks by wrapping in mbox
                        # This prevents LaTeX from breaking "-47" across lines
                        # Split by $ to handle math mode separately
                        parts_math = cell_content.split('$')
                        protected_parts = []
                        for j, part in enumerate(parts_math):
                            if j % 2 == 0:
                                # Not in math mode - protect negative numbers
                                part = re.sub(r'(-\d+)', r'\\mbox{\1}', part)
                            protected_parts.append(part)
                        cell_content = '$'.join(protected_parts)
                        cells.append(cell_content)
                    
                    # Convert spanning header rows to centered captions above the table
                    # These break table parsing when they have fewer cells than the main table
                    # (e.g., "|          | Bolt |" with only 2 cells when table has 7 columns)
                    if len(cells) <= 3 and i + 1 < len(lines):  # Allow up to 3 cells for spanning headers
                        next_stripped = lines[i + 1].strip()
                        # If next line is a proper table row (has more cells), convert this to a caption
                        if next_stripped.startswith('|') and '|' in next_stripped[1:]:
                            next_parts = next_stripped.split('|')
                            next_cells = [p.strip() for p in next_parts[1:-1]]
                            if len(next_cells) > len(cells) + 1:  # Next row has significantly more cells
                                # This is a spanning header - extract all non-empty text
                                header_parts = [c for c in cells if c.strip()]
                                if header_parts:
                                    header_text = ' '.join(header_parts)
                                    # Add as a centered caption/header above the table
                                    # Use LaTeX centering with proper character escaping
                                    # Escape special LaTeX characters
                                    escaped_header = header_text.replace('\\', '\\textbackslash{}')
                                    escaped_header = escaped_header.replace('{', '\\{').replace('}', '\\}')
                                    escaped_header = escaped_header.replace('&', '\\&').replace('%', '\\%')
                                    escaped_header = escaped_header.replace('$', '\\$').replace('#', '\\#')
                                    escaped_header = escaped_header.replace('^', '\\textasciicircum{}')
                                    escaped_header = escaped_header.replace('_', '\\_').replace('~', '\\textasciitilde{}')
                                    cleaned_lines.append(f'\\begin{{center}}\\textbf{{{escaped_header}}}\\end{{center}}')
                                    cleaned_lines.append("")
                                prev_line_was_table = False
                                continue
                    
                    # Rejoin with consistent spacing: | cell | cell |
                    cleaned_line = '| ' + ' | '.join(cells) + ' |'
                    cleaned_lines.append(cleaned_line)
                    prev_cell_count = len(cells)
                    prev_line_was_table = True
            else:
                cleaned_lines.append(line)
                prev_line_was_table = False
        
        md_content = '\n'.join(cleaned_lines)
        
        # Convert horizontal rules (---) to spacing/breaks
        # Replace lines with exactly "---" with double newlines (paragraph break for spacing)
        md_content = re.sub(
            r'^---\s*$',
            r'\n\n',
            md_content,
            flags=re.MULTILINE
        )
        
        # Handle variables with bars (x̄, ȳ, z̄, etc.) - convert to LaTeX \bar{x}
        # Pattern matches letter followed by combining macron (U+0304)
        md_content = re.sub(
            r'([a-zA-Z])\u0304',  # letter + combining macron
            r'$\\bar{\1}$',
            md_content
        )
        
        # Also handle precomposed characters if they exist (x̄ as single character)
        # Convert x̄, ȳ, z̄, etc. to LaTeX \bar{x}
        bar_variables = {
            'x̄': r'$\\bar{x}$',
            'ȳ': r'$\\bar{y}$',
            'z̄': r'$\\bar{z}$',
            'X̄': r'$\\bar{X}$',
            'Ȳ': r'$\\bar{Y}$',
            'Z̄': r'$\\bar{Z}$',
        }
        for var, latex in bar_variables.items():
            # Replace if not already in math mode
            pattern = r'(?<!\$)' + re.escape(var) + r'(?!\$)'
            md_content = re.sub(pattern, latex, md_content)
        
        # Convert Unicode math symbols - some to LaTeX commands, some kept as Unicode in math mode
        # Symbols that need LaTeX commands (don't render well as Unicode)
        # Use double backslash in raw strings to get single backslash in the actual string
        symbol_replacements_latex = [
            (r'∑', r'\\sum'),
            (r'∫', r'\\int'),
            (r'∞', r'\\infty'),
            (r'≠', r'\\neq'),
        ]
        
        # Symbols to keep as Unicode but wrap in math mode for proper rendering
        # Note: ≤, ≥, ±, and ≈ work better as Unicode symbols in math mode than as LaTeX commands
        unicode_symbols = [r'ε', r'α', r'β', r'γ', r'δ', r'θ', r'λ', r'μ', r'σ', r'≤', r'≥', r'±', r'≈']
        
        # First, wrap Unicode symbols in math mode (keep the symbol, just ensure it renders)
        # Less restrictive pattern to catch symbols in parentheses and other contexts
        for symbol in unicode_symbols:
            # Only wrap if not already in math mode - allow symbols in parentheses and other contexts
            pattern = r'(?<!\$)' + re.escape(symbol) + r'(?!\$)'
            # Wrap in inline math mode to ensure proper rendering
            md_content = re.sub(pattern, lambda m, sym=symbol: f'${sym}$', md_content)
        
        # Then, convert symbols that need LaTeX commands
        # Process symbols that should always be in math mode
        for symbol, latex_cmd in symbol_replacements_latex:
            # Replace symbol if not immediately preceded or followed by $ (simple check)
            # This catches symbols in text like "P(X ≤ 3)" or "160 ≤ X"
            pattern = r'(?<!\$)' + re.escape(symbol) + r'(?!\$)'
            md_content = re.sub(pattern, lambda m, cmd=latex_cmd: f'${cmd}$', md_content)
            
            # Handle edge case: symbol appears right after closing $ (like $\bar{x}$ ± z)
            # Replace $...$symbol with $...$ $symbol$ (separate math blocks)
            pattern_after_math = r'(\$[^$]+\$)\s*' + re.escape(symbol) + r'(?!\$)'
            md_content = re.sub(pattern_after_math, lambda m, cmd=latex_cmd: f'{m.group(1)} ${cmd}$', md_content)
            
            # Clean up any nested math blocks that might have been created
            # But preserve $$...$$ for display math (don't convert to $...$)
        
        # Create temporary markdown file with processed content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(md_content)
            temp_md_path = temp_md.name
        
        # Create header file with LaTeX packages for better rendering of certain math symbols
        header_content = """\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{fontspec}
% Ensure horizontal rules render properly
\\usepackage{booktabs}
\\usepackage{longtable}
\\usepackage{array}
% Better table column alignment
\\usepackage{tabularx}
% Prevent line breaks in table cells with math
\\usepackage{makecell}
% Auto-adjust column widths to prevent wrapping
\\usepackage{adjustbox}
\\usepackage{colortbl}
% Set table column width handling
\\setlength{\\tabcolsep}{6pt}
\\renewcommand{\\arraystretch}{1.2}
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
                "--from=markdown+tex_math_dollars+pipe_tables+raw_html+raw_tex",  # Enable math, pipe tables, raw HTML, and raw LaTeX
                "--to=pdf",
            ]
            print(f"Converting '{full_input_path}' to '{full_output_path}' .")
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



