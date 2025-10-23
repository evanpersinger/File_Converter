#!/usr/bin/env python3
"""
SQL to PDF Converter

Converts SQL files to PDF format with syntax highlighting.
"""

import os
import sys
import argparse
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import sqlparse


def setup_directories():
    """Create input and output directories if they don't exist."""
    input_dir = Path("input")
    output_dir = Path("output")
    
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    return input_dir, output_dir


def format_sql_with_syntax_highlighting(sql_content):
    """
    Format SQL content with basic syntax highlighting using reportlab.
    This is a simplified version - for full syntax highlighting, 
    consider using pygments or similar libraries.
    """
    # Basic SQL keywords to highlight
    sql_keywords = [
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
        'ALTER', 'TABLE', 'INDEX', 'VIEW', 'PROCEDURE', 'FUNCTION', 'TRIGGER',
        'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'GROUP', 'BY', 'ORDER',
        'HAVING', 'UNION', 'DISTINCT', 'AS', 'AND', 'OR', 'NOT', 'IN', 'EXISTS',
        'BETWEEN', 'LIKE', 'IS', 'NULL', 'TRUE', 'FALSE', 'CASE', 'WHEN', 'THEN',
        'ELSE', 'END', 'IF', 'WHILE', 'FOR', 'LOOP', 'BEGIN', 'COMMIT', 'ROLLBACK',
        'TRANSACTION', 'GRANT', 'REVOKE', 'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES',
        'UNIQUE', 'CHECK', 'DEFAULT', 'NOT', 'NULL', 'AUTO_INCREMENT', 'IDENTITY'
    ]
    
    lines = sql_content.split('\n')
    formatted_lines = []
    
    for line in lines:
        if not line.strip():
            formatted_lines.append("")
            continue
            
        # Simple keyword highlighting (case-insensitive)
        formatted_line = line
        for keyword in sql_keywords:
            # Use regex-like replacement for whole words
            import re
            pattern = r'\b' + re.escape(keyword) + r'\b'
            formatted_line = re.sub(pattern, f'<b>{keyword}</b>', formatted_line, flags=re.IGNORECASE)
        
        formatted_lines.append(formatted_line)
    
    return '\n'.join(formatted_lines)


def create_pdf_from_sql(sql_file_path, output_path):
    """Create a PDF from SQL file content."""
    try:
        # Read SQL file
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Parse and format SQL
        try:
            # Use sqlparse to format the SQL nicely
            formatted_sql = sqlparse.format(sql_content, reindent=True, keyword_case='upper')
        except Exception:
            # Fallback to original content if parsing fails
            formatted_sql = sql_content
        
        # Create PDF document
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Create custom style for SQL code
        sql_style = ParagraphStyle(
            'SQLCode',
            parent=styles['Code'],
            fontSize=9,
            leading=12,
            fontName='Courier',
            leftIndent=20,
            rightIndent=20,
            spaceAfter=12,
            backColor=colors.lightgrey,
            borderColor=colors.black,
            borderWidth=1,
            borderPadding=10
        )
        
        # Create title style
        title_style = ParagraphStyle(
            'SQLTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=20,
            alignment=1  # Center alignment
        )
        
        # Build PDF content
        story = []
        
        # Add title
        filename = Path(sql_file_path).stem
        title = Paragraph(f"SQL File: {filename}", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Add formatted SQL content
        sql_lines = formatted_sql.split('\n')
        for line in sql_lines:
            if line.strip():
                # Escape special characters for reportlab
                escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                para = Paragraph(escaped_line, sql_style)
                story.append(para)
            else:
                story.append(Spacer(1, 6))  # Empty line spacing
        
        # Build PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False


def convert_sql_files():
    """Convert all SQL files in input directory to PDF."""
    input_dir, output_dir = setup_directories()
    
    # Find SQL files
    sql_files = list(input_dir.glob("*.sql"))
    
    if not sql_files:
        print("No SQL files found in the input/ directory.")
        print("Please place your .sql files in the input/ folder and try again.")
        return
    
    print(f"Found {len(sql_files)} SQL file(s) to convert:")
    for sql_file in sql_files:
        print(f"  - {sql_file.name}")
    
    successful_conversions = 0
    failed_conversions = 0
    
    for sql_file in sql_files:
        output_file = output_dir / f"{sql_file.stem}.pdf"
        
        print(f"\nConverting {sql_file.name}...")
        
        if create_pdf_from_sql(sql_file, output_file):
            print(f"✓ Successfully converted to {output_file.name}")
            successful_conversions += 1
        else:
            print(f"✗ Failed to convert {sql_file.name}")
            failed_conversions += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Conversion Summary:")
    print(f"  Successful: {successful_conversions}")
    print(f"  Failed: {failed_conversions}")
    print(f"  Total: {len(sql_files)}")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Convert SQL files to PDF")
    parser.add_argument("sql_file", nargs="?", help="SQL file to convert (optional)")
    parser.add_argument("output_file", nargs="?", help="Output PDF file name (optional)")
    
    args = parser.parse_args()
    
    if args.sql_file:
        # Convert specific file
        input_dir, output_dir = setup_directories()
        
        sql_file_path = Path(args.sql_file)
        if not sql_file_path.is_absolute():
            sql_file_path = input_dir / sql_file_path
        
        if not sql_file_path.exists():
            print(f"Error: File '{sql_file_path}' not found.")
            return
        
        if not sql_file_path.suffix.lower() == '.sql':
            print(f"Error: '{sql_file_path}' is not a SQL file.")
            return
        
        # Determine output file
        if args.output_file:
            output_path = output_dir / args.output_file
        else:
            output_path = output_dir / f"{sql_file_path.stem}.pdf"
        
        print(f"Converting {sql_file_path.name} to {output_path.name}...")
        
        if create_pdf_from_sql(sql_file_path, output_path):
            print(f"✓ Successfully converted to {output_path.name}")
        else:
            print(f"✗ Failed to convert {sql_file_path.name}")
    else:
        # Convert all SQL files in input directory
        convert_sql_files()


if __name__ == "__main__":
    main()
