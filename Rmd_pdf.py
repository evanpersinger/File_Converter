# Rmd_pdf.py
# converts restructured markdown file to pdf file


import os
import sys
import subprocess
from pathlib import Path
from shutil import which


def command_exists(cmd):
    return which(cmd) is not None


def convert_rmd_to_pdf(rmd_path, output_path=None):
    """
    Convert an .Rmd file to PDF.

    Prefers R's rmarkdown (handles R chunks). Falls back to pandoc if R is unavailable.

    Args:
        rmd_path (str | Path): Path to the .Rmd file (relative to input folder or absolute)
        output_path (str | Path | None): Desired output PDF filename. If None, uses input stem + .pdf

    Returns:
        bool: True if conversion successful, False otherwise
    """
    input_dir = Path("input")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Early guard: if the provided path already points to a PDF, stop
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

    # 1) Try via R + rmarkdown (best for .Rmd with code chunks)
    if command_exists("Rscript"):
        try:
            # Render with rmarkdown; place artifact in output_dir
            # rmarkdown::render(input, output_format="pdf_document", output_file="name.pdf", output_dir="output")
            r_expr = (
                "rmarkdown::render("
                f"\"{str(full_input_path)}\", "
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
                return True
            else:
                # Surface stderr for easier debugging
                if result.stderr:
                    print(f"rmarkdown stderr: {result.stderr.strip()}")
                print("rmarkdown conversion did not produce output; will try pandoc fallback if available.")
        except Exception as e:
            print(f"rmarkdown failed with error: {e}")

    # 2) Fallback to pandoc (works for plain Markdown; R chunks won't execute)
    if command_exists("pandoc"):
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
    if len(sys.argv) < 2:
        # No args: convert all .Rmd files in input/
        input_dir = Path("input")
        rmd_files = sorted(p for p in input_dir.glob("*.Rmd"))
        if not rmd_files:
            print("No .Rmd files found in input folder")
            print("Usage: python Rmd_pdf.py <file.Rmd> [output.pdf]")
            print("Example: python Rmd_pdf.py report.Rmd")
            print("Example: python Rmd_pdf.py report.Rmd my_report.pdf")
            return
        any_failed = False
        for rmd in rmd_files:
            ok = convert_rmd_to_pdf(rmd.name, None)
            if not ok:
                any_failed = True
        if any_failed:
            sys.exit(1)
        return

    rmd_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    success = convert_rmd_to_pdf(rmd_file, output_file)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()


