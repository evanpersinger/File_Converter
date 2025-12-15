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
        # raw_tex doesn't always handle \[...\] correctly, so convert to $$...$$
        # Match pairs properly to avoid breaking existing $$...$$ blocks
        def convert_display_math(match):
            content = match.group(1)
            return f'$${content}$$'
        # Pattern: \[ followed by content until \], handling escaped characters
        md_content = re.sub(r'\\\[([^\\]*(?:\\.[^\\]*)*?)\\\]', convert_display_math, md_content)
        # Convert \(...\) to $...$ for inline math (only matched pairs)
        # This ensures we don't create unmatched delimiters
        # Match \( followed by content until \), handling escaped characters
        def convert_math(match):
            content = match.group(1)
            return f'${content}$'
        # Pattern: \( followed by any chars (including escaped ones) until \)
        md_content = re.sub(r'\\\(([^\\]*(?:\\.[^\\]*)*?)\\\)', convert_math, md_content)
        
        # Replace em-dashes globally (they can break LaTeX rendering)
        md_content = md_content.replace('—', '-').replace('–', '-')
        
        # Ensure lists are properly formatted - add blank line before lists if missing
        # This helps pandoc recognize lists correctly (especially after text like "where:")
        md_content = re.sub(r'([^\n])\n(- )', r'\1\n\n\2', md_content)
        md_content = re.sub(r'([^\n])\n(\* )', r'\1\n\n\2', md_content)
        md_content = re.sub(r'([^\n])\n(\d+\. )', r'\1\n\n\2', md_content)
        
        # Normalize table spacing: fix spacing around | pipes while preserving cell content
        # This is necessary because inconsistent spacing can break pandoc's table parser
        lines = md_content.split('\n')
        cleaned_lines = []
        
        # Track table context to detect problematic header rows and add space before tables
        prev_line_was_table = False
        prev_cell_count = 0
        in_table = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Check if this is a table row
            if stripped.startswith('|') and '|' in stripped[1:]:
                # If this is the start of a new table (not already in one), add space before it
                if not in_table and not prev_line_was_table:
                    # Add LaTeX commands to prevent page breaks within table only
                    # Don't use \samepage as it keeps content after table together too
                    cleaned_lines.append("")
                    cleaned_lines.append("\\nopagebreak[4]")
                    cleaned_lines.append("")
                    in_table = True
                
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
                        # Unescape dollar signs (some markdown files have \$ instead of $)
                        cell_content = cell_content.replace('\\$', '$')
                        # Convert existing \(...\) to $...$ for consistent handling in table cells
                        # Then combine adjacent $...$ expressions
                        def convert_math_to_dollars(text):
                            r"""Convert \(...\) to $...$ for table cells."""
                            result = []
                            i = 0
                            while i < len(text):
                                start = text.find('\\(', i)
                                if start == -1:
                                    result.append(text[i:])
                                    break
                                result.append(text[i:start])
                                # Find matching \)
                                depth = 0
                                j = start + 2
                                while j < len(text):
                                    if j < len(text) - 1 and text[j:j+2] == '\\(':
                                        depth += 1
                                        j += 2
                                    elif j < len(text) - 1 and text[j:j+2] == '\\)':
                                        if depth == 0:
                                            math_inner = text[start+2:j]
                                            result.append(f'${math_inner}$')
                                            i = j + 2
                                            break
                                        else:
                                            depth -= 1
                                            j += 2
                                    else:
                                        j += 1
                                else:
                                    result.append(text[start:])
                                    break
                            return ''.join(result)
                        
                        cell_content = convert_math_to_dollars(cell_content)
                        # Combine adjacent math expressions separated by math operators into a single math block
                        # This handles cases like "$d_i$ = $y_i$ - $x_i$" which should become one math block
                        # Keep using $...$ in table cells (pandoc handles this fine)
                        while True:
                            # Match $...$ [operator] $...$ and combine them
                            combined = re.sub(
                                r'\$([^\$]+?)\$\s*([=+\-×÷≤≥≠≈±])\s*\$([^\$]+?)\$',
                                r'$\1 \2 \3$',
                                cell_content
                            )
                            if combined == cell_content:
                                break
                            cell_content = combined
                        # Protect negative numbers from line breaks by wrapping in mbox
                        # This prevents LaTeX from breaking "-47" across lines
                        # Split by $...$ to separate math from non-math parts
                        # Protect negatives only outside math
                        parts_list = re.split(r'(\$[^\$]+\$)', cell_content)
                        protected_parts = []
                        for part in parts_list:
                            if part.startswith('$') and part.endswith('$'):
                                # This is math, keep as is
                                protected_parts.append(part)
                            else:
                                # Not math, protect negative numbers
                                protected_parts.append(re.sub(r'(-\d+)', r'\\mbox{\1}', part))
                        cell_content = ''.join(protected_parts)
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
                # If we were in a table and now we're not, add closing LaTeX commands
                if in_table and not stripped.startswith('|'):
                    # End table protection
                    # allow normal page breaks after table
                    cleaned_lines.append("\\nopagebreak[4]")
                    cleaned_lines.append("")
                    in_table = False
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
        
        # Convert Unicode subscripts to LaTeX subscripts before processing Greek letters
        # This ensures θ₀ becomes $\theta_0$ instead of $θ$₀
        subscript_map = {
            '₀': '_0', '₁': '_1', '₂': '_2', '₃': '_3', '₄': '_4', '₅': '_5',
            '₆': '_6', '₇': '_7', '₈': '_8', '₉': '_9',
            'ₐ': '_a', 'ₑ': '_e', 'ₕ': '_h', 'ᵢ': '_i', 'ⱼ': '_j', 'ₖ': '_k',
            'ₗ': '_l', 'ₘ': '_m', 'ₙ': '_n', 'ₒ': '_o', 'ₚ': '_p', 'ᵣ': '_r',
            'ₛ': '_s', 'ₜ': '_t', 'ᵤ': '_u', 'ᵥ': '_v', 'ₓ': '_x', 'ᵧ': '_y', 'ᵦ': '_z'
        }
        
        # Greek letter to LaTeX command mapping
        greek_to_latex = {
            'θ': r'\theta', 'ε': r'\varepsilon', 'α': r'\alpha', 'β': r'\beta',
            'γ': r'\gamma', 'δ': r'\delta', 'λ': r'\lambda', 'μ': r'\mu', 'σ': r'\sigma',
            'ρ': r'\rho', 'τ': r'\tau',  # Add rho and tau
            'Θ': r'\Theta', 'Ε': r'\Epsilon', 'Α': r'\Alpha', 'Β': r'\Beta',
            'Γ': r'\Gamma', 'Δ': r'\Delta', 'Λ': r'\Lambda', 'Μ': r'\Mu', 'Σ': r'\Sigma'
        }
        
        # Convert patterns like θ₀, θ₁, x₁, etc. to LaTeX
        # Match: letter/Greek + subscript, not already in math mode
        for subscript_unicode, subscript_latex in subscript_map.items():
            # Match any letter (including Greek) followed by subscript
            pattern = r'(?<!\$)([a-zA-Zα-ωΑ-Ωθε])(?<!\\\\)' + re.escape(subscript_unicode) + r'(?!\$)'
            def replace_with_subscript(match):
                base_char = match.group(1)
                latex_base = greek_to_latex.get(base_char, base_char)
                return f'${latex_base}{subscript_latex}$'
            md_content = re.sub(pattern, replace_with_subscript, md_content)
        
        # Convert LaTeX-style subscripts (B_j, p_i, T_i, etc.) to math mode
        # But skip if already inside math blocks (\[...\], $$...$$, $...$)
        # This handles cases like B_j, p_i, T_i, x_i, y_j, β_j, etc.
        def convert_underscore_subscript(match):
            base_char = match.group(1)
            subscript = match.group(2)
            # Check if base character is a Greek letter
            latex_base = greek_to_latex.get(base_char, base_char)
            return f'${latex_base}_{{{subscript}}}$'
        
        # First, protect math blocks by temporarily replacing them
        # Note: \[...\] has already been converted to $$...$$ earlier, so we only need to protect $$ and $
        math_blocks = []
        math_block_counter = 0
        
        # Protect $$...$$ blocks (display math) - must do this before protecting $...$
        def protect_dollar_math(match):
            nonlocal math_block_counter
            placeholder = f"__MATH_BLOCK_DOLLAR_{math_block_counter}__"
            math_blocks.append(('dollar', match.group(0), placeholder))
            math_block_counter += 1
            return placeholder
        
        # Match $$...$$ (non-greedy, handling escaped $)
        md_content = re.sub(r'\$\$([^$]*(?:\\.[^$]*)*?)\$\$', protect_dollar_math, md_content)
        
        # Protect $...$ blocks (inline math) - but be careful not to match $$
        def protect_inline_math(match):
            nonlocal math_block_counter
            placeholder = f"__MATH_BLOCK_INLINE_{math_block_counter}__"
            math_blocks.append(('inline', match.group(0), placeholder))
            math_block_counter += 1
            return placeholder
        
        md_content = re.sub(r'(?<!\$)\$([^$]+?)\$(?!\$)', protect_inline_math, md_content)
        
        # Now convert underscore subscripts (only outside math blocks)
        # Match: single letter (including Greek) + underscore + single letter/number
        md_content = re.sub(
            r'(?<![a-zA-Z0-9_])([a-zA-Zα-ωΑ-Ωθε])(?<!\\\\)_([a-zA-Z0-9])(?![a-zA-Z0-9_])',
            convert_underscore_subscript,
            md_content
        )
        
        # Restore protected math blocks
        for math_type, original, placeholder in reversed(math_blocks):
            md_content = md_content.replace(placeholder, original)
        
        # Convert standalone Greek letters to LaTeX commands (not already in math from subscripts)
        # Convert ε to \varepsilon (or \epsilon), and other Greek letters
        greek_standalone = {
            'ε': r'\varepsilon',  # Use \varepsilon for epsilon
            'θ': r'\theta',
            'π': r'\pi',  # Add pi
            'ρ': r'\rho', 'τ': r'\tau',  # Add rho and tau
            'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
            'λ': r'\lambda', 'μ': r'\mu', 'σ': r'\sigma'
        }
        for greek_char, latex_cmd in greek_standalone.items():
            # Only convert if not already in math mode
            pattern = r'(?<!\$)' + re.escape(greek_char) + r'(?!\$)'
            md_content = re.sub(pattern, lambda m, cmd=latex_cmd: f'${cmd}$', md_content)
        
        # Convert additional math symbols to LaTeX commands
        additional_symbols = {
            '⋈': r'\bowtie',  # Bowtie/join symbol
            '∪': r'\cup',      # Union
            '∩': r'\cap',      # Intersection (common with union)
            '∃': r'\exists',   # Existential quantifier
            '∀': r'\forall',   # Universal quantifier
            '∈': r'\in',       # Element of
            '∉': r'\notin',    # Not element of
            '⊆': r'\subseteq', # Subset or equal
            '⊂': r'\subset',  # Subset
            '∅': r'\emptyset', # Empty set
        }
        for symbol, latex_cmd in additional_symbols.items():
            # Only convert if not already in math mode
            pattern = r'(?<!\$)' + re.escape(symbol) + r'(?!\$)'
            md_content = re.sub(pattern, lambda m, cmd=latex_cmd: f'${cmd}$', md_content)
        
        # Combine adjacent math expressions that were just created (e.g., θ₀ + θ₁x becomes one block)
        # Match: $...$ followed by space/operator and $...$
        while True:
            combined = re.sub(
                r'\$([^$]+)\$\s*([+\-=])\s*\$([^$]+)\$',
                r'$\1 \2 \3$',
                md_content
            )
            if combined == md_content:
                break
            md_content = combined
        
        # Symbols to keep as Unicode but wrap in math mode for proper rendering
        # Note: ≤, ≥, ±, and ≈ work better as Unicode symbols in math mode than as LaTeX commands
        unicode_symbols = [r'≤', r'≥', r'±', r'≈']
        
        # Wrap remaining Unicode symbols in math mode (but skip if already in math from above)
        for symbol in unicode_symbols:
            # Only wrap if not already in math mode
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
\\usepackage{array}
% Better table column alignment
\\usepackage{tabularx}
% Prevent line breaks in table cells with math
\\usepackage{makecell}
% Auto-adjust column widths to prevent wrapping
\\usepackage{adjustbox}
\\usepackage{colortbl}
% Prevent page breaks within tables - keep tables together
\\usepackage{float}
% Configure table placement to avoid page breaks (H = here, don't float)
\\floatplacement{table}{H}
% Set table column width handling
\\setlength{\\tabcolsep}{6pt}
\\renewcommand{\\arraystretch}{1.2}
% Prevent page breaks within tables - keep entire tables on one page
\\usepackage{etoolbox}
% Prevent page breaks within tables, but allow normal flow after table
% Only prevents splitting within the table itself, not after it
\\preto\\table{\\nopagebreak[4]}
\\appto\\endtable{\\nopagebreak[4]}
% Prevent breaks in tabular environments - strong penalties to prevent splitting within table
\\preto\\tabular{\\nopagebreak[4]\\penalty10000\\begingroup}
\\appto\\endtabular{\\endgroup\\penalty10000\\nopagebreak[4]}
% Additional protection using AtBeginEnvironment - only within table
\\AtBeginEnvironment{table}{\\nopagebreak[4]}
\\AtEndEnvironment{table}{\\nopagebreak[4]}
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



