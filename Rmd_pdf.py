# Rmd_pdf.py
# converts restructured markdown file to pdf file


import os
import sys
import subprocess
import argparse
from pathlib import Path
from shutil import which


def command_exists(cmd):
    return which(cmd) is not None

# convert an R markdown file to a pdf file
# returns True if successful, False otherwise
def convert_rmd_to_pdf(rmd_path, output_path=None, input_dir=None, output_dir=None):
    # Set default directories if not provided
    if input_dir is None:
        input_dir = Path("input")
    else:
        input_dir = Path(input_dir)
    
    if output_dir is None:
        output_dir = Path("output")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)

    # if the provided path already points to a PDF, stop
    try:
        if Path(rmd_path).suffix.lower() == ".pdf":
            print("That file is already in pdf format")
            return False
    except Exception:
        pass

    # Build full input path
    full_input_path = Path(rmd_path) if os.path.isabs(str(rmd_path)) else input_dir / rmd_path
    if not full_input_path.exists():
        print(f"Error: Rmd file '{full_input_path}' not found")
        return False

    # Compute output name
    if output_path is None:
        pdf_name = f"{full_input_path.stem}.pdf"
    else:
        pdf_name = Path(output_path).name
    full_output_path = output_dir / pdf_name

    # Try via R + rmarkdown (best for .Rmd with code chunks)
    if command_exists("Rscript"):
        import tempfile
        temp_path = None
        try:
            # Create a modified version with better formatting to prevent text overflow
            with open(full_input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if YAML header exists and add geometry settings for proper margins
            if content.startswith('---'):
                # Find the end of YAML header
                yaml_end = content.find('---', 3)
                if yaml_end != -1:
                    yaml_header = content[:yaml_end + 3]
                    # Add geometry settings if not already present
                    if 'geometry:' not in yaml_header and 'margin' not in yaml_header.lower():
                        yaml_header = yaml_header.replace('\n---', '\ngeometry: margin=1in\n---')
                        content = yaml_header + content[yaml_end + 3:]
            else:
                # No YAML header, prepend one
                content = '---\ngeometry: margin=1in\n---\n\n' + content
            
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.Rmd', delete=False, encoding='utf-8') as tmp:
                tmp.write(content)
                temp_path = tmp.name
            
            r_expr = (
                "rmarkdown::render("
                f"\"{temp_path}\", "
                "output_format=\"pdf_document\", "
                f"output_file=\"{pdf_name}\", "
                f"output_dir=\"{str(output_dir)}\")"
            )
            cmd = [
                "Rscript",
                "-e",
                r_expr,
            ]
            print(f"Converting '{full_input_path}' to '{full_output_path}' using rmarkdown...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and full_output_path.exists():
                print(f"Successfully converted to '{full_output_path}'")
                # Clean up temp file
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                return True
            else:
                # Surface stderr for easier debugging
                if result.stderr:
                    print(f"rmarkdown stderr: {result.stderr.strip()}")
                print("rmarkdown conversion did not produce output; will try pandoc fallback if available.")
        except Exception as e:
            print(f"rmarkdown failed with error: {e}")
        finally:
            # Clean up temp file on error
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    # Fallback to pandoc (works for plain Markdown; R chunks won't execute)
    if command_exists("pandoc"):
        try:
            cmd = [
                "pandoc",
                str(full_input_path),
                "-o",
                str(full_output_path),
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=1in",  # Set 1 inch margins
                "-V", "fontsize=11pt",  # Set readable font size
            ]
            print(f"Converting '{full_input_path}' to '{full_output_path}' using pandoc...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and full_output_path.exists():
                print(f"Successfully converted to '{full_output_path}'")
                return True
            else:
                print(f"pandoc failed: {result.stderr.strip() if result.stderr else 'unknown error'}")
                return False
        except FileNotFoundError:
            print("Error: pandoc not found.")
            return False
        except Exception as e:
            print(f"Unexpected error running pandoc: {e}")
            return False

    print("Neither Rscript (rmarkdown) nor pandoc found. Please install one of them to convert .Rmd to PDF.")
    print("- Install R + rmarkdown: Rscript -e 'install.packages(\"rmarkdown\")'")
    print("- Or install pandoc: see https://pandoc.org/installing.html")
    return False


def main():
    parser = argparse.ArgumentParser(description="Convert R Markdown files to PDF")
    parser.add_argument("rmd_file", nargs="?", help="R Markdown file to convert (optional)")
    parser.add_argument("output_file", nargs="?", help="Output PDF filename (optional)")
    parser.add_argument("--input-dir", default="input", help="Input directory (default: input)")
    parser.add_argument("--output-dir", default="output", help="Output directory (default: output)")
    
    args = parser.parse_args()
    
    # Set up directories
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if args.rmd_file:
        # Convert specific file
        success = convert_rmd_to_pdf(args.rmd_file, args.output_file, input_dir, output_dir)
        if not success:
            sys.exit(1)
    else:
        # convert all .Rmd files in input/
        rmd_files = sorted(p for p in input_dir.glob("*.Rmd"))
        if not rmd_files:
            print(f"No .Rmd files found in {input_dir} folder")
            print("Usage: python Rmd_pdf.py <file.Rmd> [output.pdf] [--input-dir DIR] [--output-dir DIR]")
            print("Example: python Rmd_pdf.py report.Rmd")
            print("Example: python Rmd_pdf.py report.Rmd my_report.pdf")
            print("Example: python Rmd_pdf.py --input-dir myinput --output-dir myoutput")
            return
        any_failed = False
        for rmd in rmd_files:
            ok = convert_rmd_to_pdf(rmd.name, None, input_dir, output_dir)
            if not ok:
                any_failed = True
        if any_failed:
            sys.exit(1)


if __name__ == "__main__":
    main()


