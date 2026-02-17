import re

import pdfplumber


class PDFService:
    """Extract accurate text content from PDF files with advanced cleaning."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract all text from a PDF file using pdfplumber.
        Applies cleaning for accurate quiz generation:
        - Removes repeated headers/footers
        - Fixes broken hyphenation across lines
        - Normalizes whitespace
        - Extracts tables as structured text
        """
        text_parts = []
        all_lines_per_page = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract main text
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if page_text:
                    all_lines_per_page.append(page_text.strip().split("\n"))

                # Extract tables and append as structured text
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        table_text = PDFService._table_to_text(table)
                        if table_text:
                            text_parts.append(table_text)

        # Detect and remove repeated headers/footers
        header_footer = PDFService._detect_repeated_lines(all_lines_per_page)

        # Clean each page's text
        for page_lines in all_lines_per_page:
            cleaned_lines = [
                line
                for line in page_lines
                if line.strip() and line.strip() not in header_footer
            ]
            if cleaned_lines:
                page_text = "\n".join(cleaned_lines)
                text_parts.append(page_text)

        full_text = "\n\n".join(text_parts)

        # Post-processing
        full_text = PDFService._clean_text(full_text)

        if not full_text.strip():
            raise ValueError("No readable text found in the PDF.")

        return full_text

    @staticmethod
    def _clean_text(text: str) -> str:
        """Apply text cleaning rules for better AI comprehension."""
        # Fix broken hyphenation (e.g., "algo-\nrithm" → "algorithm")
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

        # Fix line breaks within sentences (join lines that don't end with sentence-enders)
        text = re.sub(r"([a-z,;])\n([a-z])", r"\1 \2", text)

        # Normalize multiple spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove page numbers (standalone numbers on a line)
        text = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", text)

        # Remove common PDF artifacts
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

        return text.strip()

    @staticmethod
    def _detect_repeated_lines(all_lines_per_page: list) -> set:
        """
        Detect lines that appear on most pages (headers/footers).
        If a line appears on >50% of pages, it's likely a header/footer.
        """
        if len(all_lines_per_page) < 3:
            return set()

        line_counts = {}
        for page_lines in all_lines_per_page:
            # Check first 2 and last 2 lines of each page
            candidates = page_lines[:2] + page_lines[-2:]
            for line in candidates:
                stripped = line.strip()
                if stripped and len(stripped) < 100:  # headers/footers are short
                    line_counts[stripped] = line_counts.get(stripped, 0) + 1

        threshold = len(all_lines_per_page) * 0.5
        return {line for line, count in line_counts.items() if count >= threshold}

    @staticmethod
    def _table_to_text(table: list) -> str:
        """Convert a pdfplumber table to a readable text format."""
        rows = []
        for row in table:
            if row:
                cells = [str(cell).strip() if cell else "" for cell in row]
                if any(cells):
                    rows.append(" | ".join(cells))
        return "\n".join(rows) if rows else ""
